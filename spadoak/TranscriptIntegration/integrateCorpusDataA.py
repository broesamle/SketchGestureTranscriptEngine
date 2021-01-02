
### activate logging
LOG_FILENAME = 'integrateCorpusDataA.log'

f = open(LOG_FILENAME,'w')
f.close()

import logging
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

logging.debug("- --------------------------------------BEGIN LOG XXXX")

print ("activated logging" + LOG_FILENAME)

### general packages
from sys import argv
import re
import copy
from pyx import *
import pyx
#from math import pi
import os
import time


### my general library
from WCompositeStringA import CompositeString
from WTimelineA import IntervalTimeline, AnnotatedSequence, TS_INPOINT, TS_OUTPOINT, BY_INDEX, BY_TIMESTAMP, keyElanTS, keyPremiereTS, keyPremiereTSoffset
from WTextServicesB import WRegexpTranslator
from WFileAnalyzer import LogFileLight,LogParser


### project modules
#from Visualizer import
from CorpusXML import XMLCorpusDocument
#from StrokesSVG import SVGDocument



##########################################
### DEFINE CONTENT TO PROCESS
### structure and format
##########################################

### for the recoding of speakers there has to be a one char alias for each speaker
### these have to be unique within each input RTF file
### informer labels + one character abbreviations

speakerLabelsNChars = {		'Interviewer:':'x',
							'JoNo:':'a',
							'PeRu:':'b',
							'Os:':'c',
							'PeFe:':'d',
							'LoAl:':'e',
							'FrMi:':'f',
							'MiHoCo:':'g',
							'KaSt:':'h',
							'De:':'i'}


### for simply doing the reverse mapping use this							
#speakerCharsNLabels = {}
#for label,ch in speakerLabelsNChars.iteritems():
#	speakerCharsNLabels[ch] = label

### for encoding speakers nice and pretty you can put new labels

speakerCharsNLabels = {		'x':'R',
							'a':'JoNo',
							'b':'PeRu',
							'c':'Os',
							'd':'PeFe',
							'e':'LoAl',
							'f':'FrMi',
							'g':'MiHoCo',
							'h':'KaSt',
							'i':'De'}
							
							
edlPath = "VideoProjekte-PRPRJ+EDL/"
### RTF input
rtfPath = "TranscripsRTF/"
rtfList = []
rtfList += ['[FrMi-all]FrMi_M2U00128MM1.rtf','[JoNo-all]JoNo_M2U00124MM_DK_16_11_2010.rtf']
rtfList += ['[De-all]De_StrokeAnnos_DK_03_11_2010.rtf']
rtfList += ['legendeA.rtf']
rtfList += ['[Os-all]Os_M2U00120+121MM.rtf']
rtfList += ['[PeFe-all]PeFe_M2U00122_DK_17_11_2010.rtf']
rtfList += ['[PeRu-all]PeRu_M2U00117+118MM_strokes_DK_02_11_2010.rtf']


XMLfname = "VerbalData/block1.xml"

#protocolFname = 'protocol.txt'

protocolFname = XMLfname+'.protocol.txt'
protocolfile = open(protocolFname,'w')

s = "Script for Integrating annotated RTF Transcripts and EDL Timestamp data into XML"
protocolfile.write(s+'\n')
print s

rtfFiles = ""
for x in rtfList[:-1]:
	rtfFiles += x+', '
rtfFiles += rtfList[-1]

date = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
s = "%s\nRTF path: %s\nRTF files: %s\nEDL path: %s\nXML output:%s" % (date,rtfPath,rtfFiles,edlPath,XMLfname)
protocolfile.write(s+'\n')
print s


##########################################
### Doing the work
##########################################


### FUNCTIONS ###
### FUNCTIONS ###
### FUNCTIONS ###

def markerIfy(s):
	r = str(s).replace(':','L')
	r = r.replace('.','k')
	return 'MRK'+r

specialCharsReplacer = WRegexpTranslator()
### from RTF to something intermediate
specialCharsReplacer.addReplacer(r"[\n\r]+", r"")
specialCharsReplacer.addReplacer(r"\\\{", r"#Open;")
specialCharsReplacer.addReplacer(r"\\\}", r"#Close;")
specialCharsReplacer.addReplacer(r"\\par", r"#Par;")
specialCharsReplacer.addReplacer(r"\\lquote", r"#quote;")
specialCharsReplacer.addReplacer(r"\\rquote", r"#quote;")
specialCharsReplacer.addReplacer(r"\\tab", r" ")

