#!/usr/bin/env python2.3
#
#  xml-sandkasten01.py
#  
#
#  Created by martinb on 27.12.09.
#  Copyright (c) 2009 __MyCompanyName__. All rights reserved.
#

from xml.dom.minidom import *

from WDataHandlingA import WListCatalog,WSetCatalog
#from WotilitiesA import unique
import re

from logging import info



class ReferenceAction(object):
	"""Stores all data related to one occurrance of a spatial reference (deixis/drawing stroke) within the transcript"""
	def __init__(self,spatialElementID,paragraphID,refType,repeat,externalMedium,xmlNode):
		#print "__init__"
		self.id = spatialElementID		### global id of the referred spatial element
		self.par = paragraphID			### numeric id of the enclosing paragraph
		self.refType = refType			### 'gesture' or 'draw'
		self.repeat = repeat			### repeat status: 
											#	0:firsOccurrence,correctly coded; 
											#	1:repatedOccurrence,correctly coded;
											#	2:firsOccurrence,incorrectly coded;
											#	3: vergessen :-)
											#	4:repatedOccurrence,incorrectly coded;
		self.extMed = externalMedium	### id of the last 'externalmedium' tag in the xml corpus
		self.node = xmlNode				### dom.xml node object representing the tag (<draw id= ...> </draw>)
		
	def __str__(self):
		return "%s,%05d:%s,%s,%s" % (self.id,self.par,self.refType,self.repeat,self.extMed)
	

class Context(object):
	def __init__(self,ref_act,preContext,succContext):
		self.ref = ref_act
		self.pre = preContext
		self.succ = succContext
		
	def getRefsInContext(self):
		"""get all reference acts to other diagrammatic elements in the context. the 'pivot' element, the context of which it is, is NOT included."""
		result = []
		# pars things of the form [IDm akl fjas ] .*? matches everything in a non-greedy fasion
		r = re.compile(u'\[(?P<elementID>.*?)\]')
		for m in r.finditer(self.preAsString()+self.succAsString()):
			ref=m.group(u'elementID')
			info (u"getRefsInContext(): found ref: elementID=%s" % ref)
			result.append(ref)
		
		return result
	
	def refElementID(self):
		return self.ref.id
		
	def refPar(self):
		return self.ref.par
	
	def preAsString(self):
		return reduce ( lambda x,y:x+y , self.pre, "")
	
	def succAsString(self):
		return reduce ( lambda x,y:x+y , self.succ, "")
	
	def __str__(self):
		return u"CONTEXT: PRE:%s REF:%s SUCC:%s" % (self.preAsString(),self.ref.id,self.succAsString())
		
		


