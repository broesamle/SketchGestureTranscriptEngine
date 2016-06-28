import xml.dom.minidom as xml
#from logging import info
import logging

#from Include import keyAllTS
#from Include import
from ..TranscriptIntegration.WTimelineA import AnnotatedSequence, keyPremiereTSoffset
from ._utils import InputError

def attr2dict(node):
    x = {}
    for key in node.attributes.keys():
        x[key] = node.getAttribute(key)
    return x

class CorpusDescriptorDocument(object):
    def __init__(self,filename):
        print ("  INITIALIZING CORPUS DESCRIPTOR. %s" % filename)
        self.descriptorversion = "1.1"
        f = open(filename,'r')
        self.dom = xml.parse(f)
        f.close()

        self.corpusdescr = self.dom.documentElement
        if self.descriptorversion != self.corpusdescr.getAttribute("descriptorversion"):
            print ("!!  Warning: Descriptor Versions do not match.")
            #raise InputError("Descriptor Versions do not match.")

        self.projectID = self.corpusdescr.getAttribute('id')
        self.projectDescr = self.corpusdescr.getAttribute('descr')
        self.projectLongDescr = self.corpusdescr.getAttribute('longdescription')

        self.gestureSpeechPath = self.corpusdescr.getAttribute('gesturespeechpath')

        ### descriptor version 1.1 does not use timelines
        #self.timelines = {}
        #for tl in self.corpusdescr.getElementsByTagName("Timeline"):
        #   self.timelines[tl.getAttribute("id")] = tl

        self.canvases = {}
        for ca in self.corpusdescr.getElementsByTagName("Canvas"):
            self.canvases[ca.getAttribute("id")] = ca

        self.sessions = {}
        logging.debug("  CorpusDescriptorDocument.__init__ %s" % self.corpusdescr.getElementsByTagName("Session") )

        for se in self.corpusdescr.getElementsByTagName("Session"):
            self.sessions[se.getAttribute("id")] = se

        self.resources = {}
        self.trnscrblocks = {}
        for re in self.corpusdescr.getElementsByTagName("Resource"):
            self.resources[re.getAttribute("id")] = re
            if re.getAttribute('type') == "transcript-block":
                self.trnscrblocks[re.getAttribute('id')] = re

        print ("  RESOURCES: %s" % str(self.resources.keys()))


    def getProjectDescription (self):
        return self.projectDescr

    def getProjectID (self):
        return self.projectID

    def getGestureSpeechPath(self):
        return self.gestureSpeechPath

    #def getCanvas(self,x):
    #   return self.canvases[x].attributes

    #def getTimeline(self,x):
    #   return self.timelines[x].attributes

    def getResource(self,x):
        return attr2dict(self.resources[x])

    def getAllEpisodes(self):
        result = []
        for e in self.corpusdescr.getElementsByTagnName("Episode"):
            #result.append(e.attributes)
            result.append(attr2dict(e))

        return result

#   def getAllTrnscrBlocks(self):
#       result = []
#       for bockID,bl in self.trnscrblocks.items():
#           result.append(bl)
#       return result

### descriptor version 1.1 does not use timelines
#   def getMediaClipsByTimeline(self,tl):
#       result = []
#       for x in self.timelines[tl].getElementsByTagName('MediaClip'):
#           result.append(attr2dict(x))
#       return result
#
#   def getVerbalDataByTimeline(self,tl):
#       result = []
#       for x in self.timelines[tl].getElementsByTagName('VerbalData'):
#           result.append(attr2dict(x))
#       return result

#   def getPatchesByCanvas(self,can):
#       result = []
#       for x in self.canvases[can].getElementsByTagName('Patch'):
#           result.append(attr2dict(x))
#       return result

    def getElementsFromCanvasAsDict(self, canvasID,tagname):
        result = []
        if canvasID not in self.canvases:
            ValueError("%s is not a valid canvas ID." % canvasID )
        for el in self.canvases[canvasID].getElementsByTagName(tagname):
            result.append(attr2dict(el))
        return result

    def getCanvasAsDict(self,canvasID):
        if canvasID not in self.canvases:
            ValueError("%s is not a valid canvas ID." % canvasID )

        return attr2dict(self.canvases[canvasID])

    def getEpisodesBySession(self,sess):
        result = []
        for x in self.sessions[sess].getElementsByTagName('Episode'):
            result.append(attr2dict(x))
        return result

    def getAllRessources(self):
        result = []
        for resourceID,res in self.resources.items():
            result.append(attr2dict(res))
        return result

    def getAllSessions(self):
        logging.debug("getAllSessions:%s" % self.sessions )
        result = []
        for sID,s in self.sessions.items():
            descr = s.getAttribute('descr')
            people = []
            for p in s.getElementsByTagName('Person'):
                pattr = attr2dict(p)

                people.append((pattr['id'],pattr['pseudonym'],pattr['role']))
            result.append((sID,descr,people))
        return result


    #def getEpisodesByTrnscrBlock (self, block):







