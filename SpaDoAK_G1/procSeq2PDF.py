import xml.dom.minidom as xml
import pyx
import logging
import os.path

from .StrokesSVG import SVGDocument

import datetime


"""
This module handles main Input/Output Files, Document/Page-related Visualisation Issues, Sequence processing according to page settings.
E.g. page sizes, text line lenghts etc. define how a long sequence has to be split up into smaller ones, which information has to be displayed on each page ...
"""


def texIfyParam(t):
    t = t.replace(r'_',r'\_')
    return t

class LoadedTrajManager(object):
    def __init__(self):
        self.loaded = {}
        self.defined = {}

    def defineTrajRessource(self,ressourceID,filename):
        if ressourceID in self.defined:
            raise ValueError("ressource already defined %s" % ressouceID)

        self.defined[ressourceID] = filename

    def load(self,ressourceID):
        SVGFname = self.defined[ressourceID]
        print ("    LOAD TRAJ: %s/%s" % (ressourceID,SVGFname))
        self.loaded[ressourceID] = SVGDocument(SVGFname)

        logging.info("reading trajectories from SVG: %s, %s" % (ressourceID,SVGFname))

    def unload(self,ressourceID):
        SVGFname = self.defined[ressourceID]
        logging.info("unloading trajectories: %s, %s" % (ressourceID,SVGFname))
        print ("    UNLOAD TRAJ: %s/%s" % (ressourceID,SVGFname))

        ### hopefully garbage collection will work : )
        del self.loaded[ressourceID]

    def getLoaded(self,ressourceID):
        return self.loaded[ressourceID]

    def getAllLoaded(self):
        return [ x for x in self.loaded.values() ]

    def getLoadedInfo(self):
        infoS = ""
        for key,val in self.loaded.iteritems():
            infoS += "[%s]%s , " % (key,val.filename)
        infoS = infoS[:-3]
        return infoS


    def loadunloadTrajRessources(self,listOfRessourceIDs):
        """ basically this method ensures that no unnecessary loading and unloading of spatial data occurs.
        it is not exacly trivial since a set of several trajectory files can be loaded at the same time."""

        includeImage = None

        oldSet = set(self.loaded.keys())
        newSet = set([])
        for resID in listOfRessourceIDs:
            if resID not in self.loaded:
                self.load(resID)
            else:
                print ("    TRAJ already loaded: %s" % resID)
            newSet.add(resID)
        removeSet = oldSet-newSet

        ### remove those which are only in the old set but not in the new
        for resID in removeSet:
            self.unload(resID)

