#!/usr/bin/env python 

import inkex, simplepath, simplestyle, simplepath
from Woz_AnnotatedTranscriptXML import *
import os
import random
import math
from logging import info

from logging import info
import logging

#import numpy

LOG_FILENAME = 'Woz_ContextualizerA.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)



#corpus_fname = 'C:\Programme\Inkscape\share\extensions\minicorpus.xml'
#corpus_fname = 'C:\Programme\Inkscape\WozardCorpus\Korpus_V205-bereinigenDerAnnotationen-D.xml'
#corpus_fname = 'C:\Programme\Inkscape\WozardCorpus\TextCorpus_current.xml'
corpus_fname = 'C:\Dokumente und Einstellungen\wozard\Eigene Dateien\MultimodalCorpus\VerbalData\VerbalCorpus-BlockA.xml'

def getPathLocation(node):
	p = simplepath.parsePath(node.get('d'))
	for cmd,params in p:
		if cmd == 'M':
			return params[-2],params[-1]
	

class WContextualizer(inkex.Effect):
	def __init__(self):
	
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("-c", "--contextsizepre", action="store", type="string", dest="contextsizepre", default="150", help="Prefix")
		self.OptionParser.add_option("-C", "--contextsizesucc", action="store", type="string", dest="contextsizesucc", default="150", help="Prefix")
		self.OptionParser.add_option("-s", "--textsizefactor", action="store", type="string", dest="textsizefactor", default="5", help="Prefix")
		self.OptionParser.add_option("-w", "--boxwidth", action="store", type="string", dest="boxwidth", default="200", help="Prefix")
		self.OptionParser.add_option("-f", "--spacefactor", action="store", type="string", dest="spacefactor", default="1.0", help="Prefix")
		self.OptionParser.add_option("-I", "--increase_main", action="store", type="string", dest="incstrokemain", default="0", help="Prefix")
		self.OptionParser.add_option("-i", "--increase_sub1", action="store", type="string", dest="incstrokesub1", default="0", help="Prefix")
		self.OptionParser.add_option("-e", "--context_elements", action="store", type="string", dest="contextelements", default="0", help="Prefix")
		self.OptionParser.add_option("-d", "--kill_duplicates", action="store", type="string", dest="killduplicates", default="0", help="Prefix")
		self.OptionParser.add_option("-l", "--layout", action="store", type="string", dest="layout", default="0", help="Prefix")
		
		self.taken = [(0,0,500,500)]
		self.nextPosXY = (-100,100) 
		self.angle = 0.0
		self.elementIdx = {}

		
	def effect(self):
		# index to kill duplicate paragraphs
		self.placedParagraphs = set([])
	
		# # # Parameter # # #
		contextsizepre = int(self.options.contextsizepre.strip('"').replace('\$','$'))
		contextsizesucc = int(self.options.contextsizesucc.strip('"').replace('\$','$'))
		self.textsizefactor = float(self.options.textsizefactor.strip('"').replace('\$','$'))
		self.boxwidth = int(self.options.boxwidth.strip('"').replace('\$','$'))
		self.spacefactor = float(self.options.spacefactor.strip('"').replace('\$','$'))
		self.incStrokeMain = float(self.options.incstrokemain.strip('"').replace('\$','$')) 
		self.incStrokeSub1 = float(self.options.incstrokesub1.strip('"').replace('\$','$')) 
		self.handleContextElements = self.options.contextelements.strip('"').replace('\$','$')
		self.killduplicates = self.options.killduplicates.strip('"').replace('\$','$')
		self.layout = self.options.layout.strip('"').replace('\$','$')
		
		svg = self.document.getroot()
		
		self.makeElementIdx(svg)
		
		# or alternatively
		# svg = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]

		# Again, there are two ways to get the attibutes:
		width  = inkex.unittouu(svg.get('width'))
		height = inkex.unittouu(svg.attrib['height'])

		layer = inkex.etree.SubElement(svg, 'g')
		layer.set(inkex.addNS('label', 'inkscape'), 'Contextualizer Output')
		layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
		
		# # # CORPUS # # #
		#corpus_fname = 'minicorpus.xml'
		corpus = CorpusDocument(corpus_fname)
		
		for id, node in self.selected.iteritems():
			info ("going through selection: %s" % id)
			spl = id.split('_')
			xml_id = "%s_%s" % ( spl[0] , spl[1] )
			
			# # # reduce the id to the essential first two bits (VPxx_yy_ArrowsNStuff -> VP
			#id = id.replace('_SArrow','')
			#id = id.replace('_DArrow','')

			
			ref_acts = corpus.getRefActs(xml_id)

			if ref_acts == None:
				#raise Exception('retrieved no reference acts for spatial element. id/xmlid: %s/%s' % (id,xml_id))

				tmpstyle = simplestyle.parseStyle(node.get('style'))
				tmpstyle['stroke-dasharray'] = '6,3,1.5,3'
				node.set('style',simplestyle.formatStyle(tmpstyle))

			else:						
				info("effect(): retrieved RefActs: %s" % str(ref_acts))
				
				# # # retrieve the contexts for each reference act
				contexts = map( lambda x : corpus.getContext(x,contextsizepre,contextsizesucc) , ref_acts)
				
				# # # place the context boxes arount the referred diagrammatic element 
				info ("getting position of node id: %s" % id)
				try:
					x,y = getPathLocation(node)
				except TypeError:
					raise Exception("Element %s contains no valid path data to retrieve position." % id)
				
				self.addContexts(layer,xml_id,x,y,contexts,self.boxwidth)
				
	
	def getBoxHeight(self,width,len):
		#charwidth=10
		charheight=12.5
		#return (len*charwidth/width)*charheight
		return int(1+len*self.textsizefactor/width) * charheight
			
	def addContexts(self,parent,pathID,pathX,pathY,contexts,width=50,height=40,direction='vertical'):
		""" visualizes all given text contexts of a path identified by its ID. The position of the text boxes is determined based on former boxes."""
		xoffset,yoffset = 100,100
		
		
		if self.layout == 'offset':
			x,y = pathX + xoffset, pathY + yoffset
		elif self.layout == 'circle':
			x,y = self.getNextPosition()
		elif self.layout == 'coveredArea:X':
			x,y = pathX, pathY

		else:
			raise ValueError("unrecocnized layout option" % self.layout)
			
		xx,yy = x,y 
				
		elementsInContext = []
		for con in contexts:			
			parID = con.ref.par

			if self.killduplicates != 'yes' or (not parID in self.placedParagraphs):
				self.placedParagraphs.add(parID)
				contextboxID = self.uniqueId("CON_%s_%s" % (pathID,parID))
				contextbox = inkex.etree.SubElement(parent,'g',id=contextboxID)
				
				#info (u"context %s has references %s" % (con.__str__(),text))
				text = u"%s [-%s-] %s" % (con.preAsString(),con.refElementID(),con.succAsString())
				height = self.getBoxHeight(self.boxwidth,len(text))
				
				stribewidth = 10
				
				if self.layout == 'coveredArea:X':
					## modify the X-coordinate xx such that it reflects the area covered by the graphic elements referred in the context.
					refs = con.getRefsInContext()
					referredElements = map ( lambda x : ("%s_%s" % (pathID.split('_')[0],x)), refs )

					referredXCoords = [x]
					referredYCoords = [y]
					for el in set(referredElements):
						#info ("blubb:" + el)
						# # str converts from unicode string to standard string
						try:
							elNode = self.elementIdx[str(el)]
							info("[%s]: %s %s" % (str(pathID),str(el),str(elNode))   )
							elX,elY = getPathLocation(elNode)
							referredXCoords.append(elX)
							referredYCoords.append(elY)
						except KeyError:
							elX,elY = 0,0
							self.addText(parent,elX,elY,"NOT FOUND: "+str(el),size=12)
					xx = -500 + self.spacefactor * math.sqrt( (max(referredXCoords)-min(referredXCoords))**2 + (max(referredYCoords)-min(referredYCoords))**2 )
					
				flowtextbox = self.addFlowTextBox(contextbox,xx,yy,width,height,text,extraWidth=stribewidth)
				flowtextboxID = flowtextbox.get('id')

				# # # paragraph ID in the 'blue stribe'
				s = 'opacity:0.5;fill:#3344ff;fill-opacity:1;stroke:#000000;stroke-width:0;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'
				bluestribe = inkex.etree.SubElement(contextbox,'rect',x=str(xx+width),y=str(yy),width=str(stribewidth),height=str(height),style=s)

				tx,ty= xx+width+stribewidth , yy+height-10		# die soll-koordinaten f. den text -- frag mich einer nach der mathe aber irgendwie klappts so
				# wegen transformation bekommt addText die koordinaten x=-ty und y = tx. Die matrix macht den rest wieder gut. wirklich!
				self.addText(contextbox,-ty,tx,parID,size=stribewidth+1,transform='matrix(0,-1,1,0,0,0)')
				
				# the id of the element and its thick box
				s = "opacity:1;fill:#ffffff;fill-opacity:1;stroke:#000000;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1"
				boxX = xx+width-100
				box = inkex.etree.SubElement(contextbox,'rect',x=str(boxX),y=str(yy+height-2),width=str(120),height=str(15),style=s)
				box.set('id',self.uniqueId('pathIDBox'))
				#self.addText(contextbox,xx+55,yy+height+10,pathID,size=12)
				self.addText(contextbox,boxX+5,yy+height+10,pathID,size=12)
				
				# # # connections # # #
				ctrx,ctry = xx+0.5*width, yy+0.5*height
				self.addConnection(parent,pathX,pathY,ctrx,ctry,contype='main',end=('#'+contextboxID))

				# # # increase stroke width in the 'pivot' element
				pivotNode = self.elementIdx[con.refElementID()]
				tmpstyle = simplestyle.parseStyle(pivotNode.get('style'))
				tmpsw = float(tmpstyle['stroke-width'])
				tmpsw += self.incStrokeMain
				tmpstyle['stroke-width'] = str(tmpsw)
				pivotNode.set('style',simplestyle.formatStyle(tmpstyle))
				
				if self.handleContextElements == 'yes':
					# # handle the spatial elements referred to in the context
					refs = con.getRefsInContext()
					referredElements = map ( lambda x : ("%s_%s" % (pathID.split('_')[0],x)), refs )

					for el in set(referredElements):
						#info ("blubb:" + el)
						# # str converts from unicode string to standard string
						try:
							elNode = self.elementIdx[str(el)]
							info("[%s]: %s %s" % (str(pathID),str(el),str(elNode))   )
							elX,elY = getPathLocation(elNode)
							tmpstyle = simplestyle.parseStyle(elNode.get('style'))
							tmpsw = float(tmpstyle['stroke-width'])
							tmpsw += self.incStrokeSub1
							tmpstyle['stroke-width'] = str(tmpsw)
							elNode.set('style',simplestyle.formatStyle(tmpstyle))

						except KeyError:
							elX,elY = 0,0
							self.addText(parent,elX,elY,"NOT FOUND: "+str(el),size=12)
							#raise Exception("par %s refers to diagram el %s, which was not found!" % (str(parID),str(el)))
						
						self.addConnection(parent,elX,elY,ctrx,ctry,contype='sub1',end=('#'+contextboxID))
				# # next position for next context but same element
				if self.layout != 'coveredArea:X':
					yy += height +10

	def addFlowTextBox(self,node,x,y,w,h,text,extraWidth=0,extraHeight=0):
		
		group = inkex.etree.SubElement(node,'g')
		group.set('id',self.uniqueId('theGroup'))
		
		s = 'opacity:1;fill:#ffffff;fill-opacity:0.8;stroke:#000000;stroke-width:1;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'
		rect = inkex.etree.SubElement(group,'rect',x=str(x),y=str(y),width=str(w+extraWidth),height=str(h+extraHeight),style=s)
		s = 'font-size:10px;font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;text-align:start;line-height:125%;writing-mode:lr-tb;text-anchor:start;fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;font-family:Arial;-inkscape-font-specification:Arial'
		froot = inkex.etree.SubElement(group,'flowRoot',style=s)
		froot.set('xml:space','preserve')
		fregion = inkex.etree.SubElement(froot,'flowRegion')
		#s = 'opacity:1;fill:#ffffff;fill-opacity:0.80232562;stroke:#FF0000;stroke-width:1;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'
		inkex.etree.SubElement(fregion,'rect',x=str(x),y=str(y),width=str(w),height=str(h))
		inkex.etree.SubElement(froot,'flowPara').text = text
		return group
		
		#rect.set('x',str(x)).set('y',str(y)).set('height',str(h)).set('width',str(w)).set('id','theRect')
		#rect.set('style','opacity:1;fill:#ffffff;fill-opacity:0.8;stroke:#000000;stroke-width:1;stroke-miterlimit:4;stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1')

	def getNextPosition(self):
		#return (random.randint(-200,700),random.randint(-200,700))
		x = math.sin(self.angle) * 1000 
		y = math.cos(self.angle) * 1000
		self.angle += 0.036 * math.pi
		info("(%f,%f,%f)" % (x,y,self.angle))
		return (int (x),int(y))


		
	def addConnection(self,parent,x1,y1,x2,y2,contype='main',start=None,end=None):
		"""
	    <path
         style="fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1"
         d="M 150.5,57.27694 L 228.42994,29.927295"
         id="path4819"
         inkscape:connector-type="polyline" inkscape:connection-start="#rect4638" inkscape:connection-end="#lalala" />
		"""
		if contype == 'main':
			s = "fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:2px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;marker-start:url(#DotM);marker-end:url(#DotM)"
		elif contype == 'sub1':
			s = "fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:2;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;stroke-miterlimit:4;stroke-dasharray:2, 2;stroke-dashoffset:0"
		dd = "M %s,%s L %s,%s" % (str(x1),str(y1),str(x2),str(y2))
		n = inkex.etree.SubElement(parent,'path',style=s,d=dd)
		n.set('inkscape:connector-type','polyline')
		if start != None: n.set('inkscape:connection-start',start)
		if end   != None: n.set('inkscape:connection-end',end)		
                
	def addText(self,node,x,y,text,size=10,transform=None):
		new = inkex.etree.SubElement(node,inkex.addNS('text','svg'))
		s = {'font-size': ('%d' % size), 'fill-opacity': '1.0', 'stroke': 'none',
			'font-weight': 'normal', 'font-style': 'normal', 'fill': '#000000'}
		new.set('style', simplestyle.formatStyle(s))
		new.set('x', str(x))
		new.set('y', str(y))
		if transform!=None:
			new.set('transform',transform)
		new.text = str(text)

		
	def makeElementIdx(self,svgelement):
		elid = svgelement.get('id')
		info("makeElementIdx(%s,%s)" % (str(svgelement),str(elid)))
		#info ("element ID:%s" % str(elid))
		#only take those elements which actually carry relevant IDs that is 'VP...'
		
		
		if elid != None and elid[:2] == 'VP':
			elidsplit = elid.split('_')
			elid = "%s_%s" % (elidsplit[0],elidsplit[1])
			self.elementIdx[elid] = svgelement
			info ("adding %s to element index" % str(svgelement))
		for el in svgelement:
			self.makeElementIdx(el)

e = WContextualizer()
e.affect()