#           epiID = e.getAttribute("id")
#           timelineNode = self.timelines[e.getAttribute("timeline")]
#           canvasNode = self.timelines[e.getAttribute("canvas")]
#
#           mclips = []
#           for mediaclip in timelineNode.getElementsByTagName("MediaClip"):
#               clipID = self.resources[mediaclip.getAttribute("id")]
#               mclips.append((clipID,self.resources[clipID].getAttribute('file'),self.resources[clipID].getAttribute('description')))
#               ## (id,file,description)
#
#           canvases = []
#           for pat in canvasNode.getElementsByTagName("Patch"):
#               patchID = self.resources[pat.getAttribute("id")]
#               canvases.append((patchID,self.resources[patchID].getAttribute('file'),self.resources[clipID].getAttribute('description')))
#               ## (id,file,description)
#
#           inpoint, outpoint = e.getAttribute("inpoint") , e.getAttribute("outpoint")
#
#           result.append((epiID,inpoint,outpoint,mclips))


#   def getEpisodesData(self):
#       result = []
#       for e in self.corpusdescr.getElementsByTagnName("Episode"):
#           epiID = e.getAttribute("id")
#           timelineNode = self.timelines[e.getAttribute("timeline")]
#           canvasNode = self.timelines[e.getAttribute("canvas")]
#
#           mclips = []
#           for mediaclip in timelineNode.getElementsByTagName("MediaClip"):
#               clipID = self.resources[mediaclip.getAttribute("id")]
#               mclips.append((clipID,self.resources[clipID].getAttribute('file'),self.resources[clipID].getAttribute('description')))
#               ## (id,file,description)
#
#           canvases = []
#           for pat in canvasNode.getElementsByTagName("Patch"):
#               patchID = self.resources[pat.getAttribute("id")]
#               canvases.append((patchID,self.resources[patchID].getAttribute('file'),self.resources[clipID].getAttribute('description')))
#               ## (id,file,description)
#
#           inpoint, outpoint = e.getAttribute("inpoint") , e.getAttribute("outpoint")
#
#           result.append((epiID,inpoint,outpoint,mclips))