class CorpusDocument(object):
	def __init__(self,filename):
		self.spatialElementCat = WListCatalog()		# for each spatial element a list gives all occurrences
		self.currExtMed = ""
	
		#print "Processing corpus: " + filename
		
		dom = parse(filename)
		self.dom = dom
		self.handleCorpus(dom.getElementsByTagName("annotatedtranscript")[0])
		pass
		
	selectNode = (lambda (node,repeat,elType,extmed) : node)
		
	def handleCorpus(self,corpusroot):
		#print ("Processing %s" % corpusroot)
		interviews = corpusroot.getElementsByTagName("interview")
		for interview in interviews:
			self.handleInterview(interview)
	
	def handleInterview(self, interview):
		id,vpnr,nickname = interview.getAttribute('id') , interview.getAttribute('vpnr') , interview.getAttribute('nickname')
		#print ("processing Interview: %s,%s,%s   %s" % (id,vpnr,nickname,interview))
		
		for par in interview.getElementsByTagName("paragraph"):
			self.handleParagraph(par,vpnr,nickname)
		
	def handleParagraph(self,paragraph,vpnr,nickname):
		par_id,informer,speaker = int(paragraph.getAttribute('id')),paragraph.getAttribute('informer'),paragraph.getAttribute('speaker')
		#print ("PAR: %d, %s %s " % (par_id,informer,speaker))
				
		if speaker == 'informer':
			node = paragraph.firstChild
			#print node
			while node != None:
				try:
					if node.tagName == 'externalmedium':	
						self.currExtMed = node.getAttribute('id')
					elif node.tagName == 'gesture' or node.tagName == 'draw':
						#print node.tagName
						refType,elID,repeat = node.tagName , node.getAttribute('id') , int(node.getAttribute('repeat')) 
						spatialElementID = "VP%02d_%s" % (int(vpnr),elID)
						#x = (spatialElementID,par_id,refType,repeat,self.currExtMed,node)
						#print x
						reference_action = ReferenceAction(spatialElementID,par_id,refType,repeat,self.currExtMed,node)
						#print "blubb %s" % reference_action
						#print ("adding %s,%s" % (spatialElementID,reference_action) )
						self.spatialElementCat.add(spatialElementID,reference_action)
				except(AttributeError):
					pass
				node = node.nextSibling
		
	def testIntegrity(self):
		for id,occurs in self.spatialElementCat.iteritems():
			repeatseq = map((lambda (node,repeat,elType,extmed) : str(repeat)),occurs)
			#print (repeatseq)
			repeatstr = reduce( lambda x,y : x+y ,repeatseq)
			#print ("%10s: %s" % (id,repeatstr))
			
	def getRefActs(self,ID):
		""" for a given spatial element all occurring reference acts in the transcripts are retrieved and returned in a list of RefAct objects."""
		result = self.spatialElementCat.getElementsByKey(ID)
		info("CorpusDocument.getRefActs(%s): return %s" % (ID,result))
		return self.spatialElementCat.getElementsByKey(ID)
		
	def getContext(self,ref_act,preLen,succLen):
		result = Context(ref_act,self.getContextPre(ref_act.node,preLen),self.getContextSucc(ref_act.node,succLen))
		return result
	
	def getContextPre(self,node,maxLen=20,maxRefNum=65760):
		""" Retrieves the context of a draw/gesture node. 
			Context means the preceeding text node as well as all draw/gesture nodes enclosed by the text node and 'node'.
			maxLen:		number of text characters retrieved at maximum.
			maxRefNum:	number of spatial references retrieved at maximum."""			
		info("CorpusDocument.getContextPre(%s,...):" % node)
		result = []
		a = node.previousSibling		
		countC = 0
		countR = 0
		while a != None and countC < maxLen and countR < maxRefNum:
			try:
				if a.tagName == 'gesture' or a.tagName == 'draw':
					result.append("[%s]" % a.getAttribute('id'))
					countR += 1
			except(AttributeError):
				pass
			if a.nodeType == node.TEXT_NODE:
				#result.append((a,a.data))
				text = a.data[-(maxLen-countC):]	# truncate text to the remaining available space
				result.append(text)
				countC += len(text)
			a = a.previousSibling
		result.reverse()
		info("... returning %s" % result)
		return result

	def getContextSucc(self,node,maxLen=20,maxRefNum=65760):
		""" Retrieves the context of a draw/gesture node. 
			Context means the succeeding text node as well as all draw/gesture nodes enclosed by the text node and 'node'.
			maxLen:		number of text characters retrieved at maximum.
			maxRefNum:	number of spatial references retrieved at maximum."""			
		info("CorpusDocument.getContextSucc(%s,...):" % node)
		result = []
		a = node.nextSibling		
		countC = 0
		countR = 0
		while a != None and countC < maxLen and countR < maxRefNum:
			try:
				if a.tagName == 'gesture' or a.tagName == 'draw':
					result.append("[%s]" % a.getAttribute('id'))
					countR += 1
			except(AttributeError):
				pass
			if a.nodeType == node.TEXT_NODE:
				#result.append((a,a.data))
				text = a.data[:maxLen-countC]	# truncate text to the remaining available space
				result.append(text)
				countC += len(text)
			a = a.nextSibling
		info("... returning %s" % result)
		return result

	
	def getAllParagraphs (self):
		allParagraphs = []
		for paragraph in self.dom.getElementsByTagName("paragraph"):
			par_id,informer,speaker = int(paragraph.getAttribute('id')),paragraph.getAttribute('informer'),paragraph.getAttribute('speaker')
			if speaker == 'informer':
				parAsText = u""
				a = paragraph.firstChild
				while a != None:
					try:
						if a.tagName == 'gesture' or a.tagName == 'draw':
							parAsText = parAsText + ("[%s]" % a.getAttribute('id'))
					except(AttributeError):
						pass
						
					if a.nodeType == a.TEXT_NODE:
						parAsText = parAsText + a.data
					
					a = a.nextSibling
				p = Paragraph(par_id,parAsText)
				allParagraphs.append(p)
		return allParagraphs

		
class Paragraph(object):
	def __init__(self,parID ='99431', parText = 'kashd askjf asdfk [12] kdjsfh askjh [14] asjkhdfkadsh[16]'):
		self.parText = parText
		self.parID = parID
		self.refs = []
		
		# pars things of the form [IDm akl fjas ] .*? matches everything in a non-greedy fasion
		r = re.compile(u'\[(?P<elementID>.*?)\]')
		for m in r.finditer(self.parText):
			ref=m.group(u'elementID')
			#info (u"getRefsInContext(): found ref: elementID=%s" % ref)
			self.refs.append(ref)

	def asCVS(self):
		result = ""
		result = result + ('"PAR","%s","%s";\n' % (str(self.parID),self.parText))
		for r in self.refs:
			result = result + ('"REF","%s","%s";\n' % (str(self.parID),r))
		return result
	
		

### QUASI MAIN ###
#corpus_fname = 'minicorpus.xml'
#corpus_fname = 'Korpus_V205-bereinigenDerAnnotationen.xml'
#a = CorpusDocument(corpus_fname)
#print a.spatialElementCat
#for spatrefid,occurrences in a.spatialElementCat.iteritems():
#	print spatrefid
#	for occ in occurrences:
#		#print occ
#		print ("%s : %s" % (spatrefid, a.getContextSucc(occ.node)))


