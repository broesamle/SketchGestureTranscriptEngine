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

import logging
from logging import info

LOG_FILENAME = 'Woz_Marker.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

class RangeMarker(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		
		self.OptionParser.add_option("-i", "--idsss", action="store", type="string", dest="idsss", default="???", help="Prefix")
		self.OptionParser.add_option("-s", "--style", action="store", type="string", dest="style", default="???", help="Prefix")
		self.OptionParser.add_option("-v", "--value", action="store", type="string", dest="value", default="??", help="Prefix")
		
#        self.OptionParser.add_option("-d", "--dotsize",
 #                       action="store", type="string", 
  #                      dest="dotsize", default="10px",
   #                     help="Sizes of the dots placed at path nodes")
    #    self.OptionParser.add_option("-f", "--fontsize",
     #                   action="store", type="string", 
      #                  dest="fontsize", default="20",
       #                 help="Size of node label numbers")    

	def effect(self):
		#ids = "123,231"
		#style = 'stroke'
		#value = 'blubb'

		ids = self.options.idsss.strip('"').replace('\$','$')
		style = self.options.style.strip('"').replace('\$','$')
		value = self.options.value.strip('"').replace('\$','$')
		
		svg = self.document.getroot()

		idlist = ids.split(',')
		for id in idlist:
			node = self.findByID(svg,id)
			if node == None:	
				raise(ValueError("did not find element: id=%s" % id))
			oldstyle = node.get('style')
			styledict = simplestyle.parseStyle(oldstyle)
			styledict[style] = value
			newstyle = simplestyle.formatStyle(styledict)
			node.set('style',newstyle)
			
		#		inkex.etree.subElement(node,'hhhh')
		#		raise Exception("found Element %s" % str(node))
		

	def findByID__ALTERNATIVE_NOT_TESTED(self,svgelement,id):
		info("findByID(%s,%s)" % (str(svgelement),str(id)))
		elid = svgelement.get('id')
		info ("element ID:%s" % str(elid))
		if elid == id:
			info ("returning %s" % str(svgelement))
			return (svgelement)
		else:
			for el in svgelement:
				result = self.findByID(el,id)
				if result != None:
					return result
			return None

	def findByID(self,svgelement,id):
		info("findByID(%s,%s)" % (str(svgelement),str(id)))
		elid = svgelement.get('id')
		info ("element ID:%s" % str(elid))
		if elid == id:
			info ("returning %s" % str(svgelement))
			return (svgelement)
		else:
			if svgelement:
				for el in svgelement:
					result = self.findByID(el,id)
					if result != None:
						return result
			else:
				return None

                
	def addText(self,node,x,y,text):
		new = inkex.etree.SubElement(node,inkex.addNS('text','svg'))
		s = {'font-size': self.options.fontsize, 'fill-opacity': '1.0', 'stroke': 'none',
			'font-weight': 'normal', 'font-style': 'normal', 'fill': '#000000'}
		new.set('style', simplestyle.formatStyle(s))
		new.set('x', str(x))
		new.set('y', str(y))
		new.text = str(text)
                    
e = RangeMarker()
e.affect()