def recodeSpecialChars(s):
	return specialCharsReplacer.translate(s)


xmlIfyReplacer = WRegexpTranslator()
xmlIfyReplacer.addReplacer(r"#Open;", r"\{")
xmlIfyReplacer.addReplacer(r"#Close;", r"\}")
xmlIfyReplacer.addReplacer(r"#Par; #Par;",r"---")
xmlIfyReplacer.addReplacer(r"#Par;",r"---")
xmlIfyReplacer.addReplacer(r"\\endash",r"--")
xmlIfyReplacer.addReplacer(r"\\rquote",r"'")
xmlIfyReplacer.addReplacer(r"\\lquote",r"'")
xmlIfyReplacer.addReplacer(r"\\tab",r"'")
xmlIfyReplacer.addReplacer(r"#quote;",r"'")
#xmlIfyReplacer.addReplacer(r"\^",r" ")
#xmlIfyReplacer.addReplacer(r"#quote;",r"'")

def XMLify(s):
	return xmlIfyReplacer.translate(s)

def differenceTS(premiere,elan):
	logging.debug("COMPARE: %s ~= %s" % (premiere,elan))

	frames1 = keyPremiereTS(premiere)
	frames2 = keyElanTS(elan)

	logging.debug("DIFFERS: %f" % (frames1 - frames2) )
	return frames1 - frames2


###########################################
### recode speaker information layer into intervals
###########################################




### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###
### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###
### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###### MAIN ###
	

########################################################################################################################
### create XML corpus
########################################################################################################################

xmlcorpus = XMLCorpusDocument(text2xml=XMLify)

xmlcorpus.initNewDocument()


for RTFfname in rtfList:
	RTFfname = os.path.join(rtfPath,RTFfname)
	inf = open(RTFfname,'r')
	rtfcontent = inf.read()
	inf.close()

	try:
		preamble,content = rtfcontent.split('BEGIN-TRANSCRIPT',1)
	except ValueError:
		raise ValueError("No BEGIN-TRANSCRIPT tag detected")

	try:
		content,postamble = content.split('END-TRANSCRIPT',1)
	except ValueError:
		raise ValueError("No END-TRANSCRIPT tag detected")

	
	print "fetching meta info from rtf file..." 

	m = re.search("(TRANSCRIPTFILE:(?P<data>.*?):TRANSCRIPTFILE)", preamble)	
	if m == None:	print ("No TRANSCRIPTFILE section found in %s." % RTFfname)
	sourceInfo = m.groupdict()['data']

	m = re.search("(SEQUENCE-ID:(?P<data>.*?):SEQUENCE-ID)", preamble)
	if m == None:	print ("No SEQUENCE-ID section found in %s." % RTFfname)
	transcriptSeqID = m.groupdict()['data']

### SVG not required in this step
#	m = re.search("(SVG:(?P<data>.*?):SVG)", preamble)	
#	if m == None:	print ("No SVG section found in %s." % RTFfname)
#	SVGfname = m.groupdict()['data']

	m = re.search("(VIDEO:(?P<data>.*?):VIDEO)", preamble)
	if m == None:	print ("No VIDEO section found in %s." % RTFfname)
	VIDEOreference = m.groupdict()['data']

	m = re.search("(EDL:(?P<data>.*?):EDL)", preamble)	
	if m == None:	print ("No EDL section found in %s." % RTFfname)
	EDLfname = m.groupdict()['data']

	
### SVG not required in this step
	#print ("Processing %s:\n    %s\n    %s\n    %s" % (RTFfname,EDLfname,SVGfname,VIDEOreference))

	print ("Processing %s:\n    %s\n" % (RTFfname,EDLfname))

	protocolfile.write("Source (RTF):%s\n" % RTFfname )
	protocolfile.write("MetaData:\n    TRA:%s\n    SEQ:%s\n    VID:%s    EDL:%s\n" %
		(sourceInfo,transcriptSeqID,VIDEOreference,EDLfname) )
	


	#pdfoutfname="out.pdf"

	formatCharsNLabels = {}
	formatLabelsNChars  = {}
	formatCharsNLabels['X'] = 'STRIKE'
	formatCharsNLabels['R'] = 'RED+YELLOW'
	formatCharsNLabels['r'] = 'RED'
	formatCharsNLabels['y'] = 'YELLOW'
	formatCharsNLabels['#'] = 'KILLER'
	formatCharsNLabels[' '] = 'NORMAL'
	for ch,label in formatCharsNLabels.iteritems():
		formatLabelsNChars[label] = ch
		

	
	content = recodeSpecialChars(content)
	cc = CompositeString(['text','color'],['',''])

	#pat = re.compile(r"\{((:\\\w+\s*)+)([^\}*])\}",re.I)
	pat = re.compile(r"\{\s*((?:\\\w+\s?)+)(.*?)\}",re.I)

	for m in pat.finditer(content):
		format,text = m.groups()

