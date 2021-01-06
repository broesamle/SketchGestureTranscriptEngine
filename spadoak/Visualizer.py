import re
import logging
import copy
import os.path
import sys
import codecs

from .TranscriptIntegration.WTimelineA import TS_INPOINT, TS_OUTPOINT, BY_INDEX, BY_TIMESTAMP, keyPremiereTSoffset, isNativePremiereTS
from .StrokesSVG import TRAJ_ORDINARY, TRAJ_SODIPODI
from ._utils import ValueRetrieveError, InputError

from pyx import deco,text,style,bitmap
import pyx
import latexcodec

pathToMyself,Myself = os.path.split(__file__)


################################################
### Fixed initially usefull scale factors and sizes
### these might be overridden and/or modified by
### other parameters
### values are mostly historical.
################################################

textBaseScale = 5

coordinateBaseScale = 0.1
pyx.unit.set(uscale=coordinateBaseScale)


#############################################
### Cleaning and translating input for Latex
#############################################

def cleanTexInput(s):
    return s.replace("^"," ")

#############################################
### VISUALIZER
#############################################

class Visualizer(object):
    def __init__(self,
        pyxCanvas,
        xfactor=1,
        xoffset=0,
        yfactor=1,
        yoffset=0,
        lineLen=100,
        strokewidth=3.0,
        textX=0,
        textY=0,
        errX=None,
        errY=None,
        hideIDs=False,
        hideComments=False,
        hideTSs=False,
        hideSpeakers=False,
        hidePhrases=False,
        hideInfoHeader=False,
        sliceStrokes=False,
        colorPaletteFN="",
        textScale=1.0,
        progressFeedback=True,
        hideColouredFormatBars=False,
        graphicalDimensions=None,
        hideSequential=False
        ):
        """ Does the actual drawing, currently in a PyX Canvas.
            xfactor=1,xoffset=0,yfactor=1,yoffset=0     Transformation for PyX
            lineLen=100                                 length of a text line
            textX=0, textY=0, errX=None, errY=None,     Where to put text, and how to offset from there for placing error messages
            hide/slice and stuff                        more or less map directly map onto the command line parameters
            progressFeedback=True                       Give text output while rendering.
            graphicalDimensions=None                    print markers at the minimal/maximal dimensions
                                                        based on the given (minX,minY,maxX,maxY).
            """
        self.progressFeedback = progressFeedback
        self.totalColourCount = 0
        pyx.unit.set(xscale=textBaseScale*textScale)
        ### for double slicing
        self.doubleSlice = False
        self.lastPrintedStrokeID = ""
        ### for debugging purposes
        self.theSpecialNumber = 11111
        self.hideIDs = hideIDs
        self.hideComments = hideComments
        self.hideTSs = hideTSs
        self.hideSpeakers = hideSpeakers
        self.hidePhrases = hidePhrases
        self.hideInfoHeader = hideInfoHeader
        self.sliceStrokes = sliceStrokes
        self.hideColouredFormatBars = hideColouredFormatBars
        self.hideSeq = hideSequential
        ###########################
        ### graphics parameters
        ###########################
        self.maxW = lineLen
        self.pageHeight = pyx.unit.x_mm*230
        self.textX,self.textY  =  textX,textY
        if errX:    self.errX0=textX+errX
        else:       self.errX0=textX+self.pageHeight*0.7
        if errY:    self.errY0=textY+errY
        else:       self.errY0=textY+self.pageHeight*0.90
        self.strokewidth = strokewidth
        self.handstrokewidth=self.strokewidth*2
        self.txtstrokewidthscale = 2.0
        self.draww = self.strokewidth*1.7
        self.strokecolors = PyxPalette()
        if self.sliceStrokes:
            self.stroketransp = 0.0
            if colorPaletteFN!="":
                self.strokecolors.extractFromHTMFile(os.path.join(pathToMyself,colorPaletteFN))
            else:
                self.strokecolors.extractFromHTMFile(os.path.join(pathToMyself,"black-only-colors.htm"))
        else:
            self.stroketransp = 0.0
            #self.strokecolors.extractFromHTMFile(os.path.join(pathToMyself,"alternating-stroke-colorsA.htm"))
            if colorPaletteFN!="":
                self.strokecolors.extractFromHTMFile(os.path.join(pathToMyself,colorPaletteFN))
            else:
                self.strokecolors.extractFromHTMFile(os.path.join(pathToMyself,"alternating-stroke-colorsC.htm"))
        self.connprecis = 20
        self.setTrajTransformation(xfactor,xoffset,yfactor,yoffset)
        self.symbolsize = 15.0
        self.symbolstrokewidth = self.symbolsize / 10
        self.symbolfilltrans = 0.5
        self.symbaker = SymbolMaker(pyxCanvas,size=self.symbolsize,linewidth=self.symbolstrokewidth)
        self.newCanvas(pyxCanvas)
        self.speakercolors = PyxPalette()
        self.speakercolors.extractFromHTMFile(os.path.join(pathToMyself,"palettespeakers.htm"))
        self.speakers = {}
        #self.speakers['informer'] = self.speakercolors.getColor(len(self.speakers))
        self.erroffset = 0, -pyx.unit.x_pt * 10
        self.idtxtSep = pyx.unit.x_pt * 4
        self.idYoff = - self.idtxtSep
        if not hideIDs:
            self.idHeight = pyx.unit.x_pt * 16
        else:
            self.idHeight = pyx.unit.x_pt * 0
        self.commentYoff = - (self.idtxtSep+self.idHeight+pyx.unit.x_pt * 4)
        if not hideComments:
            self.commentHeight = pyx.unit.x_pt * 8
        else:
            self.commentHeight = pyx.unit.x_pt * 0
        if not hideTSs:
            self.tsHeight = pyx.unit.x_pt * 16
        else:
            self.tsHeight = pyx.unit.x_pt * 0
        self.tsYoff = self.idYoff - (self.tsHeight + self.idHeight + self.commentHeight)
        self.phraseHeight = self.commentHeight + self.idHeight + self.tsHeight
        self.phraseYoff = self.idYoff - 0.5 * self.phraseHeight
        self.speakerwidth = pyx.unit.x_pt * 2
        self.textFontSize = 10*pyx.unit.x_pt
        self.textSep = 10*pyx.unit.x_pt
        self.textHeight = (self.phraseHeight + self.strokewidth*self.txtstrokewidthscale
                    + self.textFontSize + self.speakerwidth + self.idtxtSep + self.textSep)
        ###########################
        ### Info parameters and supplementary graphics
        ###########################
        self.eraseMetaData()
        self.markers=[]
        self.dims=graphicalDimensions
        self.bgImage = None

    def getVisualizerInfo(self):
        paramInfo = ""
        paramInfo += "Visualiser Settings::*************\n"
        paramInfo += "Transformation Xoff,Yoff,Xscale,Yscale:: %s , %s , %s , %s\n" % (self.xfactor,self.xoffset,self.yfactor,self.yoffset)
