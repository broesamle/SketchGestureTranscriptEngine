""" Main controller.
    Command line settings, input file names etc. are handled here.
    It should explicitly be kept abstract regarding the used types of sequences, visualisers and so on. This is to be handled by imported Modules. """

from operator import itemgetter
import xml.dom.minidom as xml
#import pyx         ### no need for pyx any more: stuff seems to be encapsulated in Visualiser
import os.path
import copy
import re

### prepare logging
LOG_FILENAME = 'drawGestureActivity.log'

### remove old logmessages (delete old logfile)
f = open(LOG_FILENAME,'w')
f.close()

import logging
logging.basicConfig(filename=LOG_FILENAME,level=logging.ERROR)

logging.info("Begin logs...")

print ("----------------- SpaDoAK-G1 (v02) -----------------")
print ("LOGGING: " + LOG_FILENAME)

from ..TranscriptIntegration.WTimelineA import AnnotatedSequence
from ._utils import fetchIfNotDef, fetchOrDefault
from .CorpusXML import XMLCorpusDocument, CorpusDescriptorDocument
from .Visualizer import Visualizer
from .procSeq2PDF import SeqProcessor,LoadedTrajManager

################################################
### Get Commandline Options
################################################
import argparse
parser = argparse.ArgumentParser(description='...')
parser.add_argument('-s','--sessions', type=str, nargs='+', default=[], help='Sessions to be printed.')
parser.add_argument('-e','--episodes', type=str, nargs='+', default=[], help='Episodes to be printed.')
parser.add_argument('-p','--pages', type=str, nargs='+', default=[], help='Pages to be printed. (relative to respective episode)')

parser.add_argument('-B','--begin', type=int, default=None, help='Index where the printing starts. (relative to respective episode)')
parser.add_argument('-E','--end', type=int, default=None, help='Index where the printing stops. (relative to respective episode)')
parser.add_argument('-P','--project', type=str, default="ProjectDescriptor.xml", help='The file containging this project`s descriptor.')
#parser.add_argument('-I','--inpoint', type=str, default='', help='Index where the printing starts')
#parser.add_argument('-O','--outpoint', type=str, default='', help='Index where the printing stops')

parser.add_argument('-L','--textperline', type=int, default=None, help='Maximum number of sequence chars printed in one line. (overrides project settings)')
parser.add_argument('-G','--graphpagelength', type=int, default=None, help='Maximum chars printed in one graphics page. (overrides project settings)')
parser.add_argument('-X','--textx', type=int, default=None, help='X position of the text line on the page. (overrides project settings)')
parser.add_argument('-Y','--texty', type=int, default=None, help='Y position of the text line on the page. (overrides project settings)')
parser.add_argument('-S','--textscale', type=float, default=None, help='scale factor for text size. (overrides project settings)')
parser.add_argument('-T','--textpagelength', type=int, default=None, help='Maximum chars printed in one text page. (overrides project settings)')

parser.add_argument('-U','--simulate', action='store_true', help='just simulate, do not generate PDF output')
parser.add_argument('-c','--slice', action='store_true', help='Generate each stroke on a separate page.')

parser.add_argument('-d','--hideids', action='store_true', help='hide stroke IDs')
parser.add_argument('-m','--hidecomments', action='store_true', help='')
parser.add_argument('-a','--hidetimestamps', action='store_true', help='hide timestamps')
parser.add_argument('-k','--hidespeakers', action='store_true', help='')
parser.add_argument('-r','--hidephrases', action='store_true', help='')
parser.add_argument('-z','--hideheaders', action='store_true', help='')
parser.add_argument('-b','--hidecolouredformatbars', action='store_true', help='')
parser.add_argument('-H','--hideall', action='store_true', help='hides everything except the Essence!')
parser.add_argument('-y','--bboxtext', action='store_true', help='')
parser.add_argument('-j','--trajectorylabels', action='store_true', help='Print trajectory labels')
parser.add_argument('-J','--trajectoryprefixes', type=str, nargs='+', default=[], help='Prefixes to be removed from the trajectory labels.')
parser.add_argument('-f','--outsuffix',type=str,default="",help='override the automatic output filename suffix')
parser.add_argument('-C','--colorpalettefile',type=str,default="",help='name of a GIMP-exported *.html file containing a palette image as a table.')

args = parser.parse_args()

projectArg = args.project
sessionsArg = args.sessions
episodesArg = args.episodes

pagesArg = []
for p in args.pages:
    if '-' in p:
        pa,pb = p.split('-')
        pagesArg += range(int(pa),int(pb)+1)
    else:
        pagesArg.append(int(p))