#		print "format:%s" % format
#		print "text:%s" % text


		fo = ''
		if format.find(r'\strike') >= 0:
			#print 'XXX'
			fo = 'X'
		elif format.find(r'\cf6') >= 0: 
			if format.find(r'\highlight7') >= 0:
				fo= 'R'
			else:
				fo= 'r'
		else:
			if format.find(r'\highlight7') >= 0:
				fo='y'
			else:
				fo=' '
#		print "fo:%s" % fo
		cc.appendTexts( [ text, fo*len(text) ] )
	

	###########################################
	### extract and recode speaker information
	###########################################
	cc.addLayer('speaker')
	cc2 = CompositeString(['text','color','speaker'],['','',''])

	## pat = re.compile(r"(Interviewer:)|(JoNo:)|(\[Crosstalk\])\w*",re.IGNORECASE)

	patstr = "SECTION:"
	for label,char in speakerLabelsNChars.iteritems():
		patstr += "|(%s)" % label

	###patstr = patstr[:-1]  ## remove final '|' from the string
	
	pat = re.compile(patstr,re.IGNORECASE)

		# Crosstalk should be addressed later as single point events 

	m = pat.search(cc.layers['text'])
	speaker = '-'
	while m != None:
		mtext = cc.layers['text'][m.start():m.end()]
		#print "MT:%s" % mtext
		if mtext != 'SECTION:':
			### adding the speaker characters in the speaker layer of the composite string
			cc.substituteText( 'speaker', speaker*m.start(), 0)		### put the speaker info before the match
			cc2 += cc[:m.start()]					### move the stuff before the match to cc2
			cc = cc[m.end():] 						#   ...
			speaker = speakerLabelsNChars[mtext]	### fetch the new speaker character	(which will be put)
		else:
			cc.substituteText( 'speaker', speaker*m.start(), 0)		### put the speaker info before the match
			cc2 += cc[:m.end()]						### move the stuff before and in the match to cc2
			cc = cc[m.end():]
			#speaker = speakerLabelsNChars[mtext]	### fetch the new speaker character	(which will be put)
			speaker = ';'
		m = pat.search(cc.layers['text'])		### find the next match

	#logging.debug("cc: \n" + str(cc))

	cc.substituteText( 'speaker', speaker*len(cc), 0)
	cc = cc2 + cc

	logging.debug("- --------------------------------------Content after speaker marking: \n" + str(cc))


	###########################################
	### Get Time Info from EDL
	###########################################

	print "EDL processing..."

	parser = LogParser()

	### no phrase event -- a clip on audio track 1 means that there is currently no phrase (and no stroke)
	### the start of this will be the stop of the last phrase and the stop of this will be the start of the next phrase
	###              316   AX   A   C                  00: 07: 44: 14                  00: 07: 46: 04                       00: 07: 44: 14                      00: 07: 46: 04
	r = re.compile(r'\d+\s+AX\s+A\s+C\s+(?P<clipStart>\d+:\d+:\d+:\d+)\s+(?P<clipStop>\d+:\d+:\d+:\d+)\s+(?P<timelineStart>\d+:\d+:\d+:\d+)\s+(?P<timelineStop>\d+:\d+:\d+:\d+)')
	parser.addLineParserRE(r,'noPhrase')

	### a clip on audiotrack 3 (marked as 'NONE' in the EDL) is a stroke
	r = re.compile(r'\d+\s+AX\s+NONE\s+C\s+(?P<clipStart>\d+:\d+:\d+:\d+)\s+(?P<clipStop>\d+:\d+:\d+:\d+)\s+(?P<timelineStart>\d+:\d+:\d+:\d+)\s+(?P<timelineStop>\d+:\d+:\d+:\d+)')
	parser.addLineParserRE(r,'Stroke')

	## blaupunkt in EDL:
	#008  AX       V     C        01:00:00:00 01:00:00:01 00:02:23:05 00:02:23:06
	#REEL AX IS CLIP Farbflche

	r = re.compile(r'\d+\s+AX\s+V\s+C\s+(?P<clipStart>\d+:\d+:\d+:\d+)\s+(?P<clipStop>\d+:\d+:\d+:\d+)\s+(?P<timelineStart>\d+:\d+:\d+:\d+)\s+(?P<timelineStop>\d+:\d+:\d+:\d+)')
	parser.addLineParserRE(r,'Blaupunkt')


	EDLfname = os.path.join(edlPath,EDLfname)
	edlfile = LogFileLight(EDLfname,parser)
	
	#print edlfile.getAllEvents()
	
	phrasesNstrokes = []
	nextPhraseStart = None
	lastPhraseStart = None
	lastPhraseStop = None
	currentstrokes = []
	edlcounter = []
	blaupunkte = set([])
	for event in edlfile.getAllEvents():
		if event['eventtype'] == 'noPhrase':
			lastPhraseStop = event['timelineStart']
			nextPhraseStart = event['timelineStop']
			if lastPhraseStart:			### if there is an earlier noPhrase event, then we can complete a phrase
				phrasesNstrokes.append((lastPhraseStart,lastPhraseStop,currentstrokes))
				edlcounter.append(len(currentstrokes))
			currentstrokes = []
			lastPhraseStart = nextPhraseStart
		elif event['eventtype'] == 'Stroke':
			currentstrokes.append((event['timelineStart'],event['timelineStop']))
		elif event['eventtype'] == 'Blaupunkt':
			blaupunkte.add(event['timelineStart'])


	msg = "detected %d phrases with \n%s\n strokes respectively." % (len(edlcounter),edlcounter)
	print msg
	protocolfile.write(msg+'\n')
	
	
	###########################################
	### create an AnnotatedSequence instance and 
	### recode phrases into intervals
	###########################################
	print "Doing the phrases business..."
	logging.info("- --------------------------------------Processing phrases into an annotated sequence...")


	#pat = re.compile(r"\[(?P<startTS>\d\d:\d\d:\d?\.\d*)(.*?)(?P<stopTS>\d\d:\d\d:\d?\.\d*)\]")
	pat = re.compile(r"\[(?P<startTS>\d+:\d+:\d*\.?\d*)(?P<phrase>.*?)(?P<stopTS>\d+:\d+:\d*\.?\d*)\]")

	aseq = AnnotatedSequence(cc.getEmptyCopy())	## make an empty annotated sequence with the same layers

	phrasesNstrokesRest = phrasesNstrokes
	strokesByPhraseID = {}

	logging.debug("integrateCorpusData:phrasesNstrokes " + str(phrasesNstrokes))

	m = pat.search(cc.layers['text'])
	counter = 0
	nonmatchingTimestamps = {}

	while m != None:
		startTS = m.groupdict()['startTS']
		stopTS = m.groupdict()['stopTS']
		counter += 1
		msg = "Detected phrase %d in the transcript: %s..%s" % (counter,startTS,stopTS)
		print msg
		protocolfile.write(msg+'\n')
		
		if len(phrasesNstrokesRest) == 0:
			msg = "!! running out of phrase data in the EDL"
			print msg
			protocolfile.write(msg+'\n')
			break

		startTS_premiere,stopTS_premiere,strokes = phrasesNstrokesRest[0]

		diff = differenceTS(startTS_premiere,startTS)
		if abs(diff) > 12.0:
			msg = "!! PREMIERE/EDL timestamps differ: %s  %s d=%f" % (startTS_premiere,startTS,diff)
			print (msg)
			protocolfile.write(msg+'\n')
			nonmatchingTimestamps[startTS] = (startTS,startTS_premiere,diff)
			nonmatchingTimestamps[startTS_premiere] = (startTS,startTS_premiere,diff)

		diff = differenceTS(stopTS_premiere,stopTS)
		if abs(diff) > 12.0:
			msg = "!! PREMIERE/EDL timestamps differ: %s  %s d=%f" % (stopTS_premiere,stopTS,diff)
			print (msg)
			protocolfile.write(msg+'\n')
			nonmatchingTimestamps[stopTS] = (stopTS,stopTS_premiere,diff)
			nonmatchingTimestamps[stopTS_premiere] =  (stopTS,stopTS_premiere,diff)

		##          length of [xx:yy:zz.fff
		phrase = cc[ (m.start()+len(startTS)+1) : (m.end()-(len(stopTS)+1)) ]

		logging.debug("integrateCorpusData:recoding phrases: %s/%s,%s/%s %s" % (startTS,startTS_premiere,stopTS,stopTS_premiere,m.groupdict()['phrase']))
		logging.debug("Phrase: %s,%s: %s" % (startTS,stopTS,phrase))

		#startIdx = offset + m.start()		## the index of the phrase start
		#stopIdx = offset + m.start() + len(phrase)		## index of the phrase stop

		aseq.append(cc[:m.start()])						## move the stuff before the match from cc to aseq
		phrasedata = {'IntervalType':'PHRASE'}
		phrasedata['startblau'] = startTS_premiere in blaupunkte
		phrasedata['stopblau'] = stopTS_premiere in blaupunkte
		iid = aseq.appendAsInterval(startTS_premiere,stopTS_premiere,phrase,data=phrasedata)	## append the phrase as interval

		#print ("appended interval: %s" % iid)
		### this dictionary collects strokes info sorted by interval id for the
		### respective enclosing phrase interval. it will be used for
		### strokes recoding and control of stroke numbers in each phrase
		strokesByPhraseID[iid] = strokes
	
		cc = cc[m.end():]
		
		m = pat.search(cc.layers['text'])
		phrasesNstrokesRest = phrasesNstrokesRest[1:]
	