class SeqProcessor(object):
    """ The main document handling class. Here, Trajectories are loaded, Annotated sequences get passed to processAnnotatedSequence(...) in order to be visualised and then
        written to a PyX document; possibly slitting it up into multiple pages.
        All the page/document handling is located here.
        """


    predefinedPaperFormats = {}
    predefinedPaperFormats['A4'] = pyx.document.paperformat.A4
    predefinedPaperFormats['A3'] = pyx.document.paperformat.A3
    predefinedPaperFormats['A2'] = pyx.document.paperformat.A2
    predefinedPaperFormats['A1'] = pyx.document.paperformat.A1
    predefinedPaperFormats['A0'] = pyx.document.paperformat.A0



    def __init__(self,visualizer,loadedtrajectories,paperFormat="A4",rotatedPaper=1):
        self.setVisualizer(visualizer)
        self.loadedTraj = loadedtrajectories
        self.setPaperFormat(paperFormat,rotatedPaper)


    def setVisualizer(self,v):
        self.vis = v

    def setPaperFormat(self,paperFormat='A4',rotatedPaper=1):
        if paperFormat in self.predefinedPaperFormats:
            self.paperFormat = self.predefinedPaperFormats[paperFormat]
        else:
            try:
                paperw,paperh = map(int,paperFormat)
                #print ("Paper Custom Size: %d x %d mm" % (paperw,paperh))
                self.paperFormat = pyx.document.paperformat(pyx.unit.length(paperw,"t","mm"),pyx.unit.length(paperh,"t","mm"))
            except (TypeError,ValueError):
                raise ValueError("Custom paperFormat needs to be a 2-tuple of numbers: (width,height) in Millimeter")

        self.rotated = rotatedPaper

    def canvas2page(self,can,bbox=None):
        page = pyx.document.page(can,paperformat=self.paperFormat,margin=5*pyx.unit.t_mm,
                fittosize=1,rotated=self.rotated,bbox=bbox)
        return page


    def processAnnotatedSequence(self,aseq,PDFfname,PDFpath,textPageLen,graphPageLen,inIdx=0,outIdx=0,selectedPages=[],outputFileSuffix=None,
        transcrIdPrefix="",spatialIdPrefix="",simulate=False,backgroundPage=False,bbox=None,bboxtext=False):

        """ The function processes an annotated sequence into a PDF file using a given visualiser.
        inIdx/outIdx are used to slice within that sequence. The function is used for reacting on precise begin/end parameters by the user
        selected pages are a subordinary parameter for skipping pages in the output generation.
        """

        ### when not told otherwise, do the whole sequence

        ### indicate that a print region has been explicitly specified
        if inIdx or outIdx:
            printRegion = True
        else:
            printRegion = False


        if not inIdx:
            inIdx = 0
        if not outIdx:
            outIdx = len(aseq)

        logging.info ("Processing Interval: %s..%s TPL:%d GPL:%d simulate=%s" %(inIdx,outIdx,textPageLen,graphPageLen,simulate) )
        printOutIdx = outIdx
        currstop = inIdx + graphPageLen
        lastPrintPos = inIdx
        pagecounter = 1

        if not simulate:
            logging.info ("Making new PDF Document.")
            pdfDoc = pyx.document.document(pages=[])
            print ("NEW PDF-DOC:%s  PAGES:%s" % (pdfDoc, pdfDoc.pages))

        textPresent = False

        print ("    %d...%d / %d" % (lastPrintPos, currstop, printOutIdx))
        while lastPrintPos < printOutIdx:
            #logging.info ("processing interval %s: %s/%d..%s/%d  %s" %  (iid,startTS,startIdx,stopTS,stopIdx,data) )
            #logging.info("processing interval(%s,%d,%s,%d,%s)" % (startTS,startIdx,stopTS,stopIdx,data))

            ### checking for strokes (e.g. spatial output)
            spatialPresent = False

            #print "touching intevals for %d..%d" % (currstop-graphPageLen,currstop)
            for iid,startTS,startIdx,stopTS,stopIdx,data in aseq.touchingIntervalsByIdx(currstop-graphPageLen,currstop):

                if data['IntervalType'] == 'STROKE':
                    spatialPresent = True
                    #print "Spatial/Graphical Content ahead."
                    break

            if (spatialPresent and textPresent) or currstop - lastPrintPos >= textPageLen:
                ### if there is enough text for a text page or graphics ahead...
                ### in both cases we print the text just *bevore* the stop pos
                if selectedPages == [] or pagecounter in selectedPages:
                    print ("TEXT-PAGE: %d  %d..%d" % (pagecounter, lastPrintPos, currstop-graphPageLen))

                    #try:
                    if not simulate:
                        self.vis.newCanvas()

                        pageInfo = "%d (%d..%d)" % (pagecounter,lastPrintPos,(currstop-graphPageLen))
                        self.vis.setMetaData(page=pageInfo)

                        #print ("lpp:%d currstop:%d gpl:%d" % (lastPrintPos,currstop,graphPageLen))
                        drawnCanvases = self.vis.drawIntervalsBetween(aseq,lastPrintPos,
                                    currstop-graphPageLen,self.loadedTraj.getAllLoaded())
                        #self.vis.drawMarkers('LR')
                        self.vis.drawInfoHeaders()
                        print ("    appending page %d" % pagecounter)
                        for can in drawnCanvases:
                            print ("    slice")
                            if bboxtext:
                                page = self.canvas2page(can,bbox)
                            else:
                                page = self.canvas2page(can,bbox=None)
                            pdfDoc.append ( page )
                    else:
                        print ("    simulated page %d" % pagecounter)
                else:
                    print ("    not printing page %d" % pagecounter)

                lastPrintPos = currstop-graphPageLen
                textPresent = False
                pagecounter += 1

            if spatialPresent:
                ### print the spatial stuff.
                if selectedPages == [] or pagecounter in selectedPages:
                    print ("GRFX-PAGE: %d  %d..%d" % (pagecounter, lastPrintPos, currstop))
                    #try:
                    if not simulate:
                        self.vis.newCanvas()
                        self.vis.drawBackgroundImage()
                        pageInfo = "%d (%d..%d)" % (pagecounter, lastPrintPos, currstop)
                        self.vis.setMetaData(page=pageInfo)
                        drawnCanvases = self.vis.drawIntervalsBetween(aseq,lastPrintPos,currstop,self.loadedTraj.getAllLoaded(),
                                    transcriptIDprefix=transcrIdPrefix,spatialIDprefix=spatialIdPrefix)

                        self.vis.drawMarkers()
                        self.vis.drawInfoHeaders()
                        print ("    appending page %d" % pagecounter)
                        for can in drawnCanvases:
                            print ("    slice")
                            page = self.canvas2page(can,bbox)
                            pdfDoc.append ( page )
                    else:
                        print ("    simulated page %d" % pagecounter)
                else:
                    print ("    not printing page %d" % pagecounter)

                pagecounter += 1
                lastPrintPos = currstop
            else:
                ### if there was no graphics to print,
                ### then there will be text present next round
                textPresent = True
            currstop += graphPageLen

        if not outputFileSuffix:
            if printRegion:
                try:
                    PDFfname += '.%05d+%d' % (inIdx,outIdx-inIdx)
                except NameError:
                    try:
                        PDFfname += '.%05d' % inIdx
                    except NameError:
                        PDFfname += '.Region'


            if selectedPages != []:
                PDFfname += '.PageExtr'
        else:
            PDFfname += outputFileSuffix

        if not simulate:

            if backgroundPage:
                #self.vis.setMetaData(" "," "," "," ")
                can = self.vis.createBackgroundPage()
                page = self.canvas2page(can,bbox)
                pdfDoc.append ( page )

            paramInfo = ""
            paramInfo += "****************************************SpaDoAK-G1 PDF Output::************************************************************************************\n"

            dateNtime = datetime.datetime.today().isoformat()
            da,ti = dateNtime.split('T')
            paramInfo += "Date / Time:: %s / %s\n" % (da,ti)
            paramInfo += "PageLen TEXT/GRAF::%s/%s\n" % (textPageLen,graphPageLen)
            paramInfo += "Index IN/OUT::%s/%s\n" % (inIdx,outIdx)
            paramInfo += "page Selection::%s\n" % selectedPages
            paramInfo += "id prefixes TRNS/SPAT::%s/%s\n" % (transcrIdPrefix,spatialIdPrefix)
            paramInfo += "backgroundPage::%s\n" % backgroundPage
            #paramInfo += "bBox::%s\n" % str(bbox)
            paramInfo += "output:: FILE:%s --- PATH:%s --- SFFX:%s\n" % (PDFfname,PDFpath,outputFileSuffix)
            paramInfo += "\n"
            paramInfo += self.vis.getVisualizerInfo()
            paramInfo += "\n"
            paramInfo += "spatialData::%s" % self.loadedTraj.getLoadedInfo()

            canv = pyx.canvas.canvas()
            textY = 1000
            for param in paramInfo.split('\n'):
                if param != "":
                    try:
                        par,val = param.split('::')
                    except(ValueError):
                        par = param
                        val = ""

                    canv.text(0,textY,':')
                    canv.text(pyx.unit.x_pt*-2,textY,texIfyParam(par),[pyx.text.halign.right])
                    canv.text(pyx.unit.x_pt*7,textY,texIfyParam(val),[pyx.text.halign.left])
                    textY -= pyx.unit.x_pt * 15
            pdfDoc.append ( pyx.document.page(canv,paperformat=self.paperFormat,margin=1*pyx.unit.t_cm,fittosize=1,rotated=1) )


        PDFfnamepath = os.path.join(PDFpath,PDFfname)

        print ("output file: FN:%s  PATH:%s" % (PDFfname,PDFpath))
        pdfDoc.writePDFfile(PDFfnamepath)
