#!/usr/bin/env python 
'''
Copyright (C) 2005 Aaron Spike, aaron@ekips.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''
import inkex, simplepath, simplestyle, simplepath
from Woz_AnnotatedTranscriptXML import *

class IDPrefixer(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.OptionParser.add_option("-f", "--find", action="store", type="string", dest="findtxt", default="", help="")
		self.OptionParser.add_option("-r", "--replace", action="store", type="string", dest="replacetxt", default="", help="")
			
	def effect(self):
		replaceFlag = False
		findtxt = self.options.findtxt.strip('"').replace('\$','$')
		replacetxt = self.options.replacetxt.strip('"').replace('\$','$')
		if findtxt != "": 	replaceFlag = True

		## make an output layer
		svg = self.document.getroot()
		layer = inkex.etree.SubElement(svg, 'g')
		layer.set(inkex.addNS('label', 'inkscape'), 'Element ID Labels')
		layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
		
		
		for id, node in self.selected.iteritems():
			#self.group = inkex.etree.SubElement(node.getparent(),inkex.addNS('g','svg'))

			#a =[]
			p = simplepath.parsePath(node.get('d'))
			#num = 1
			for cmd,params in p:
				if cmd == 'M':
					text = str(id)
					if replaceFlag:	text = text.replace(findtxt,replacetxt)
					self.addText(layer,params[-2]+3,params[-1]+3,text)
		
                
	def addText(self,node,x,y,text):
		new = inkex.etree.SubElement(node,inkex.addNS('text','svg'))
		s = {'font-size': '10', 'fill-opacity': '1.0', 'stroke': 'none',
			'font-weight': 'normal', 'font-style': 'normal', 'fill': '#000000'}
		new.set('style', simplestyle.formatStyle(s))
		new.set('x', str(x))
		new.set('y', str(y))
		new.text = str(text)
                    
e = IDPrefixer()
e.affect()