#       paramInfo += "Text position / Error position::%s,%s / %s,%s\n" % (self.textX,self.textY,self.errX0,self.errY0)
        paramInfo += "Text position / Error position::%s,%s / %s,%s\n" % (self.textX,self.textY,"?","?")
        paramInfo += "lineLen / strokeW / slice::%s / %s / %s\n" % (self.maxW,self.strokewidth,self.sliceStrokes)
        paramInfo += ("hide: IDs/Comments/TSs / Speakers / Phrases / Header::%s/%s/%s / %s / %s / %s\n" %
                      (self.hideIDs,
                       self.hideComments,
                       self.hideTSs,
                       self.hideSpeakers,
                       self.hidePhrases,
                       self.hideInfoHeader))
        return paramInfo

    def setTrajTransformation(self,xfactor=1,xoffset=0,yfactor=1,yoffset=0):
        print ("    setTrajTransformation: %s,%s,%s,%s" % (xfactor,xoffset,yfactor,yoffset))
        self.xfactor = xfactor
        self.xoffset = xoffset
        self.yfactor = yfactor
        self.yoffset = yoffset
        self.tra = pyx.trafo.scale(xfactor,yfactor) * pyx.trafo.translate(xoffset,-yoffset)

    def newCanvas(self, pyxCanvas=None):
        if not pyxCanvas :
            pyxCanvas = pyx.canvas.canvas()
        #self.maxW=lineLen
        self.canvas = pyxCanvas
        self.errpos = self.errX0,self.errY0
        self.symbaker.newCanvas(pyxCanvas)
        return self.canvas

    def transform(self,x,y):
        x1,y1 = (x*self.xfactor+self.xoffset , y*self.yfactor+self.yoffset)
        return x1,y1

    def eraseMetaData(self):
        self.projectInfo = "?PRJ?"
        self.sessionInfo = "?SESS?"
        self.episodeInfo = "?EPI?"
        self.spatialInfo = "?SPAT?"
        self.sequentialInfo = "?SEQ?"
        self.pageInfo= "?PAGE?"

    def setMetaData(self,project=None, session=None, episode=None, spatial=None, sequence=None, page=None):
        if project:     self.projectInfo = project
        if session:     self.sessionInfo = session
        if episode:     self.episodeInfo = episode
        if spatial:     self.spatialInfo = spatial
        if sequence:    self.sequentialInfo = sequence
        if page:        self.pageInfo= page

    def initSpeakers(self,speakers):
        for s in speakers:
            self.speakers[s] = self.speakercolors.getColor(len(self.speakers))

    def errorPos(self):
        e = self.errpos
        self.errpos = (self.errpos[0] + self.erroffset[0]),(self.errpos[1] + self.erroffset[1])
        return e

    ### DRAWING ###
    ### DRAWING ###
    ### DRAWING ###
    ### all drawing routines take native svg coordinates and transform them accordingly

    def drawJPG(self,filename,x=0,y=0,width=None,height=None,transp=0.0):
        if filename[-4:] != ".jpg":
            print ("    replacing extension with JPG")
            filename = filename[:-4]+'.jpg'

        i = bitmap.jpegimage(filename)
        self.canvas.insert(bitmap.bitmap(x,y,i, width=width, height=height, compressmode=None),[pyx.color.transparency(transp)])

    def getInfoPositions(self):
        #width = abs(self.metaInfoPos-)
        #x,y = - dist*0.5,self.metaInfoPos-height

        dist = 5*pyx.unit.x_mm
        height = dist*2.5
        width = self.pageHeight
        x,y = self.textX,self.textY
        return x,y,width,height,dist

    def drawInfoHeaders(self):
        #self.symbaker.putCross(0.0,0.0,3.0,[pyx.color.rgb.blue])
        if self.hideInfoHeader:
            return
        x,y,width,height,dist = self.getInfoPositions()
        tab = 20*pyx.unit.x_mm
        margin = dist*0.5
        sc = pyx.canvas.canvas()
        transf = [pyx.trafo.rotate(90,x=x,y=y), pyx.trafo.translate(-height+2*margin, self.metaInfoPos)]
        sc.stroke(pyx.path.rect(x,y-0.5*dist,width,height),[deco.filled([pyx.color.grey(0.90)])])
        string1 = "PROJ:%s --- SESS:%s --- EPIS:%s" % ( self.projectInfo, self.sessionInfo, self.episodeInfo )
        string2 = "%s" % self.pageInfo
        string3 = "SPAT:%s --- SEQU:%s" % (self.spatialInfo,self.sequentialInfo)
        logging.info("A-LATEX:%s" % cleanTexInput(string1))
        sc.text(x+margin,y+dist,cleanTexInput(string1))
        logging.info("B-LATEX:%s" % cleanTexInput(string2))
        sc.text(x+width-2*margin,y+dist,cleanTexInput(string2),[text.halign.boxright])
        logging.info("C-LATEX:%s" % cleanTexInput(string3))
        sc.text(x+margin,y,cleanTexInput(string3))
        self.canvas.insert(sc, transf)

    def setMarkers(self,svgdoc,
        markers=['Marker1','Marker2','Marker3','Marker4','TEXT_MARKER','UPPER_LEFT','LOWER_RIGHT'],
        markerlabels=[ '1',      '2',      '3',      '4',      '',        'UL',         'LR']):
        missingmarkers = []
        for marker,label in zip(markers,markerlabels):
            try:
                x,y = svgdoc.getSodiPodiXY(marker)
                self.markers.append((label,x,y,marker))
            except(ValueRetrieveError):
                missingmarkers.append(marker)
        if missingmarkers != []:
            print ("!!  Did not find marker(s) %s." % str(missingmarkers)[1:-1])

    def setTextPositionFromMarker (self,marker="TEXT_MARKER"):
        for label,x,y,m in self.markers:
            print (label)
            if m == marker:
                self.textX,self.textY = self.tra.apply(x,y)
                return
        raise InputError("Marker not defined! %s" % marker)

    def getBBoxFromMarkers (self,marker1,marker2):
        for label,x,y,m in self.markers:
            if m == marker1:
                x1,y1 = self.tra.apply(x,y)
            if m == marker2:
                x2,y2 = self.tra.apply(x,y)
        return pyx.bbox.bbox(llx_pt=min(x1,x2),lly_pt=min(y1,y2),urx_pt=max(x1,x2),ury_pt=max(y1,y2))

    def drawMarkers(self):
        for label,x,y,m in self.markers:
            x,y = self.tra.apply(x,y)
            self.symbaker.putText(x+5,y,label)
            self.symbaker.putCross(x,y,8,[pyx.color.rgb.green])
        if self.dims is not None:
            minX, minY, maxX, maxY = self.dims
            self.symbaker.putPolygonC([(minX,minY+20),
                                       (minX,minY),
                                       (minX+20,minY)], [pyx.color.rgb.blue])
            self.symbaker.putPolygonC([(maxX-40,maxY),
                                       (maxX,maxY),
                                       (maxX,maxY-40)], [pyx.color.rgb.blue])
            self.symbaker.putCross(0,0, 10, [pyx.color.rgb.blue])

    def defineBackgroundImage(self,x,y,w,h,filepath,transparency=0.6):
        print ("    BG-IMAGE: %s,%s,%s,%s,%s" % (x,y,w,h,filepath))
        self.bgImage = x,y,w,h,filepath
        self.bgTransp = transparency

    def drawBackgroundImage(self,transp=None,override=False):
        if self.sliceStrokes and not override:
            print ("slicing: ignore background image")
        else:
            if transp == None:
                transp = self.bgTransp
            if self.bgImage:
                x,y,w,h,file = self.bgImage
                self.drawJPG(file,x,y,w,h,transp)
            else:
                print ("!!  Warning, no background image defined.")

    def createBackgroundPage(self):
        self.newCanvas()
        self.drawBackgroundImage(0.7,override=True)
        #self.drawInfoHeaders()
        self.drawMarkers()
        return self.canvas

    def _drawTextForSequential(self,
                               aseq,
                               inpointIdx,
                               outpointIdx,
                               posx,
                               posy,
                               microcanvasesByStartTS):
        """Draw sequential text data on the current canvas.
        If `self.sliceStrokes` is true, new canvases can be
        created and be added to microcanvasesByStartTS
        Returns the positions of the markers of all segments as a dict.
        """
        segmpos = {}
        ### this loop follows the logic of SEGMENTS between TIMESTAMPs.
        ### it prints text and puts markers where there is timestamps (irrelevant where they belong in terms of intervals!)
        ### the iteration follows segments (where a segment is defined as the largest piece of transcript text belonging to the same set of intervals)
        ### as soon as a new one starts or an interval stops a segment border (and a timestamp) should be reached.
        for x in aseq.iterSegments(inpointIdx,
                                   outpointIdx,
                                   sortPoints=BY_TIMESTAMP,
                                   pointKey=keyPremiereTSoffset):
            startTS,startIdx,stopTS,stopIdx,txt = x
            speakerXsep = 0
            logging.info( "printing Segment: " + txt )
            logging.info("(%s,%d)-(%s,%d)" % (startTS,startIdx,stopTS,stopIdx))
            if self.progressFeedback:
                sys.stdout.write("|" + txt)
            ### put the text segment
            startmarker = "\\PyXMarker{anfang}"
            stopmarker = "\\PyXMarker{ende}"
            TEXtxt =  startmarker + codecs.encode(txt,'latex').decode('utf8') + stopmarker
            TEXtxt = cleanTexInput(TEXtxt)
            t = self.canvas.text(posx+speakerXsep,posy,TEXtxt)

            ### after printing the text of the segment we save the
            ### position of marker 1 for later interval drawing
            ### interval drawing will refer to the timestamps and retrieve the respective coordinates
            center1 = t.marker("anfang")
            posx,posy = center1
            segmpos[startTS] = center1
            if not self.sliceStrokes and not self.hideTSs:
                lastx = posx
                ### printing the timestamp (ignoring the hours part by [3:])
                if isNativePremiereTS(startTS):
                    self.symbaker.putCross(posx, posy+self.tsYoff,
                                           tsSymbolSize,[pyx.color.rgb.red])
                    self.canvas.stroke(pyx.path.line(
                            posx,posy+self.tsYoff,posx,posy-5),
                            [pyx.color.rgb.red])
                    self.canvas.text(posx, posy+self.tsYoff, "%s" % startTS[3:],
                            [pyx.text.size.tiny,
                             pyx.trafo.rotate(TSrot)])
            center2 = t.marker("ende")
            posx,posy = center2[:2]
            if self.sliceStrokes:
                microcanvasesByStartTS[startTS] = self.canvas
                self.newCanvas(pyx.canvas.canvas())
        ### save the last segments end position -- then we should have all timestamps
        segmpos[stopTS] = center2
        return segmpos

    def drawIntervalsBetween(self,
                             aseq,
                             inpointIdx, outpointIdx,
                             svgdocs,
                             textPos=None,
                             transcriptIDprefix="",
                             spatialIDprefix="",
                             drawTrajLabels=False,
                             trajLabelPrefixes=[]):
        ### the transcriptIDprefix defines the prefix of the stroke IDs coming from the transcript.
        ### it has to be removed for mapping onto the svgdoc ids, which do not have the transcript sequence prefix
        ### TODO: a systematic path/namespace logic would neatly solve the issue without this 'hack'

        logging.debug("drawIntervalsBetween: %s..%s" % (inpointIdx,outpointIdx))

        ### split recursively if the sequence is too long
        #################################################

        if outpointIdx - inpointIdx > self.maxW:
            #it is longer than the longest line should be
            pos = inpointIdx
            offset = 0
            result = []
            while pos < outpointIdx:
                result+=self.drawIntervalsBetween(aseq,pos,min(pos+self.maxW,outpointIdx),svgdocs,textPos=self.textY+offset,transcriptIDprefix=transcriptIDprefix,spatialIDprefix=spatialIDprefix)
                pos += self.maxW
                offset -= self.textHeight
                self.metaInfoPos = offset
            if self.sliceStrokes:
                return result
            else:
                return result[:1]
        else:
            self.metaInfoPos = -20*pyx.unit.x_mm

        ######################################
        ### the rest is basically the main job
        ######################################

        ### textX is the user position of the text
        ### textPos is the yposition moving down line by line (not given. when recursing for multiple lines)
        if not textPos:
            textPos = self.textY
        posx,posy = self.textX,textPos
        strokeoffset = self.textFontSize + (self.strokewidth*self.txtstrokewidthscale*0.5)
        strokelabelrot = 330
        #### see below ### connwidth = 0.5
        speakerYoff =  self.idYoff - self.phraseHeight - self.speakerwidth
        #thisSpeakerXsep = 0
        speakerlabeloffset = speakerYoff-self.speakerwidth/2.0
        speakertransparency = 0.0
        trajLabelOffsetX = 5
        trajLabelOffsetY = 5
        trajLabelRot = 45
        tsRad = 3
        tsSymbolSize = 3.5
        TSrot = 30
        #tsOffset
        connwidth = 1
        lastx = -1000
        ## segmpos: the positions of the markers of all segments
        # ... independent of the interval structure behind it
        if self.sliceStrokes:
            Slices=[]
            microcanvasesByStartTS = {}
            textsliceByStartTS = {}
        else:
            Slices=[self.canvas]
        segmpos = self._drawTextForSequential(aseq,
                                              inpointIdx,
                                              outpointIdx,
                                              posx,
                                              posy,
                                              microcanvasesByStartTS)
        if self.sliceStrokes:
            self.newCanvas()
            strokeCount = 0
            if self.doubleSlice:
                for iid,startTS,startIdx,stopTS,stopIdx,intervaldata,subseq in aseq:
                    if intervaldata['IntervalType'] == 'STROKE':
                        if stopIdx < inpointIdx or startIdx > outpointIdx:
                            continue        ## in this case, the interval is completely irrelevant
                        ### check whether it starts earlier
                        if startIdx < inpointIdx:
                            continue
                        strokeCount += 1
        currStrokeCount = 0
        oddStrokeCount = True
        ### this loop follows the logic of intevals (coded subsequences)
        ### each inteval is checked whether its a stroke or a phrase
        ### then the corresponding text positions (timestamps, see above) are found and
        ### the interval is marked on the text.
        for iid,startTS,startIdx,stopTS,stopIdx,intervaldata,subseq in aseq:
            if 'spatialElementID' in intervaldata:
                spatElID = intervaldata['spatialElementID']
            else:
                spatElID = iid
            if stopIdx < inpointIdx or startIdx > outpointIdx:
                continue        ## in this case, the interval is completely irrelevant
            ### check whether it starts earlier
            if startIdx < inpointIdx:
                startTS = TS_INPOINT
                startclipping = True
            else:
                startclipping = False
            ### check whether it stops later
            if stopIdx > outpointIdx:
                stopTS = TS_OUTPOINT
                stopclipping = True
            else:
                stopclipping = False
            #if startTS in segmpos and stopTS in segmpos:
            startX,startY = segmpos[startTS]
            stopX,stopY = segmpos[stopTS]
            arrows = []
            if startclipping:   arrows.append(deco.barrow.large)
            if stopclipping:    arrows.append(deco.earrow.large)
            if intervaldata['IntervalType'] == 'STROKE':
                ### remove
                #iid = iid.replace(transcriptIDprefix,"")
                if len(transcriptIDprefix)!=0:
                    if spatElID[:len(transcriptIDprefix)] == transcriptIDprefix:
                        spatElID = spatElID [len(transcriptIDprefix):]
                    else:
                        raise InputError("encountered stroke with bad id prefix: %s (should be %s)"
                                         % (spatElID,transcriptIDprefix))
                if self.lastPrintedStrokeID == spatElID:
                    continue
                spatElID = spatialIDprefix + spatElID
                ### rotate color palette / count total required colours
                self.strokecolors.rotate()
                if self.progressFeedback:
                    self.totalColourCount += 1
                    sys.stdout.write("%d " % self.totalColourCount)
                    if self.totalColourCount % 10 == 0:
                        sys.stdout.write("\n")
                ### draw the label for the stroke ID
                if not self.hideIDs:
                    logging.info("DLATEX:%s" % cleanTexInput(spatElID))
                    self.canvas.text(startX, startY+self.idYoff,
                                     cleanTexInput(spatElID),
                                     [pyx.text.size.tiny,text.valign.top,pyx.trafo.rotate(strokelabelrot)])
                if 'comment' in intervaldata and not self.hideComments:
                    logging.info("DLATEX:%s" % cleanTexInput(intervaldata['comment']))
                    self.canvas.text(startX, startY+self.commentYoff,
                                     cleanTexInput(intervaldata['comment']),
                                     [pyx.text.size.tiny])
                theline = pyx.path.line(startX, startY+strokeoffset,
                                        stopX, stopY+strokeoffset)
                self.canvas.stroke(theline,
                                   [style.linewidth(self.strokewidth*self.txtstrokewidthscale),
                                    self.strokecolors.getColor()])
                polygoneA = [(startX,startY+strokeoffset)]
                textdeco = []
                strokecolor = [self.strokecolors.getColor()]
                strokedeco = copy.deepcopy(strokecolor)
                ### go for all svgdocs until the spatElID returns some pathdata
                try:
                    svgpathdata = None
                    for svgdoc in svgdocs:
                        try:
                            svgpathdata = svgdoc.getStroke(spatElID)
                        except ValueError as Verr:
                            print ("!!  [%s] Error getting SVG path data: %s" % (spatElID,Verr.message))
                        if svgpathdata:
                            break

                    if not svgpathdata:
                        print ("!!  missing trajectory data for spatial element %s" % spatElID)

                    drawedtrajectories = self.drawStroke(svgpathdata, intervaldata, strokedeco)
                    for traj in drawedtrajectories:
                        polygoneA.append(traj['markers'][0])
                except ValueError as verr:
                    errX,errY = self.errorPos()
                    polygoneA.append((errX,errY))
                    errmsg = "[%s] %s" % (spatElID,verr.message)
                    logging.info("F-LATEX:%s" % cleanTexInput(errmsg))
                    self.canvas.text(errX+5,errY,cleanTexInput(errmsg),
                                     [pyx.text.size.small])
                    textdeco = [text.halign.boxright]
                if drawTrajLabels:
                    textX,textY = polygoneA[1]
                    ### if one of the prefixes is present remove it
                    for pref in trajLabelPrefixes:
                        if spatElID[len(pref)] == pref:
                            spatElIDstub = spatElID[len(pref):]
                            break
                    logging.info("G-LATEX:%s" % cleanTexInput(spatElID))
                    self.canvas.text(textX+trajLabelOffsetX,
                                     textY+trajLabelOffsetY,
                                     cleanTexInput(spatElID),
                                     [pyx.text.size.tiny,
                                      pyx.trafo.rotate(trajLabelRot)]+textdeco)
                self.symbaker.putPolygonC(polygoneA,strokecolor)
                polygoneA = polygoneA[1:]
                self.symbaker.putPolygonC(polygoneA,
                                          strokecolor + [ deco.filled(strokecolor+[pyx.color.transparency(0.9)]) ])
                currStrokeCount += 1
                ### every second -- and the last one in any case
                if self.doubleSlice:
                    oddStrokeCount = not oddStrokeCount
                #print "ODD:%s CURR:%s ALL:%s" % (oddStrokeCount,currStrokeCount,strokeCount)
                if self.sliceStrokes and (oddStrokeCount or currStrokeCount == strokeCount):
                    self.drawInfoHeaders()
                    for startTSmicro,microcan in microcanvasesByStartTS.items():
                        self.canvas.insert(microcan)
                    self.drawMarkers()
                    Slices.append(self.canvas)
                    self.newCanvas(pyx.canvas.canvas())
                    self.lastPrintedStrokeID = spatElID
            elif intervaldata['IntervalType'] == 'PHRASE' and not self.sliceStrokes and not self.hidePhrases:
                ### never needed interval ids printed really
                self.canvas.stroke(pyx.path.line(startX, startY+self.phraseYoff,
                                                 stopX, stopY+self.phraseYoff),
                                        [pyx.color.rgb(0,0,0.8),
                                         style.linewidth(self.phraseHeight),
                                         pyx.color.transparency(0.8)])
                if intervaldata['startblau'] and not startclipping:
                    self.canvas.stroke(
                            pyx.path.circle(startX,
                                            startY+self.phraseYoff+self.phraseHeight/3,
                                            self.phraseHeight/16),
                            [pyx.color.rgb(0,0,0.8), deco.filled()])
                if intervaldata['stopblau'] and not stopclipping:
                    self.canvas.stroke(
                            pyx.path.circle(stopX,
                                            stopY+self.phraseYoff+self.phraseHeight/3,
                                            self.phraseHeight/16),
                            [pyx.color.rgb(0,0,0.8), deco.filled()])
            elif (intervaldata['IntervalType'] == 'SPEAKER'
                  and not self.sliceStrokes
                  and not self.hideSpeakers):
                speaker = intervaldata['Speaker']
                if speaker not in self.speakers:
                    print ("    Adding an additional speaker: %s" % speaker)
                    self.speakers[speaker] = self.speakercolors.getColor(len(self.speakers))
                speakercolor = self.speakers[speaker]
                speakerVwidth = pyx.unit.x_pt *2
                speakerline = pyx.path.line(startX, startY+speakerYoff,
                                            stopX, stopY+speakerYoff)
                self.canvas.stroke(speakerline,
                                   [style.linewidth(self.speakerwidth),
                                    speakercolor])
                if not startclipping:
                    speakerlineVert = pyx.path.line(startX+speakerVwidth/2,
                                                    startY+speakerYoff,
                                                    startX+speakerVwidth/2,
                                                    stopY)
                    self.canvas.stroke(speakerlineVert,
                                       [style.linewidth(speakerVwidth),
                                        speakercolor])
                logging.info("H-LATEX:%s" % cleanTexInput(speaker))
                self.canvas.text(startX, startY+speakerlabeloffset,
                                 cleanTexInput(speaker),
                                 [pyx.text.size.tiny])
            elif intervaldata['IntervalType'] == 'FORMAT' and not self.sliceStrokes:
                formatoffset = pyx.unit.x_pt*3
                formatw = pyx.unit.x_pt * 5
                formattransparency = 0.5
                format = intervaldata['Format']
                if format == 'RED+YELLOW':
                    if not self.hideColouredFormatBars:
                        formatline1 = pyx.path.line(startX, startY+formatoffset,
                                                    stopX, stopY+formatoffset)
                        formatline2 = pyx.path.line(startX, startY+formatoffset+formatw/2,
                                                    stopX, stopY+formatoffset+formatw/2)
                        self.canvas.stroke(formatline1,
                                           [style.linewidth(formatw/2),
                                            pyx.color.rgb(1,1,0),
                                            pyx.color.transparency(formattransparency)])
                        self.canvas.stroke(formatline2,
                                           [style.linewidth(formatw/2),
                                            pyx.color.rgb.red,
                                            pyx.color.transparency(formattransparency)])
                elif format == 'RED':
                    if not self.hideColouredFormatBars:
                        formatline1 = pyx.path.line(startX, startY+formatoffset,
                                                    stopX, stopY+formatoffset)
                        self.canvas.stroke(formatline1,
                                           [style.linewidth(formatw),
                                            pyx.color.rgb.red,
                                            pyx.color.transparency(formattransparency)])
                elif format == 'YELLOW':
                    if not self.hideColouredFormatBars:
                        formatline1 = pyx.path.line(startX, startY+formatoffset,
                                                    stopX, stopY+formatoffset)
                        self.canvas.stroke(formatline1,
                                           [style.linewidth(formatw),
                                            pyx.color.rgb(1,1,0),
                                            pyx.color.transparency(formattransparency)])
                elif format == 'STRIKE':
                    formatline = pyx.path.line(startX, startY+formatoffset,
                                               stopX, stopY+formatoffset)
                    self.canvas.stroke(formatline,[style.linewidth(formatw/8)])
        return Slices

    ### low level drawing for strokes etc ... these also take svg coordinates
    ### they return pyx coordinates as reference points such that drawn elements can be located on the
    ### canvas for further drawing (like labels for drawn paths etc)
    def drawStroke(self,traj,intervaldata,decoration):
        ### traj contains the SVG based trajectory information
        ### fingers is a string identifying the finger, hand, or tool (pen etc) for each trajectory
        fingers = intervaldata['fingers']
        if 'holdstart' in intervaldata:     holdstart = intervaldata['holdstart']
        else:                               holdstart = ""
        if 'holdstop' in intervaldata:      holdstop = intervaldata['holdstop']
        else:                               holdstop = ""
        if 'hold' in intervaldata:          hold = intervaldata['hold']
        else:                               hold = ""
        ### both are sequences or exactly one single element
        strokedeco = copy.deepcopy(decoration)
        if not traj:
            raise InputError("Empty trajectory information.")
        err = False
        if fingers=='':
            print ("!!  Empty finger information in stroke")
            err = True
            fingers = 'X'

        if type(traj) == list:
            result = []
            ### composed multi finger trajectory
            if len(traj) == len(fingers):
                ### trivial case: one finger code per trajectory =~ no hand movement, only static hands
                for subtraj,f in zip(traj,fingers):
                    #self.drawTrajectoryElement(subtraj,f,decoration)
                    result.append(self.drawMovementTrajectory(subtraj,f,holdstart,holdstop,hold,strokedeco))
            elif len(traj)-len(fingers) == 1:
                ### there is one hand with a movement
                ### the other might be a static hand or a finger
                ### n+1 trajectories, n finger infos
                ### the hand must be the one with the two trajectories
                foundit = False
                for f in fingers:
                    if f in self.HANDCODES:
                        ### we found the hand
                        if foundit==True:
                            ### there is an other static hand that should have been coded as a second moving hand
                            ### with two hands, one moving this is necessary because it is impossible to distinguish the moving and the
                            ### static hands based on the trajectory data + finger sequence.
                            raise InputError("Two hands with only one moving have to be coded as two moving hands (with one empty movement trajectory).")
                        foundit = True
                        subtraj = traj[0]
                        traj = traj[1:]
                        result.append(self.drawHandShape(subtraj,f,holdstart,holdstop,hold,strokedeco))
                        subtraj = traj[0]
                        traj = traj[1:]
                        self.drawMovementTrajectory(subtraj,f,holdstart,holdstop,hold,strokedeco)
                    else:
                        subtraj = traj[0]
                        traj = traj[1:]
                        result.append(self.drawMovementTrajectory(subtraj,f,holdstart,holdstop,hold,strokedeco))
            elif len(traj)-len(fingers) == 2:
                ### there is two hands with movement
                ### since both hands are hands there should be no single fingers
                if len(fingers) != 2:
                    print ("!!  Mismatching two hands gesture/ movement trajectories: %s/%s" % (fingers,traj))
                    raise InputError("!!  Mismatching two hands gesture/ movement trajectories: %s" % fingers)
                f1,f2 = fingers
                if f1 not in self.HANDCODES or f2 not in self.HANDCODES:
                    print ("!!  Two hands gesture with incompatible finger code: %s/%s" % (f1,f1))
                    raise InputError("!!  Two hands gesture with incompatible finger code: %s/%s" % (f1,f1))
                h1,m1,h2,m2 = traj
                result.append(self.drawHandShape(h1,f1,holdstart,holdstop,hold,strokedeco))
                self.drawMovementTrajectory(m1,f1,holdstart,holdstop,hold,strokedeco)
                result.append(self.drawHandShape(h2,f2,holdstart,holdstop,hold,strokedeco))
                self.drawMovementTrajectory(m2,f2,holdstart,holdstop,hold,strokedeco)
            else:
                ### there should be not more than a difference of two (two hands moving)
                print ("!!  Mismatching fingers/trajectories: %s" % fingers)
                raise InputError("!!  Mismatching fingers/trajectories: %s" % fingers)

            if err:
                x,y = resultresult[:2]
                self.canvas.text(x,y,"!!  Empty Finger Info")
            return result
        else:
            ### single trajectory
            if len(fingers) != 1:
                print ("!!  Mismatching fingers/trajectories: %s/%s" % (fingers,traj))
                raise InputError("!!  Mismatching fingers/trajectories: %s" % fingers)

            if fingers in self.HANDCODES:
                return [self.drawHandShape(traj,fingers[0],holdstart,holdstop,hold,strokedeco)]
            else:
                return [self.drawMovementTrajectory(traj,fingers,holdstart,holdstop,hold,strokedeco)]

    def drawHandShape(self,traj,handtype,holdstart,holdstop,hold,decor):
        handsymblinew = 3.0
        if traj['role'] != "HAND":
            raise InputError("inconcistent role for drawHandShape: %s" % traj)
        trajdeco = copy.deepcopy(decor) + [pyx.color.transparency(self.stroketransp),style.linestyle.dashdotted,style.linewidth(self.handstrokewidth)]
        symbdeco = copy.deepcopy(decor) + [style.linewidth(handsymblinew)]
        primaryHand = handtype.islower()
        if traj['move']in ['REPEAT','OSCILLATE']:
            symbdeco.append(style.dash([0.8,0.8]))

        self.symbaker.setSizeOnce(self.symbolsize*1.5)
        if handtype in 'sS':
            ### Handkante
            #trajdeco.append(style.linewidth(self.strokewidth*3))
            markers = self.drawSVGPath(traj['svgpath'],trajdeco)
            x,y = markers[0]
            if handtype == 's':
                self.symbaker.putSymbol('edgeOfHandR',x,y,symbdeco)
            else:
                self.symbaker.putSymbol('edgeOfHandL',x,y,symbdeco)

        elif handtype in 'hH':
            ### flache Hand
            markers = self.drawSVGPath(traj['svgpath'],trajdeco)
            x,y = markers[0]
            if handtype == 'h':
                self.symbaker.putSymbol('flatHandR',x,y,symbdeco)
            else:
                self.symbaker.putSymbol('flatHandL',x,y,symbdeco)
        elif handtype in 'bB':
            ### Handruecken
            markers = self.drawSVGPath(traj['svgpath'],trajdeco)
            x,y = markers[0]
            if handtype == 'b':
                self.symbaker.putSymbol('backHandR',x,y,symbdeco)
            else:
                self.symbaker.putSymbol('backHandL',x,y,symbdeco)
        elif handtype in 'kK':
            ### Kralle
            markers = self.drawSVGPath(traj['svgpath'],trajdeco)
            x,y = markers[0]
            if primaryHand:
                self.symbaker.putSymbol('\C',x,y,symbdeco)
            else:
                self.symbaker.putSymbol('/C',x,y,symbdeco)
        self.symbaker.resetSize()
        self.symbaker.setSizeOnce(self.symbolsize*1.8)
        if handtype in hold:
            self.symbaker.putSymbol('hold',x,y,decoration=symbdeco)
        self.symbaker.resetSize()
        traj['markers'] = markers
        return traj

    def drawMovementTrajectory(self,traj,finger,holdstart,holdstop,hold,decoration):
        trajdeco = copy.deepcopy(decoration) + [pyx.color.transparency(self.stroketransp)]
        symbdeco = copy.deepcopy(decoration)
        trajectoryStroke = True

        if traj['move'] == 'REPEAT':
            trajdeco += [style.dash([1.5,1.5])]
        elif traj['move'] == 'OSCILLATE':
            trajdeco += [style.dash([2,1,1,1])]
        elif traj['move'] == 'DIFFUSE':
            trajdeco += [deco.filled([pyx.color.transparency(0.8)])]
            trajectoryStroke = False
        elif traj['move'] == 'HATCH_DOTS':
            #print "JAAA"
            patt = pyx.pattern.pattern(xstep=pyx.unit.x_pt*2,ystep=pyx.unit.x_pt*2)
            patt.text(0, 0, r".",[pyx.trafo.scale(0.3)])
            #patt.stroke(path.circle(1,1,10),[pyx.color.rgb(1,1,1),deco.filled()])
            #patt.stroke(path.rect(1.,1.,1.,1.))
            trajdeco +=[patt,deco.filled()]
            trajectoryStroke = False
        elif traj['move'] == 'HATCH':
            #print "JAAA"
            patt = pyx.pattern.pattern(xstep=pyx.unit.x_pt*1.15,ystep=pyx.unit.x_pt*2.95)
            patt.text(0, 0, r"$\backslash$",[pyx.trafo.scale(0.3)])
            #patt.stroke(path.circle(1,1,10),[pyx.color.rgb(1,1,1),deco.filled()])
            #patt.stroke(path.rect(1.,1.,1.,1.))
            trajdeco +=[patt,deco.filled()]
            trajectoryStroke = False

        if trajectoryStroke:
            if finger in 'lL':
                ### drawing something
                if traj['role'] == 'DRAW-LIGHT':
                    if traj['move'] != 'ONCE':
                        print ("!!  ignoring movement pattern in DRAW-LIGHT mode")
                    #trajdeco += [style.linewidth(self.draww*0.6),style.dash([0.5,2])]
                    trajdeco += [style.linewidth(self.draww*0.6),style.dash([0.5,2])]
                else:
                    trajdeco += [style.linewidth(self.draww)]
            elif finger in self.HANDCODES:
                trajdeco += [style.linewidth(self.handstrokewidth)]
            elif finger in self.NONDRAW:
                if traj['move'] == 'ONCE':
                    trajdeco += [style.linewidth(self.strokewidth),style.dash([4,1])]
                else:
                    trajdeco += [style.linewidth(self.strokewidth)]
        try:
            symb = self.finger2symbol[finger]
        except KeyError:
            symb = finger
        traj['finger'] = finger

        if finger in '12345' or finger.isupper():
            symbdeco2 = symbdeco + [deco.filled([pyx.color.transparency(self.symbolfilltrans)])]
        else:
            symbdeco2 = symbdeco

        if traj['type'] == TRAJ_ORDINARY:
            markers = self.drawSVGPath(traj['svgpath'],trajdeco)
            x,y = markers[0]
            #print 'drawSymb',x,y,symb
            #print "cc", symbdeco
            if finger not in self.HANDCODES:
                self.symbaker.putSymbol(symb,x,y,symbdeco2+[style.linewidth(self.symbolstrokewidth)])
        elif traj['type'] == TRAJ_SODIPODI:
            x,y = traj['centre']
            if traj['move']in ['REPEAT','OSCILLATE']:
                self.symbaker.setSizeOnce(self.symbolsize*1.3)
                markers = self.drawSymbol(symb,x,y,symbdeco2+[style.dash([0.5,0.5]),style.linewidth(self.symbolstrokewidth*1.4)])
                self.symbaker.resetSize()
            elif traj['move'] == 'ONCE':
                markers = self.drawSymbol(symb,x,y,symbdeco2+[style.linewidth(self.symbolstrokewidth)])
            else:
                raise InputError("unknown movement parameter %s" % traj['move'])

        ### do the HOLD business if necessary
        #if finger in holdstart and finger in holdstop:
        #   msg = "!!  Holdstart and hold stop for the same finger."
        #   print msg
        #   raise InputError(msg)
        #print "FI:%s HS:%s HO:%s"  % (finger,holdstart,hold)
        if finger in hold:
            x,y = markers[-1]
            self.symbaker.putSymbol('hold',x,y,decoration=symbdeco)
        else:
            if finger in holdstart:
                ### if there is a trajectory for that finger and a hold starts with this finger
                ### the rule is that the hold starts at the end of the trajectory
                x,y = markers[-1]
                self.symbaker.putSymbol('holdStart',x,y,decoration=symbdeco)
        if finger in holdstop:
                x,y = markers[0]
                self.symbaker.putSymbol('holdStop',x,y,decoration=symbdeco)

        traj['markers'] = markers
        return traj

    NONDRAW = '123456789aeEpP'
    HANDCODES = 'sSbBhHkK'
    finger2symbol = {'1':'square', '2':'triangle', '3':'O', '4':'diamond', '5':'n', '6':'square', '7':'triangle', '8':'O', '9':'diamond', 'a':'n',
                     'e':'penR', 'E':'penL', 'p':'penR', 'P':'penL', 'l':'drawP', 'L':'drawS'}

    def drawSymbol(self,symbol,x,y,decoration):
        #self.canvas.stroke(path.circle(x,y,0.5), [sodicolor])
        #y = y*self.yfactor+self.yoffset
        ### used transform earlier
        x,y = self.tra.apply(x,y)
        self.symbaker.putSymbol(symbol,x,y,decoration)
        return [(x,y)]

    def drawSVGPath(self,pathdata,stxx):
        #print "PD:%s" %pathdata
        ### EXAMLE:
        ### m 525.18708,493.92641 c -173.15095,13.84621 66.987,219.42258 66.987,53.24607 0,-49.46866 -26.468,-36.86909 -66.987,-53.24607 l 0,0 z
        ### m 997.93446,574.86515
        #   c -245.34003,54.56707 92.75124,347.8783 92.75124,85.88076
        #   0,-44.25264 -21.9212,-90.29211 -58.3989,-91.03361
        #    -160.36589,-3.25985 -213.98699,285.59403 72.1398,194.09053
        r = re.compile(r"\s+")
        r2 = re.compile(r",")
        plist =  r.split(pathdata)
        begin = True
        com = ''
        param = []
        markerpoints = []
        pyxp = pyx.path.path()
        for p in plist:
            if p.isalpha():
                com = p
                if com in ['z','Z']:
                    ## close the Path
                    pyxp.append(pyx.path.closepath())
                    xalt,yalt=markerpoints[0]
                    markerpoints.append((xalt,yalt))
            else:
                ### p must be a parameter
                xstr,ystr = r2.split(p)
                x,y = (float(xstr),float(ystr))
                param.append( (x,y) )
                if com == 'm':
                    if begin:
                        ## absolute move
                        pyxp.append(pyx.path.moveto(x,y))
                        param = []
                        markerpoints.append((x,y))
                        begin = False
                    else:
                        ## relative move
                        pyxp.append(pyx.path.rmoveto(x,y))
                        xalt,yalt=markerpoints[-1]
                        markerpoints.append((xalt+x,yalt+y))
                        param = []
                    com = 'l'   ## relative lineTo implicit command for follow-up parameters
                elif com == 'M':
                    ## absolute move
                    #print "moveto2 XY:%f,%f" % (x,y)
                    pyxp.append(pyx.path.moveto(x,y))
                    param = []
                    markerpoints.append((x,y))
                    com = 'L'   ## absolute lineTo as implicit command for follow-ups
                elif com == 'l':
                    ## relative lineTo
                    #print "rlineto XY:%f,%f" % (x,y)
                    pyxp.append(pyx.path.rlineto(x,y))
                    xalt,yalt=markerpoints[-1]
                    markerpoints.append((xalt+x,yalt+y))
                    param = []
                elif com == 'L':
                    ## absolute lineTo
                    #print "lineto XY:%f,%f" % (x,y)
                    pyxp.append(pyx.path.lineto(x,y))
                    param = []
                    markerpoints.append((x,y))
                elif com == 'c' and len(param) == 3:
                    ## relative curveTo
                    x1,y1 = param[0]
                    x2,y2 = param[1]
                    ### hier wohl nicht . . .
                    #x1,y1 = self.transform(x1,y1)
                    #x2,y2 = self.transform(x2,y2)
                    #print ("RCURVE:%s" % str((x1,y1,x2,y2,x,y)))
                    pyxp.append(pyx.path.rcurveto(x1,y1,x2,y2,x,y))
                    xalt,yalt=markerpoints[-1]
                    param = []
                    markerpoints.append((xalt+x,yalt+y))
                elif com == 'C' and len(param) == 3:
                    ## absolute curveTo
                    x1,y1 = param[0]
                    x2,y2 = param[1]
                    ### hier wohl nicht . . .
                    #x1,y1 = self.transform(x1,y1)
                    #x2,y2 = self.transform(x2,y2)
                    pyxp.append(pyx.path.curveto(x1,y1,x2,y2,x,y))
                    param = []
                    markerpoints.append((x,y))

        self.canvas.stroke(pyxp,[self.tra]+stxx)
        markerpoints = [self.tra.apply(x,y) for x,y in markerpoints]
        return markerpoints