#	logging.debug("- --------------------------------------Content after phrases processing: \n" + str(aseq))
	logging.debug("- --------------------------------------Content after phrases processing:")
	for startTS,startIdx,stopTS,stopIdx,subseq in aseq.iterSegments(pointKey=keyPremiereTSoffset):
		logging.debug("segment: [%s/%d]%s[%s/%d]" % (startTS,startIdx,subseq.layers['text'],stopTS,stopIdx))

	#s += "Sequence:" + str(self.seq[self.printIn:self.printOut])
		
	#s += "[%s/%d]\n" % (stopTS,stopIdx)


	###########################################
	### get section offsets
	###########################################
	#print "xxxx",aseq.seq.layers['text']
	pat = re.compile(r"SECTION:(?P<section>\w+):SECTION")
	sections = [ (m.start(),m.groupdict()['section']) for m in pat.finditer(aseq.seq.layers['text']) ]

	#print "SSSSSSSS:%s" % sections
	###########################################
	### recode strokes into intervals
	###########################################
	print "Doing the strokes business"
	logging.info("- --------------------------------------Strokes processing . . .")

	##							  #Open;                 shielded<           path               path2957-7   ,              e                      >#Close;
	##                            #Open;                         <              g                g2953       ,             7e                      >#Close;
	##				              #Open;            o            <           path                path2841    ,              e ;                3D  >#Close;
	pat = re.compile(r"(?P<prefix>#Open;)(?P<text>.*?)(?P<suffix><(\s*(?P<tagname>\w+)\s+)?(?P<gestureID>[\w-]+),(?P<fingers>[\w-]*)[;,]?(?P<supplement>[\s\w\.\#+-]*)>#Close;)")

	#print "Sections:", sections
	
	currSectIdx,currSectID = sections[0]
	sections = sections[1:]
	nextSectIdx,nextSectID = sections[0]
	#print ("A THIS:%d/%s NEXT:%d/%s" % (currSectIdx,currSectID,nextSectIdx,nextSectID))
	for iid,startTS,startIdx,stopTS,stopIdx,data,subseq in aseq:
		#print "START:%d" % startIdx
		#print ("B THIS:%d/%s NEXT:%d/%s" % (currSectIdx,currSectID,nextSectIdx,nextSectID))
		if startIdx >= nextSectIdx:
			currSectIdx,currSectID = nextSectIdx,nextSectID 
			print iid,startIdx,stopIdx,currSectIdx,currSectID
			if len(sections) > 0:
				nextSectIdx,nextSectID = sections[0]
			sections = sections[1:]
			
			#print ("RRRRRRRRRRRRRRRRRRRRRRRRRRRRR %d %s" % (currSectIdx,currSectID))
		#print ("C THIS:%d/%s NEXT:%d/%s" % (currSectIdx,currSectID,nextSectIdx,nextSectID))

		
		msg = "PHRASE %s: %s/%d..%s/%d DATA:%s\n    %s" % (iid,startTS,startIdx,stopTS,stopIdx,data,subseq.layers['text'])
		print (msg)
		protocolfile.write('\n'+msg+'\n')
		msg = ""
		if startTS in nonmatchingTimestamps:
			msg += "!!  Start Timestamp difference: %s ~ %s (DIFF: %f)\n" % nonmatchingTimestamps[startTS]
		if stopTS in nonmatchingTimestamps:
			msg += "!!  Stop  Timestamp difference: %s ~ %s (DIFF: %f)" % nonmatchingTimestamps[stopTS]
		if msg != "":
			print (msg)
			protocolfile.write(msg+'\n')



		if data['IntervalType'] == 'PHRASE':
			strokes = strokesByPhraseID[iid]
			msg = "    number of strokes: %d" % len(strokes)
			protocolfile.write(msg + '\n')
			print msg
			
			###print subseq.layers['text']
			m = pat.search(subseq.layers['text'])
			#print m
			### running through all strokes in this phrase
			
			while m != None:
				if len(strokes) <= 0:
					msg = "!!  more strokes in transcript than in EDL: %s: %s..%s" % (iid,startTS,stopTS)
					protocolfile.write(msg+'\n')
					print msg
					break
					#raise ValueError(msg)

				logging.debug( "Match for Stroke" + str(m.groupdict()) )
				prefix = m.groupdict()['prefix']
				text = m.groupdict()['text']
				suffix = m.groupdict()['suffix']
				gID = m.groupdict()['gestureID']
				fingers = m.groupdict()['fingers']
				supplement = m.groupdict()['supplement']

			## start and stop index of the stroke (in the final sequence)
				a = m.start() + startIdx
				b = m.end() + startIdx
				
				## overwrite prefix and suffix with 'killer character'
				## this keaps the length (and all the indexes) for the moment
				## later the killer character passages can be removed
				aseq.seq.substituteText('speaker','@'*len(prefix),a)
				aseq.seq.substituteText('speaker','@'*len(suffix),a+len(text)+len(prefix))

				strokedata = {'IntervalType':'STROKE'}
				strokedata['fingers'] = fingers
				strokestartTS,strokestopTS = strokes[0]
				#print supplement
				supplement = supplement.replace('H+','++')
				supplement = supplement.replace('H-','--')
				supplement = supplement.replace('H.','..')
				#print "XXXXXXXXXX:%s" % supplement
				supplement = supplement.replace('3D','>>')
				
				m2 = re.search(r'\+\+(?P<holdstart>[\w]+)',supplement)