beginArg = args.begin
endArg = args.end
textPageLenArg = args.textpagelength
graphPageLenArg = args.graphpagelength
textPerLineArg = args.textperline
textScaleArg = args.textscale
textXarg,textYarg = args.textx,args.texty

if args.hideall:
    args.hidecomments = True
    args.hideheaders = True
    args.hideids = True
    args.hidephrases = True
    args.hidespeakers = True
    args.hidetimestamps = True

### if neither command line option nor project file define text per line
# this value will be used.
textPerLineDefault = 180

simulateArg = args.simulate

if simulateArg:
    print ("SIMULATION MODE -- no PDF output will be generated")

################################################
### Get Corpus Descriptors
################################################
logging.info("Get Project Descriptor from %s" % projectArg)
descrdoc = CorpusDescriptorDocument(projectArg)
projectInfo = "[%s]%s" %  ( descrdoc.getProjectID() , descrdoc.getProjectDescription() )
print ("PROJECT:%s  FILE:%s  GESTURE/SPEECH-PATH:%s" % (descrdoc.getProjectID(), projectArg ,descrdoc.getGestureSpeechPath()) )

################################################
### Read Descriptor Infos
################################################
oldTrnscrBlockID = ""
################################################

### Get Trajectory Ressource Definitions
################################################

### fetch a list of dictionaries containing all ressource definitions
allRessources = descrdoc.getAllRessources()

loadedTraj = LoadedTrajManager()
allTrajectories = {}

for ressource in allRessources:
    if ressource['type'] == 'svg-trajectories':
        allTrajectories[ressource['id']] = ressource
        loadedTraj.defineTrajRessource(ressource['id'],ressource['file'])

################################################
### Sessions loop
################################################

allsessions = descrdoc.getAllSessions()

allsessions2 = []
if sessionsArg != []:
    for s in allsessions:
        if s[0] in sessionsArg:
            allsessions2.append(s)
else:
    allsessions2 = allsessions