class XMLCorpusDocument(object):
    def __init__(self,transcriptVersion="2.0.1",text2xml=(lambda x:x)):
        self.transcriptversion = transcriptVersion
        self.text2xml = text2xml

    def initNewDocument(self,block='undefined-block'):
        impl = xml.getDOMImplementation()

        ### AnnotatedTranscript (ROOT/TOPLEVEL)
        self.dom = impl.createDocument(None, "AnnotatedTranscript", None)
        top_element = self.dom.documentElement

        ### DocumentInformation (no children, just versioning etc info)
        node = self.dom.createElement('DocumentInformation')
        node.setAttribute('corpusblock',block)
        node.setAttribute('transcriptversion',self.transcriptversion)
        top_element.appendChild(node)

        ### TranscriptData (the block containing the data)
        self.trdatanode = self.dom.createElement('TranscriptData')
        top_element.appendChild(self.trdatanode)


    def addAnnotatedSequence(self,seqID,aseq,source="?SRC?",video="?VID?", edl="?EDL?"):

        #print ("addAnnotatedSequence %s" % seqID)
        ### TranscriptSequence
        trseqnode = self.dom.createElement('TranscriptSequence')
        trseqnode.setAttribute('id',seqID)
        trseqnode.setAttribute('transcriptsource',source)
        trseqnode.setAttribute('video',video)
        trseqnode.setAttribute('edl',edl)
        self.trdatanode.appendChild(trseqnode)

        ### Annotations
        annode = self.dom.createElement('Annotations')
        trseqnode.appendChild(annode)

        ### sequence data (text data and points in time)
        seqdatanode = self.dom.createElement('SequenceData')
        trseqnode.appendChild(seqdatanode)


        ### sort the speaker intervals into a list for each speaker
        #speakers = defaultdict(list)

        for iid,startTS,startIdx,stopTS,stopIdx,data,subseq in aseq:
            if data==None:
                print ("Warning: Unrecognised IntervalType --no-data--")
                #raise InputError()
            else:
                if data['IntervalType'] == 'STROKE':
                    intervalnode = self.dom.createElement('Stroke')
                    intervalnode.setAttribute('fingersNtools',data['fingers'])
                    if 'holdstart' in data:
                        intervalnode.setAttribute('holdstart', data['holdstart'])
                    if 'holdstop' in data:
                        intervalnode.setAttribute('holdstop', data['holdstop'])
                    if 'hold' in data:
                        intervalnode.setAttribute('hold', data['hold'])
                    if 'spatialElementID' in data:
                        intervalnode.setAttribute('spatial_element_id', data['spatialElementID'])
                    if 'comment' in data:
                        intervalnode.setAttribute('comment', data['comment'])


                elif data['IntervalType'] == 'PHRASE':
                    intervalnode = self.dom.createElement('Phrase')
                    if data['startblau']:
                        intervalnode.setAttribute('blaupunktstart','1')
                    else:
                        intervalnode.setAttribute('blaupunktstart','0')
                    if data['stopblau']:
                        intervalnode.setAttribute('blaupunktstop','1')
                    else:
                        intervalnode.setAttribute('blaupunktstop','0')

                elif data['IntervalType'] == 'SPEAKER':
                    intervalnode = self.dom.createElement('Speaker')
                    intervalnode.setAttribute('speaker',data['Speaker'])
                    #speakers[ data['Speaker'] ].append((startTS,stopTS))
                elif data['IntervalType'] == 'SECTION':
                    intervalnode = self.dom.createElement('Section')
                elif data['IntervalType'] == 'FORMAT':
                    intervalnode = self.dom.createElement('Format')
                    intervalnode.setAttribute('format',data['Format'])
                else:
                    print ("Warning: Unrecognised IntervalType %s" % data['IntervalType'])

            intervalnode.setAttribute('id',iid)
            intervalnode.setAttribute('startTS',startTS)
            intervalnode.setAttribute('stopTS',stopTS)

            annode.appendChild(intervalnode)

        ### Speaker Information
        #speakerinfonode = self.dom.createElement('SpeakerInformation')
        #annode.appendChild(speakerinfonode)
        #for speaker in speakers:
        #   speaknode = self.dom.createElement('SpeakerInformation')
        #   speakerinfonode.appendChild(speaknode)
        #   for interv in speaker:
        #       intervalnode = self.dom.createElement('Phrase')
        #       speaknode

            ######## should not be required in the XML
            ###      PIT tags do the job of indexing text positions
            ###intervalnode.setAttribute('startIDX',startIDX)
            ###intervalnode.setAttribute('stopIDX',stopIDX)

        for startTS,startIdx,stopTS,stopIdx,seq in aseq.iterSegments(pointKey = keyPremiereTSoffset):
            pitnode = self.dom.createElement('PointInTime')
            pitnode.setAttribute('timestamp',startTS)
            seqdatanode.appendChild(pitnode)

            textdata = seq
            textsegment = self.dom.createTextNode(self.text2xml(textdata))
            seqdatanode.appendChild(textsegment)

        pitnode = self.dom.createElement('PointInTime')
        pitnode.setAttribute('timestamp',stopTS)
        seqdatanode.appendChild(pitnode)


    def getTranscriptSequnce(self,sequenceID,inpoint=None,outpoint=None,interval=None):
        trseqnode = self.trseqnodes[sequenceID]
        ### annotation data (intervals for speaker, section, stroke, phrase)
        annode = trseqnode.getElementsByTagName('Annotations')[0]
        ### sequence data (text data and points in time)
        seqdatanode = trseqnode.getElementsByTagName('SequenceData')[0]
        
        #sourceInfo = trseqnode.getAttribute('informal_source_info')
        
        ### identify in and outpoint
        if interval:
            if inpoint or outpoint:
                raise InputError("you may specify *either* an episode OR inpoint and outpoint -- not both.")
            node = annode.firstChild
            found = False
            while node:
                if node.nodeType == node.ELEMENT_NODE:
                    intervalID, inpoint, outpoint = node.getAttribute('id'), node.getAttribute('startTS'), node.getAttribute('stopTS')
                    if intervalID == interval:
                        found = True
                        break
                node = node.nextSibling

            if not found:
                raise InputError("Did not find an interval %s" % interval)

        ### fetch the first node (according to inpoint timestamp)
        if inpoint:
            found = False
            for node in seqdatanode.getElementsByTagName('PointInTime'):
                if node.getAttribute('timestamp') == inpoint:
                    found = True
                    break
            if not found:
                raise InputError("Did not find a timestamp %s in the sequence %s" % (inpoint,sequnceID))
        else:
            node = seqdatanode.firstChild

        aseq = AnnotatedSequence("")
        while node:
            #print ((node,node.nodeType))
            if node.nodeType == node.TEXT_NODE:
                #print "appending text: %s" % node.data
                textdata = node.data
                textdata = textdata.strip()
                logging.debug("getTranscriptSequence:TEXTNODE:%s:TEXTNODE" % textdata)
                if len(textdata) > 0:
                    aseq.append(node.data)
                else:
                    logging.debug("...dropping Textnode")

            elif node.nodeType == node.ELEMENT_NODE:
                pit = node.getAttribute('timestamp')
                logging.debug("getTranscriptSequence:ELEMENTNODE:%s" % pit)
                logging.info("getTranscriptSequences: append PIT to sequence: %s" % pit)
                aseq.appendPIT(pit)

                if node.getAttribute('timestamp') == outpoint:
                    break
            else:
                raise InputError("Unrecognised node type. %s" % node.nodeType)
            node = node.nextSibling

        ### annotations (intervals)
        logging.info("getTranscriptSequnce:processing Annotations...")
        node = annode.firstChild
        while node:
            if node.nodeType == node.ELEMENT_NODE:
                logging.debug("processing element Node <%s . . .>" % node.tagName)
                intervalID, startTS, stopTS = node.getAttribute('id'), node.getAttribute('startTS'), node.getAttribute('stopTS')
                if node.tagName == 'Phrase':
                    if aseq.existsTimestamp(startTS) and aseq.existsTimestamp(stopTS):
                        data = {'IntervalType':'PHRASE'}
                        data['startblau'] = node.getAttribute('blaupunktstart') == '1'
                        data['stopblau'] = node.getAttribute('blaupunktstop') == '1'
                        aseq.defineInterval(startTS,stopTS,iid=intervalID,data=data)
                elif node.tagName == 'Stroke':
                    if aseq.existsTimestamp(startTS) and aseq.existsTimestamp(stopTS):
                        data = {'IntervalType':'STROKE'}
                        data['fingers'] = node.getAttribute('fingersNtools')
                        hold = node.getAttribute('holdstart')
                        if hold:
                            data['holdstart'] = hold
                        hold = node.getAttribute('holdstop')
                        if hold:
                            data['holdstop'] = hold
                        hold = node.getAttribute('hold')
                        if hold:
                            data['hold'] = hold
                        aseq.defineInterval(startTS,stopTS,iid=intervalID,data=data)

                        comment = node.getAttribute('comment')
                        if comment:
                            data['comment'] = comment

                        spatialElementID = node.getAttribute('spatial_element_id')
                        if spatialElementID:
                            data['spatialElementID'] = spatialElementID

                elif node.tagName == 'Speaker':
                    intervalID, startTS, stopTS = node.getAttribute('id'), node.getAttribute('startTS'), node.getAttribute('stopTS')
                    if aseq.existsTimestamp(startTS) and aseq.existsTimestamp(stopTS):
                        data = {'IntervalType':'SPEAKER'}
                        data['Speaker'] = node.getAttribute('speaker')
                        aseq.defineInterval(startTS,stopTS,iid=intervalID,data=data)
                elif node.tagName == 'Format':
                    intervalID, startTS, stopTS = node.getAttribute('id'), node.getAttribute('startTS'), node.getAttribute('stopTS')
                    if aseq.existsTimestamp(startTS) and aseq.existsTimestamp(stopTS):
                        data = {'IntervalType':'FORMAT'}
                        data['Format'] = node.getAttribute('format')
                        aseq.defineInterval(startTS,stopTS,iid=intervalID,data=data)

                elif node.tagName == 'Section':
                    intervalID, startTS, stopTS = node.getAttribute('id'), node.getAttribute('startTS'), node.getAttribute('stopTS')
                    if aseq.existsTimestamp(startTS) and aseq.existsTimestamp(stopTS):
                        data = {'IntervalType':'SECTION'}
                        aseq.defineInterval(startTS,stopTS,iid=intervalID,data=data)
                else:
                    raise InputError("Unrecognised tag %s." % node.tagName)
            node = node.nextSibling
        return aseq


    def readXMLfile(self,filename):
        f = open(filename,'r')
        self.dom = xml.parse(f)
        f.close()

        docinfo = self.dom.documentElement.getElementsByTagName("DocumentInformation")[0]
        if self.transcriptversion != docinfo.getAttribute("transcriptversion"):
            raise InputError("TranscriptVersions do not match.")

        self.trdatanode = self.dom.documentElement.getElementsByTagName("TranscriptData")[0]

        self.trseqnodes = {}
        for trseqnode in self.trdatanode.getElementsByTagName('TranscriptSequence'):
            sequenceID = trseqnode.getAttribute('id')
            self.trseqnodes[sequenceID] = trseqnode

    def writeXMLfile(self,filename,addindent='',newl=''):
        f = open(filename,'w')
        s = self.dom.toprettyxml(indent=addindent,newl=newl,encoding='utf-8')
        #print repr(s)
        #print type(s)
        #self.dom.writexml(f,addindent=addindent,newl=newl,encoding='utf-8')
        f.write(s)
        f.close()