#				print m2
				if m2:
					holdstartfingers = m2.groupdict()['holdstart']
#					print "    holdstart:%s" % holdstartfingers
#					print strokedata
#					print holdstartfingers
					strokedata['holdstart'] = holdstartfingers


				m2 = re.search(r'--(?P<holdstop>[\w-]+)',supplement)
				if m2:
					holdstopfingers = m2.groupdict()['holdstop']
#					print "    holdstop:%s" % holdstopfingers
					strokedata['holdstop'] = holdstopfingers

				m2 = re.search(r'\.\.(?P<hold>[\w-]+)',supplement)
				if m2:
					holdfingers = m2.groupdict()['hold']
#					print "    holdstop:%s" % holdstopfingers
					strokedata['hold'] = holdfingers

				strokedata['comment'] = ""
				m2 = re.search(r'\>>',supplement)
				if m2:
					#holdfingers = m2.groupdict()['hold']
					#print "    3D *** 3D" 
					strokedata['comment'] += '3D.'

					### extract comments:
				#print "SUP:%s" % supplement
				m2 = re.search(r'\#(?P<comment>[\w\s-]+)',supplement)
				#print m2

				
				if m2:
					strokedata['comment'] += m2.groupdict()['comment']

				try:
					aseq.addInterval(strokestartTS, strokestopTS, uniqueID = (currSectID+':'+gID), data = strokedata, startIdx=a, stopIdx=b)
					msg = "    STROKE %s: %s/%d..%s/%d DATA:%s" % ((currSectID+':'+gID),strokestartTS,a,strokestopTS,b,strokedata)
					protocolfile.write(msg+'\n')
					print msg
					logging.debug(msg)

					#if 'holdstart' in strokedata and 'holdstop' in strokedata:
					#	msg = "!!  holdstart AND holdstop in the same stroke."
					#	protocolfile.write(msg+'\n')
					#	print msg

				except ValueError as v:
					#msg = "!!  catched ValueError" + str(v)
					#protocolfile.write(msg+'\n')
					#print msg
					newgID = gID + '-duplicate'
					msg = "!!  changed duplicate gesture ID: %s -->> %s" % (gID,newgID)
					protocolfile.write(msg+'\n')
					print msg
					msg = "    STROKE %s: %s/%d..%s/%d DATA:%s" % ((currSectID+':'+newgID),strokestartTS,a,strokestopTS,b,strokedata)
					protocolfile.write(msg+'\n')
					print msg
					logging.debug(msg)

				###print subseq.layers['text'][m.end():]
				m = pat.search(subseq.layers['text'],m.end())
				#print m
				strokes = strokes[1:]


			if len(strokes) != 0:
				msg = "!! Stroke data in EDL which was not correctly coded in transcript: %s: %s..%s -- %s" % (iid,startTS,stopTS,strokes)
				protocolfile.write(msg+'\n')
				print msg
				#raise ValueError(msg)