seqproc = SeqProcessor (None,loadedTraj)
for sessID,sessDescr,people in allsessions2:
    sessionInfo = "[%s]%s" % (sessID,sessDescr)

    logging.info("processing session %s:%s with %s" % (sessID,sessDescr,people) )
    print ( "SESS:%s(%s)  PEOPLE:%s" % (sessID, sessDescr, people) )

    for episode in descrdoc.getEpisodesBySession(sessID):

        if episodesArg != [] and episode['id'] not in episodesArg:
            print("...skipping episode %s" % episode['id'])
            continue

        try:
            episodeDescr = episode['descr']
        except KeyError:
            episodeDescr = "--no Episode Descrition--"


        episodeID = episode['id']



        ### timelines are amalgamated with transcript sequences in descriptor version 1.1
        ### if multiple text/video streams will be needed in the future, timelines may be a helpul organizational unit.
        #timelineID = episode['timeline']
        ### in 1.0 the following two info items where in the timeline definition
        trnscrseqID = episode['transcriptsequence']
        trnscrblockID = episode['transcriptblock']

        print("EPISODE:%s  BLOCK:%s  SEQ:%s" % (episodeID, trnscrblockID, trnscrseqID))



        ##############################
        ### Get Transcript Block
        ##############################
        newTrnscrBlockID = trnscrblockID

        if oldTrnscrBlockID != newTrnscrBlockID:
            ### if the transcriptblock changes, load the new one
            oldTrnscrBlockID = newTrnscrBlockID
            trnscrblockFn = descrdoc.getResource(newTrnscrBlockID)['file']
            #logging.info( "loading new transcript block newTrnscrBlockID from file %s" % (newTrnscrBlockID,trnscrblockFn) )

            print ("TRNSCR:%s TRNSCR-XML:%s" % (newTrnscrBlockID,trnscrblockFn))
            logging.info("TRNSCR %s from:%s" % (newTrnscrBlockID,trnscrblockFn))

            trnscrblock = XMLCorpusDocument()
            trnscrblock.readXMLfile(trnscrblockFn)

            #listOfAseqs = trnscrblock.getTranscriptSequences()



        ################################################
        ### Get Data from Episode
        ################################################

        ######
        ### prefixes
        ######

        if 'transcript_id_prefix' in episode:
            transcrIdPrefix = episode['transcript_id_prefix']
        else:
            transcrIdPrefix = ""

        if 'spatial_id_prefix' in episode:
            spatialIdPrefix = episode['spatial_id_prefix']
        else:
            spatialIdPrefix = ""

        print("PREFIX spatial/transcript: %s / %s" % (spatialIdPrefix, transcrIdPrefix))


        ######
        ### transcript subsequence (based on episode or in/outpoint)
        ######
        if 'transcriptsection' in episode:
            intervalID = episode['transcriptsection']
            inpoint,outpoint = None,None
            basedOn = "(INT:"+intervalID+')'
        else:
            intervalID = None
            inpoint,outpoint = episode['inpoint'],episode['outpoint']
            basedOn = "(IN/OUT)"

        logging.info ("Getting annotated sequence from current transcript block: %s, %s..%s" % (trnscrseqID,inpoint,outpoint))

        print("Getting annotated sequence from current transcript block: %s, %s..%s" % (trnscrseqID, inpoint, outpoint))

        logging.info( "Episode %s: %s..%s INT:%s " % (episode['id'],inpoint,outpoint,intervalID) )
        print("EPISODE:%s  %s..%s  %s" % (episode['id'], inpoint, outpoint, basedOn))

        aseq = trnscrblock.getTranscriptSequnce(trnscrseqID,inpoint,outpoint,intervalID)


        ######
        ### trajectories and canvas
        ######
        spatialDataType = 'UNKNOWN'
        resIDs = []
        canvasD = {}
        if 'canvas' in episode:
            spatialDataType = 'CANVAS'
            canvasD = descrdoc.getCanvasAsDict(episode['canvas'])
            ctrajectorydata = descrdoc.getElementsFromCanvasAsDict(episode['canvas'],'TrajectoryData')

            if 'resourcesubset' in episode:
                ressubset = set(episode['resourcesubset'].split(','))
                for traj in ctrajectorydata:
                    resID = traj['resource']
                    if resID in ressubset:
                        resIDs.append(resID)
            else:
                for traj in ctrajectorydata:
                    resID = traj['resource']
                    resIDs.append(resID)
            spatialDataD = canvasD
            print("CANVAS:%s  RESOURCES:%s " % (episode['canvas'], resIDs))

        elif 'image-from-collection' in episode:
            spatialDataType = 'IMAGE_FROM_COLLECTION'
            imagecollectionResID, imagecollectionSelectedFile = episode['image-from-collection'].split(':')
            print("COLLECTION:%s IMAGE:%s " % (imagecollectionResID, imagecollectionSelectedFile))
            imagecollectionD = descrdoc.getResource(imagecollectionResID)
            spatialDataD = imagecollectionD
        else:
            print("!!  neither canvas nor trajectory data nor image collection defined.")

        loadedTraj.loadunloadTrajRessources(resIDs)

        ################################################
        ### Get Text/Graphics Parameters from spatialDataD
        ################################################
        # # #   Bei gelegenheit anpassen -- nicht heute, grad laeufts --

        textPerLine = fetchIfNotDef(textPerLineArg,spatialDataD,'textperline',textPerLineDefault,int)
        textPageLen = fetchIfNotDef(textPageLenArg,spatialDataD,'textpagelen',textPerLine*9,int)
        graphPageLen = fetchIfNotDef(graphPageLenArg,spatialDataD,'graphpagelen',textPerLine,int)

        textScale = fetchIfNotDef(textScaleArg,spatialDataD,'textscale',1.0,float)

        textX = fetchIfNotDef(textXarg,spatialDataD,'textx',0,int)
        textY = fetchIfNotDef(textYarg,spatialDataD,'texty',0,int)

        errx = fetchOrDefault(spatialDataD,'errx',None,int)
        erry = fetchOrDefault(spatialDataD,'erry',None,int)

        if 'paperFormat' in spatialDataD:
            paperformat = spatialDataD['paperFormat']
            #landscape = fetchOrDefault(spatialDataD,'landscape',0,int)
        elif 'paperWidth' in spatialDataD and 'paperHeight' in spatialDataD:
            try:
                paperformat = map((spatialDataD['paperWidth'],patialDataD['paperHeight']), int)
            except ValueError:
                raise InputError("paper width and height should be integers. (unit:millimeter)")

        landscape = fetchOrDefault(spatialDataD,'landscape',0,int)
        portrait = fetchOrDefault(spatialDataD,'portrait',0,int)

        if (landscape == 0 and portrait == 0):          # no setting was chosen by the user
            rotatePaper = 1     # use the historic default from the early days, where PyX output was on A4 landscape
        elif landscape == 1 and portrait == 0:
            rotatePaper = 1
        elif landscape == 0 and portrait == 1:
            rotatePaper = 0
        else:
            raise InputError('Incompatible orientation setting: landscape="%d" and portrait="%d"' % (landscape,portrait))

        ######
        ### create a visualizer
        ######
        v = Visualizer( pyxCanvas=None,
                        lineLen=textPerLine,
                        textX=textX, textY=textY,
                        errX=errx, errY=erry,
                        hideIDs=args.hideids,
                        hideComments=args.hidecomments,
                        hideTSs=args.hidetimestamps,
                        hideSpeakers=args.hidespeakers,
                        hidePhrases=args.hidephrases,
                        hideInfoHeader=args.hideheaders,
                        sliceStrokes=args.slice,
                        colorPaletteFN=args.colorpalettefile,
                        textScale=textScale,hideColouredFormatBars=args.hidecolouredformatbars)


        speakerpseudonyms = [pseudonym for id,pseudonym,role in people]

        v.initSpeakers(speakerpseudonyms)

        ################################################
        ### Set included images from loaded trajectories
        ################################################
        if spatialDataType == 'CANVAS':
            for traj in descrdoc.getElementsFromCanvasAsDict(episode['canvas'],'TrajectoryData'):
                if traj['resource'] in resIDs and 'includedimage' in traj:
                    imageFname = traj['includedimage']
                    x,y,w,h,filepath = loadedTraj.getLoaded(traj['resource']).getImageByFname(imageFname)
                    x = float(x)
                    y = float(y)
                    w = float(w)
                    h = float(h)

                    if not os.path.isabs(filepath):
                        ### the filepath is relative to the location of the SVG file
                        SVGFname = loadedTraj.getLoaded(traj['resource']).filename
                        filepath = os.path.join(os.path.dirname(SVGFname),filepath)

                    #filepath = filepath.encode('ascii')
                    filepath = os.path.abspath(filepath)

                    if 'imagecoordinates' in traj and traj['imagecoordinates'] == 'X-mirrorY':
                        print("coordinates mode: X-mirrorY")
                        coordMode = traj['imagecoordinates']
                        v.setTrajTransformation(yfactor=-1,yoffset=2*y + h)
                    else:
                        coordMode = "standard"
                        print("coordinates mode: standart identity transformation")
                        v.setTrajTransformation()
                    print("IMAGE INCL.:%s  RES:%s  COORD:%s" % (filepath,traj['resource'],coordMode))

                    v.defineBackgroundImage(x,y,w,h,filepath)
                    v.setMarkers(loadedTraj.getLoaded(traj['resource']))
                    boundingbox = v.getBBoxFromMarkers("UPPER_LEFT","LOWER_RIGHT")

        elif spatialDataType == 'IMAGE_FROM_COLLECTION':
            x = fetchOrDefault(imagecollectionD,'x',0,float)
            y = fetchOrDefault(imagecollectionD,'y',0,float)
            w = fetchOrDefault(imagecollectionD,'w',None,float)
            h = fetchOrDefault(imagecollectionD,'h',None,float)
            path = fetchOrDefault(imagecollectionD,'filepath',"file not defined!!!",(lambda x: x.encode('ascii')) )
            path = os.path.abspath(path)
            path = os.path.join(path,imagecollectionSelectedFile)
            v.defineBackgroundImage(x,y,w,h,path,transparency=0.1)
            print("IMAGE FROM COLLECTION:%s  RES:%s" % (path,imagecollectionD['id']))


        ### Text Position From Markers (silently overriding other definitions)
        if 'textfromMarker' in spatialDataD:
            try:
                v.setTextPositionFromMarker(spatialDataD['textfromMarker'])
                print("Set text position to Marker: %s" % spatialDataD['textfromMarker'])
            except ValueError as e:
                print("Warning: " + str(e))


        ########################################################################################################################
        ### create PDF output
        ########################################################################################################################


        spatialInfo = "[%s] %s" % (spatialDataD['id'],spatialDataD['descr'])
        episodeInfo = "[%s] %s" % (episode['id'],episode['descr'])
        trnscrseqInfo = trnscrseqID

        v.eraseMetaData()
        v.setMetaData(project=projectInfo,session=sessionInfo, episode=episodeInfo, spatial=spatialInfo, sequence=trnscrseqInfo)



        ### above inpoint outpoint and intevalID should have been set
        ### based on the EPISODE DEFINITION in the PROJECT
        ### aseq now contains that episode
        ### the users parameters will be interpreted relative to the episode

        ### inpoitn and outpoint are thus


        seqproc.setVisualizer(v)
        seqproc.setPaperFormat(paperformat,rotatePaper)
        PDFfname = "%s_%s_%s" % (descrdoc.getProjectID(),sessID,episodeID)
        PDFpath = descrdoc.getGestureSpeechPath()
        seqproc.processAnnotatedSequence(aseq, PDFfname, PDFpath,
            textPageLen,graphPageLen,
            inIdx=beginArg,outIdx=endArg,
            selectedPages=pagesArg,
            transcrIdPrefix=transcrIdPrefix,spatialIdPrefix=spatialIdPrefix,
            outputFileSuffix=args.outsuffix,
            simulate=simulateArg,
            backgroundPage=args.slice,
            bbox=boundingbox,
            bboxtext=args.bboxtext)
