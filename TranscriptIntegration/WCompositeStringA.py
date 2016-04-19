import copy


#######################################
# # # it does not work like this ! ! !
# # # it does not work like this ! ! !
# # # it does not work like this ! ! !
#######################################
#class CompositeRE(object):
#	def __init__(self,lnames,patterns,flags=0):
#		if len(layers) != len(patterns):
#			raise ValueError('number of layers does not match number of patterns')
#			
#		self.lnames = lnames
#		self.patterns = {}
#		for ln,p in zip(lnames,patterns):
#			self.layers[ln] = re.compile(p,flags)
#	
#	def matchByMainSub(self,cstr,mainlayer):
#		matches = []
#		for ln in self.lnames:
#			if ln in cstr.layers:
#				m = self.patterns[ln].match(cstr.layers[ln])
#				if m:
#					matches.append(m)
#				else:
#					return None
#			else:
#				return None
#			
#		return CompositeMatch(self.lnames,matches)
#		
#class CompositeMatch(object):
#	def __init__(self,lnames,matches):
#		self.lnames = lnames
#		self.matches = {}
#		for ln,m in zip(lnames,matches):
#			self.layers[ln] = m			

class CompositeString(object):
	def __init__(self, lnames, texts):
		#self.printIn , self.printOut = None,None
		self.setPrintRegion()	### printIn/Out will be set to None, which means the whole sequence will be printed
	
		#print "XXX %s %s" % (lnames,texts)
		self.printlinelen = 150
		
		### check consistency of argument values
		if len(lnames) != len(texts):
			raise ValueError("number of layer names does not match number of texts (%s,%s)" % (lnames,texts))
		if len(texts) > 0:
			l = len(texts[0])
			for t in texts[1:] :
				if len(t) != l:
					raise ValueError("lenghts of text layers do not match")
		else:
			l = 0
		
		self.length = l
		self.layernames = lnames
		self.layers = {}

		for ln,t in zip(lnames,texts):
			self.layers[ln] = t
			
	def getEmptyCopy(self):
		r = CompositeString([],[])
		for ln in self.layernames:
			x = self.layers[ln]
			r.addLayer(ln)	
		return r

			
	def getLayer(self,lname):
		return self.layers[lname]
			
			 		
	def addLayer(self, lname, text=None ):
		if text == None:
			text = ' ' * self.length
		#print (self.layernames)
		#print (self.length)
		#print len(text)
		
		if self.layernames == []:
			## the string has no layer yet
			self.layers[lname] = text
			self.layernames.append(lname)
			self.length = len(text)
		else:	
			## there are already other layers
			## check the length of the new layer text
			if  len(text) != self.length:
				raise(ValueError('string length differs from composite lenght'))
			self.layers[lname] = text
			self.layernames.append(lname)
	
	def substituteText(self,lname,text,pos):
		if pos + len(text) > self.length:
			raise ValueError("substitute text too long")
		self.layers[lname] = self.layers[lname][:pos] + text + self.layers[lname][pos+len(text):] 

	def appendTexts (self,texts):
		l1 = None
		for ln,t in zip(self.layernames,texts):
			self.layers[ln] += t
			if l1 != None and l1 != len(t):
				raise ValueError("lenghts of text layers do not match (b)")
			l1 = len(t)
			self.length = len(self.layers[ln])
			
			  
		
#	def __repr__(self):
#		s = "<CompositeString object>"
#		return s[:-1] + ('  [length=%d]' % self.length)
		
	def setPrintRegion(self,a=None,b=None):		
		self.printIn,self.printOut = a,b
		
	def __str__(self):
		if self.printIn == None:
			self.printIn = 0
		if self.printOut == None:
			self.printOut = self.length
	
	
		s = "LAYERS: " + str(self.layernames) + '\n'
		#print (int(self.length/self.printlinelen))
		for i in range (int(self.printIn/self.printlinelen),int(self.printOut/self.printlinelen)+1):
			a,b = int(i*self.printlinelen) , int((i*self.printlinelen)+self.printlinelen)
			s = s + "[%d .. %d]\n" % (a,b)
			for l in self.layernames:
				s = s + self.layers[l][a:b] + '\n'
			#s = s + '\n'
			
		self.setPrintRegion()
		return s[:-1] + ('  [length=%d]' % self.length)
	
	def __len__(self):
		return self.length
		
	def __getitem__(self, key):
		r = CompositeString([],[])
		for ln in self.layernames:
			x = self.layers[ln]
			i = x.__getitem__(key)
			r.addLayer(ln, i)	
		return r

#	def __setitem__(self, key, value):
#		for ln in value.layernames:
#			self.layers[ln].__setitem__(key,value.layers[ln])

	def __add__(self, value):
		if value.layernames != self.layernames:
			raise ValueError ("incompatible layers: %s / %s" % (value.layernames,self.layernames))
			
 		r = CompositeString([],[])
		for ln in self.layernames:
			r.addLayer(ln,self.layers[ln] + value.layers[ln])

		r.length = self.length + len(value) 
		
		return r
	
	def __iadd__(self, value):
		if value.layernames != self.layernames:
			raise ValueError ("incompatible layers: %s / %s" % (value.layernames,self.layernames))
			
 		#r = CompositeString([],[])
		for ln in self.layernames:
			self.layers[ln] += value.layers[ln]
			
		self.length += len(value) 
		
		return self
			
	
	def __mul__(self,n):			
 		r = CompositeString([],[])
		for ln in self.layernames:
			r.addLayer(ln,self.layers[ln] * n)
		
		r.length = self.length * n 

		return self

	def __imul__(self,n):			
 		for ln in self.layernames:
			self.layers[ln] *= n
		
		self.length *= n
		
		return self	

#def __concat__()
	

		

def demo():	
	#c = CompositeString("abcdefghijABCDEFGHIJ1234567890!?!!4&/()=xxxxxxxxxxiiiiiiiiiiwwwwwwwwwweeeeeeeeX")
	c = CompositeString(['BASIS'],["12345678"])
	c.addLayer("TEXT","abcdefgh")
	
	a = CompositeString(['BASIS','TEXT'],['xx','yy'])
	
	print (str(c))
	print (str(c[2]))
	print (str(c[1:4]))
	print (str(c[:-4]))
	print (str(c[1::2]))
	
	#c[1:3] = a
	print (str(a))
	print (str(a+c))
	
	print (str(a*3))
	
	a *= 3
	
	print str(a)
	
# demo()