#		offset = b
#		m = pat.search(aseq.seq.layers['text'],offset)


	


	logging.debug("- --------------------------------------Content after strokes processing:")
	for startTS,startIdx,stopTS,stopIdx,subseq in aseq.iterSegments(pointKey=keyPremiereTSoffset):
		logging.debug("segment: [%s/%d]%s[%s/%d]" % (startTS,startIdx,subseq.layers['text'],stopTS,stopIdx))
		
	
	#aseq.addInterval("00:00:00:00","99:59:59:24",uniqueID="WholeSequence",startIdx=0,stopIdx=len(aseq.seq))



	###########################################
	### remove killer character marked passages
	###########################################
	matches = []

	for m in re.finditer('@+', aseq.seq.layers['speaker']):
		matches.append(m)

	matches.reverse()

	for m in matches:
		a = m.start()
		b = m.end()
		logging.debug("to be removed: %d,%d: %s" % (a,b,aseq.seq.layers['speaker'][a:b]))

		### make interpolated timestamps based on given timestamps and sequence position (index)
		aseq.removePartSeq(a,b)


	###########################################
	### Speakers information
	###########################################

	for ch,slabel in speakerCharsNLabels.iteritems():
		print "process speaker intervals for: " + ch
		logging.info("- ----------- process speaker intervals for: %s (%s)" % (ch,slabel))

		pat = re.compile(ch+'+')


		for m in pat.finditer(aseq.seq.layers['speaker']):
			a = m.start()
			b = m.end()
			logging.debug("speaker info match: %d,%d" % (a,b))


			### make interpolated timestamps based on given timestamps and sequence position (index)
			startTS = aseq.getTSforIdx(a,'LOW')		### high/low tries to include/intersect other intervals
													### (expecting that speaker intervals are larger than strokes etc)
			stopTS = aseq.getTSforIdx(b,'HIGH')		### not sure if it works...


			aseq.addInterval(startTS, stopTS, data = {'IntervalType':'SPEAKER','Speaker':speakerCharsNLabels[ch]}, startIdx=a, stopIdx=b)

			pat = re.compile(ch+'+')

	###########################################
	### Format information
	###########################################

	#print aseq.seq.layers['color']
	#logging.debug("---------------CONTENT BEFORE FORMAT PROCESSING\n%s" % str(aseq))
	for ch,label in formatCharsNLabels.iteritems():
		if ch not in [ formatLabelsNChars['NORMAL'],formatLabelsNChars['KILLER'] ]:
			print "process format intervals for: " + ch
			logging.info("- ----------- process format intervals for: %s (%s)" % (ch,label))

			pat = re.compile(ch+'+')

	
			for m in pat.finditer(aseq.seq.layers['color']):
				a = m.start()
				b = m.end()
				logging.debug("format match: %d,%d" % (a,b))
				logging.debug("text:%s" % aseq.seq.layers['text'][a:b])

				
				### make interpolated timestamps based on given timestamps and sequence position (index)
				startTS = aseq.getTSforIdx(a,'HIGH')		### high/low tries to exclude/non-intersect other intervals
															### (expecting that format intervals are smaller than strokes etc)
				stopTS = aseq.getTSforIdx(b,'LOW')			### not sure if it works...

				aseq.addInterval(startTS, stopTS, data = {'IntervalType':'FORMAT','Format':label}, startIdx=a, stopIdx=b)
		
				pat = re.compile(ch+'+')
		
	logging.debug("---------------CONTENT AFTER FORMAT PROCESSING\n%s" % str(aseq))

	###########################################
	### Sections
	###########################################
	sections = []
	                  #SECTION:          intro :SECTION
	pat = re.compile(r"SECTION:(?P<section>\w+):SECTION")
	for m in pat.finditer(aseq.seq.layers['text']):
		a = m.start()				
		b = m.end()
		logging.debug("section tag match: %d,%d" % (a,b))
		#print ("section tag match: %d,%d" % (a,b))
		sectionname = m.groupdict()['section']
		logging.debug("section name: %s" % sectionname)
		
		#aseq.layers['speaker'].(a,b)	
		### make interpolated timestamps based on given timestamps and sequence position (index)
		#aseq.removePartSeq(a,b)
		### mark with a killer character passage
		aseq.seq.substituteText('speaker','#'*(b-a),a)
		
		sections.append((sectionname,a))

	if len(sections) > 0:
		name1,a = sections[0]
		sections = sections[1:]
		startTS = aseq.getTSforIdx(a)
		while len(sections) > 0:
			name2,b = sections[0]
			stopTS = aseq.getTSforIdx(b)

			sectdata={'IntervalType':'SECTION','SectionName':name1}
			sectID = name1
			aseq.addInterval(startTS, stopTS, startIdx=a, stopIdx=b,uniqueID=sectID,data=sectdata)
			msg = "SECTION %s: %s/%d..%s/%d DATA:%s" % (sectID,startTS,a,stopTS,b,sectdata)
			protocolfile.write(msg+'\n')
			
			name1,a = name2,b
			startTS = stopTS
			sections = sections[1:]
		### doing the last section
		b = len(aseq)
		stopTS = aseq.getTSforIdx(b)
		sectdata={'IntervalType':'SECTION','SectionName':name1}
		sectID = name1
		aseq.addInterval(startTS, stopTS, startIdx=a, stopIdx=b,uniqueID=sectID,data = sectdata)
		msg = "SECTION %s: %s/%d..%s/%d DATA:%s" % (sectID,startTS,a,stopTS,b,sectdata)
		protocolfile.write(msg+'\n')
	
	###########################################
	### remove killer character marked passages
	###########################################
	matches = []
	
	for m in re.finditer('#+', aseq.seq.layers['speaker']):
		matches.append(m)

	matches.reverse()
	
	for m in matches:
		a = m.start()
		b = m.end()
		logging.debug("to be removed: %d,%d: %s" % (a,b,aseq.seq.layers['speaker'][a:b]))
		
		### make interpolated timestamps based on given timestamps and sequence position (index)
		aseq.removePartSeq(a,b)	

	
	