class PyxPalette(object):
    htmpat = re.compile("#?([abcdef\d]{6})")
    def __init__(self):
        self.colors = []

    def rotate(self):
        self.colors = self.colors[1:] + self.colors[:1]

    def extractFromHTMFile(self,fname):
        f = open(fname,'r')
        c = f.read()
        f.close()
        for m in self.htmpat.finditer(c):
            self.addColorHTM(m.groups()[0])

    def addColorHTM(self,code):
        code2 = self.htmpat.match(code).groups()[0]
        rr,gg,bb = code2[0:2],code2[2:4],code2[4:6]
        r,g,b = int('0x'+rr,0) , int('0x'+gg,0) , int('0x'+bb,0)
        self.addColorRGB256(r,g,b)

#   def addColorRGBhex(self,rr,gg,bb):
#       rr,gg,bb = code2[0:2],code2[2:4],code2[4:6]
#       r,g,b = int('0x'+rr) , int('0x'+gg) , int('0x'+bb)
#       self.addColorRGB256()

    def addColorRGB(self,r,g,b):
        self.colors.append(pyx.color.rgb(r,g,b))

    def addColorRGB256(self,r,g,b):
        self.colors.append(pyx.color.rgb(r/256.0,g/256.0,b/256.0))

    def getColor(self, idx=0):
        return self.colors[idx]


class SymbolMaker(object):
    def __init__(self,canvas,size=15,linewidth=1):
        self.newCanvas(canvas)
        self.size = size
        self.rad = size/2
        ### currently only for calculation purposes (such as thickness of lines and corresponding gaps, offsets etc.)
        # the actual line drawing width is 'hidden' in the decoration.
        self.linew = linewidth

        self.sfLookup = {
            'OO':self.put_OO ,
            'O':self.put_O ,
            'bigO':self.put_bigO ,
            'hold':self.put_hold ,
            'holdStart':self.put_holdStart ,
            'holdStop':self.put_holdStop ,
            'B':self.put_B,
            'square':self.put_square,
            'triangle':self.put_triangle,
            'tria':self.put_triangle,
            'dia':self.put_diamond,
            'diamond':self.put_diamond,
            'n':self.put_n,
            #'penOR':self.put_penOR,
            #'penOL':self.put_penOL,
            'penR':self.put_penR,
            'penL':self.put_penL,
            'omega':self.put_omega,
            'drawP':self.put_drawP,
            'drawS':self.put_drawS,
            'backHandR':self.put_backHandR,
            'backHandL':self.put_backHandL,
            'flatHandR':self.put_flatHandR,
            'flatHandL':self.put_flatHandL,
            'edgeOfHandR':self.put_edgeOfHandR,
            'edgeOfHandL':self.put_edgeOfHandL,
            '\C':self.put_graspingHandR,
            '/C':self.put_graspingHandL
             }

    cos30 = 0.866025404
    sin60 = cos30
    sin10 = 0.173648178
    cos10 = 0.984807753
    cos20 = 0.939692621
    sin20 = 0.342020143

    def newCanvas(self,canvas):
        self.canvas = canvas

    def putText(self,x,y,text,attr=[]):
        logging.info("H-LATEX:%s" % cleanTexInput(text))
        self.canvas.text(x,y,cleanTexInput(text),attr)

    def setSizeOnce(self,size):
        self.oldsize=self.size
        self.size=size
        self.rad = size/2

    def resetSize(self):
        self.size=self.oldsize
        self.rad = self.size/2

    def put_OO(self,x,y,decoration):
        self.canvas.stroke(pyx.path.circle(x, y, self.rad), decoration)
        self.canvas.stroke(pyx.path.circle(x, y, self.size/3), decoration)

    def put_O(self,x,y,decoration):
        self.canvas.stroke(pyx.path.circle(x, y, self.rad), decoration)

    def put_bigO(self,x,y,decoration):
        self.canvas.stroke(pyx.path.circle(x, y, self.rad*2), decoration)

    ###hold
    def put_hold(self,x,y,decoration):
        self.putSymbol('bigO',x,y,decoration=decoration+[style.linewidth(4)])

    ###holdstart
    def put_holdStart(self,x,y,decoration):
        self.putSymbol('bigO',x,y,decoration=decoration+[style.linewidth(4),style.dash([1.4,1.4])])

    ###holdstop
    def put_holdStop(self,x,y,decoration):
        self.setSizeOnce(self.size*0.7)
        self.putSymbol('bigO',x,y,decoration=decoration+[style.linewidth(4),style.dash([1.5,1.5])])
        self.resetSize()

    def put_o(self,x,y,decoration):
        rad=self.size/2
        self.canvas.stroke(pyx.path.circle(x, y, self.rad/2), decoration)

    def put_B(self,x,y,decoration):
        self.canvas.stroke(pyx.path.circle(x, y, rad/2), decoration)

    def put_square(self,x,y,decoration):
        self.canvas.stroke(pyx.path.rect(x-self.rad, y-self.rad, self.size,self.size), decoration)

    def put_triangle(self,x,y,decoration):
        x1,y1 = x-self.cos30*self.rad,y-self.rad/2
        x2,y2 = x+self.cos30*self.rad,y-self.rad/2
        x3,y3 = x,y+self.rad
        self.putPolygonC([(x1,y1),(x2,y2),(x3,y3)],decoration)

    def put_diamond(self,x,y,decoration):
        self.putPolygonC([(x-self.rad,y),(x,y-self.rad),(x+self.rad,y),(x,y+self.rad)],decoration)

    def put_n(self,x,y,decoration):
        p = pyx.path.path()
        p.append(pyx.path.arcn(x,y, self.rad, 0, 180))
        self.canvas.stroke(p,decoration)

    def put_penR(self,x,y,decoration):
        sc = pyx.canvas.canvas()
        w = self.sin20*self.rad
        h = self.cos20*self.rad
        sc.stroke(pyx.path.rect(x-w/2, y, w, h),decoration+[deco.filled()])
        sc.stroke(pyx.path.line(x-w/2, y+h, x-w/2,y+self.size),decoration)
        sc.stroke(pyx.path.line(x+w/2, y+h, x+w/2,y+self.size),decoration)
        self.canvas.insert(sc, [pyx.trafo.translate(0,self.rad/3),pyx.trafo.rotate(310,x,y)])

    def put_penL(self,x,y,decoration):
        sc = pyx.canvas.canvas()
        w = self.sin20*self.rad
        h = self.cos20*self.rad
        sc.stroke(pyx.path.rect(x-w/2, y, w, h),decoration+[deco.filled()])
        sc.stroke(pyx.path.line(x-w/2, y+h, x-w/2,y+self.size),decoration)
        sc.stroke(pyx.path.line(x+w/2, y+h, x+w/2,y+self.size),decoration)
        self.canvas.insert(sc, [pyx.trafo.translate(0,self.rad),pyx.trafo.rotate(50,x,y)])

    def put_omega(self,x,y,decoration):
        print ("!! put OMEGA not implemented.")

    def put_drawP(self,x,y,decoration):
        #print "+ + +"
        x,y = x+self.linew*1.8, y+self.linew*3
        poly = [(x,y),(x-self.rad/6,y+self.rad),(x+self.rad/6,y+self.rad)]
        self.putPolygonC (poly,decoration+[pyx.trafo.rotate(-30,x,y),deco.filled()])

    def put_drawS(self,x,y,decoration):
        x,y = x-self.linew*1.8, y+self.linew*3
        poly = [(x,y),(x-self.rad/6,y+self.rad),(x+self.rad/6,y+self.rad)]
        self.putPolygonC (poly,decoration+[pyx.trafo.rotate(30,x,y),deco.filled()])

    def put_flatHandR(self,x,y,decoration):
        outeredge = self.rad*0.7
        p = pyx.path.path()
        p.append(pyx.path.moveto(x-self.rad,y+self.size))
        p.append(pyx.path.lineto(x-self.rad,y-self.rad))
        p.append(pyx.path.lineto(x+outeredge,y-self.rad))
        p.append(pyx.path.curveto(x+outeredge,y+self.size/2.0,x+outeredge/2.0,y+self.size,x-self.rad,y+self.size))
        p.append(pyx.path.closepath())
        self.canvas.stroke(p,decoration+[pyx.deco.filled()])
        p = pyx.path.path()
        p.append(pyx.path.moveto(x-self.rad-self.size/8,y+self.rad*0.7))
        p.append(pyx.path.lineto(x-self.rad-self.size/8,y-self.rad))
        p.append(pyx.path.lineto(x-self.rad,y-self.rad))
        self.canvas.stroke(p,decoration)

    def put_flatHandL(self,x,y,decoration):
        outeredge = self.rad*0.7
        p = pyx.path.path()
        p.append(pyx.path.moveto(x+self.rad,y+self.size))
        p.append(pyx.path.lineto(x+self.rad,y-self.rad))
        p.append(pyx.path.lineto(x-outeredge,y-self.rad))
        p.append(pyx.path.curveto(x-outeredge,y+self.size/2.0,x-outeredge/2.0,y+self.size,x+self.rad,y+self.size))
        p.append(pyx.path.closepath())
        self.canvas.stroke(p,decoration+[pyx.deco.filled()])
        p = pyx.path.path()
        p.append(pyx.path.moveto(x+self.rad+self.size/8,y+self.rad*0.7))
        p.append(pyx.path.lineto(x+self.rad+self.size/8,y-self.rad))
        p.append(pyx.path.lineto(x+self.rad,y-self.rad))
        self.canvas.stroke(p,decoration)

    def put_backHandR(self,x,y,decoration):
        #basically an unfilled flat hand L
        outeredge = self.rad*0.7
        p = pyx.path.path()
        p.append(pyx.path.moveto(x+self.rad,y+self.size))
        p.append(pyx.path.lineto(x+self.rad,y-self.rad))
        p.append(pyx.path.lineto(x-outeredge,y-self.rad))
        p.append(pyx.path.curveto(x-outeredge,y+self.size/2.0,x-outeredge/2.0,y+self.size,x+self.rad,y+self.size))
        p.append(pyx.path.closepath())
        self.canvas.stroke(p,decoration)
        p = pyx.path.path()
        p.append(pyx.path.moveto(x+self.rad+self.size/8,y+self.rad*0.7))
        p.append(pyx.path.lineto(x+self.rad+self.size/8,y-self.rad))
        p.append(pyx.path.lineto(x+self.rad,y-self.rad))
        self.canvas.stroke(p,decoration)

    def put_backHandL(self,x,y,decoration):
        #basically an unfilled flat hand R
        outeredge = self.rad*0.7
        p = pyx.path.path()
        p.append(pyx.path.moveto(x-self.rad,y+self.size))
        p.append(pyx.path.lineto(x-self.rad,y-self.rad))
        p.append(pyx.path.lineto(x+outeredge,y-self.rad))
        p.append(pyx.path.curveto(x+outeredge,y+self.size/2.0,x+outeredge/2.0,y+self.size,x-self.rad,y+self.size))
        p.append(pyx.path.closepath())
        self.canvas.stroke(p,decoration)
        p = pyx.path.path()
        p.append(pyx.path.moveto(x-self.rad-self.size/8,y+self.rad*0.7))
        p.append(pyx.path.lineto(x-self.rad-self.size/8,y-self.rad))
        p.append(pyx.path.lineto(x-self.rad,y-self.rad))
        self.canvas.stroke(p,decoration)

    def put_edgeOfHandR(self,x,y,decoration):
        size = self.size
        xoff = size/2
        self.canvas.stroke(pyx.path.line(x+xoff, y, x+xoff, y+size), decoration)
        self.canvas.stroke(pyx.path.line(x+xoff-size/8, y, x+xoff-size/8, y+size/3), decoration)
        p = pyx.path.path()
        p.append(pyx.path.arcn(x+xoff-size/16,y, self.size/16, 0, 180))
        self.canvas.stroke(p, decoration)

    def put_edgeOfHandL(self,x,y,decoration):
        size = self.size
        xoff = -size/2
        self.canvas.stroke(pyx.path.line(x+xoff, y, x+xoff, y+size), decoration)
        self.canvas.stroke(pyx.path.line(x+xoff+size/8, y, x+xoff+size/8, y+size/3), decoration)
        p = pyx.path.path()
        p.append(pyx.path.arcn(x+xoff+size/16,y, self.size/16, 0, 180))
        self.canvas.stroke(p, decoration)

    def put_graspingHandR(self,x,y,decoration):
        p = pyx.path.path()
        p.append(pyx.path.arcn(x,y,self.rad, 250, 290))
        self.canvas.stroke(p,decoration)
        self.canvas.stroke(pyx.path.line(x,y+self.rad,x+self.size,y+self.rad),decoration)

    def put_graspingHandL(self,x,y,decoration):
        p = pyx.path.path()
        p.append(pyx.path.arcn(x,y,self.rad, 250, 290))
        self.canvas.stroke(p,decoration)
        self.canvas.stroke(pyx.path.line(x,y+self.rad,x-self.size,y+self.rad),decoration)

    def putSymbol(self,symbol,x,y,decoration):
        if symbol not in self.sfLookup:
            self.canvas.text(x,y,symbol,[pyx.color.rgb(0.8,0,0.8)])
        else:
            self.sfLookup[symbol](x,y,decoration)

    def putCross(self,x,y,size,decorate=[]):
        if not size:
            size = self.symbolsize

        self.canvas.stroke(pyx.path.circle(x, y, size), decorate)
        self.canvas.stroke(pyx.path.line(x-size, y, x+size, y), decorate)
        self.canvas.stroke(pyx.path.line(x, y-size, x, y+size), decorate)

    def putPolygon(self,edges,decoration):
        polypath = pyx.path.path()
        x,y = edges[0]
        polypath.append(pyx.path.moveto(x,y))
        for x,y in edges[1:]:
            polypath.append(pyx.path.lineto(x,y))
        #polypath.append(path.multilineto_pt(polygonEdges[0]))
        #polypath.append(path.closepath())
        self.canvas.stroke(polypath,decoration)

    def putPolygonC(self,edges,decoration):
        polypath = pyx.path.path()
        x,y = edges[0]
        polypath.append(pyx.path.moveto(x,y))
        for x,y in edges[1:]:
            polypath.append(pyx.path.lineto(x,y))
        polypath.append(pyx.path.closepath())
        self.canvas.stroke(polypath,decoration)