#	for startTS,startIdx,stopTS,stopIdx,subseq in aseq.iterSegments(pointKey=keyPremiereTSoffset):
#		logging.debug("segment: [%s/%d]%s[%s/%d]" % (startTS,startIdx,subseq.layers['text'],stopTS,stopIdx))

	aseq.seq = aseq.seq.getLayer('text')
	xmlcorpus.addAnnotatedSequence(transcriptSeqID, aseq, source=sourceInfo, video=VIDEOreference, edl=EDLfname)

protocolfile.close()



########################################################################################################################
### write XML corpus
########################################################################################################################

xmlcorpus.writeXMLfile(XMLfname)
XMLfname = XMLfname.replace('.xml','.pretty.xml')
xmlcorpus.writeXMLfile(XMLfname,addindent="\t",newl="\n")





##################################################################################
#	##### This is the old piece of code that recoded strokes into intervals
#	##### it did flatten the hierarchy of phrasesNstrokes into a list of 
#	##### strokes and then matched and replaced stroke by stroke in the content.
#	##### this did not recognize the phrases structure around the strokes.
#	strokes = []
#	for ts,tss,strk in phrasesNstrokes:
#		strokes = strokes + strk
#		
#	m = pat.search(aseq.seq.layers['text'])
#	offset = 0
#	while m != None:
#		## move the stuff before the match from cc to aseq  	
#		logging.debug( "Match for Stroke" + str(m.groupdict()) )
#		prefix = m.groupdict()['prefix']
#		text = m.groupdict()['text']
#		suffix = m.groupdict()['suffix']
#		gID = m.groupdict()['gestureID']
#		fingers = m.groupdict()['fingers']
#		
#		
#		
#		## start and stop index of the stroke (in the final sequence)
#		a = m.start()				
#		b = m.start() + len(text)
#		## remove prefix and suffix
#		aseq.removePartSeq(a,a+len(prefix))
#		aseq.removePartSeq(b,b+len(suffix)) 
#		data = {'IntervalType':'STROKE'}
#		data['fingers'] = fingers
#		
#		startTS,stopTS = strokes[0] 
#		
#		aseq.addInterval(startTS, stopTS, uniqueID = gID, data = data, startIdx=a, stopIdx=b)
#	
#		logging.debug("Stroke: %s (%s,%d)-(%s,%d):" % (gID,startTS,a,stopTS,b))
#		#logging.debug("Stroke Sequence: (%s,%d)-(%s,%d): %s" % aseq.getIntervalSegment(gID))
#	                                                        # (startPID,startIdx,stopPID,stopIdx,seq)
#		
#		
#		offset = b
#		m = pat.search(aseq.seq.layers['text'],offset)
#		strokes = strokes[1:]
###################################################################################




