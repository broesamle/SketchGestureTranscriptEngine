	
#### ist noch nicht fertig !!!
class TypedTable:
	"""Handles Records of fixed number of elements"""
	def __init__():
		self.data = []
		self.types = []
		self.colIDs = {}
		self.nextID = 0
	
	def addColumn (name,t=None):
		"""Add a new column with a name and a type if given. The column is added behind (index-wise speaking) the last column in the table."""
		self.colIDs[name]=self.nextID
		self.types.append(t)
		self.nextID = self.nextID + 1
		
	def addLine(data):
		"""Add a sequence into the table. Each data item will be converted to the type of its target column, if a known type is given."""
		cdata=[]
		for t,d in zip(self.types,data):
			if t == IntType:		cdata.append(int(d))
			elif t == LongType:		cdata.append(long(d))
			elif t == BooleanType:	cdata.append(bool(d))
			elif t == FloatType:	cdata.append(float(d))
			elif t == StringType:	cdata.append(str(d))
			elif t == UnicodeType:	cdata.append(str(d).decode())
			else:		cdata.append(d)
			
	def __iter__():
		return self
		
	def next():
		pass
		

class WGenericCatalog(object):
	""" Organizes entries based on catalog keys in a dictionary. This is an abstract base class for catalogs. 
	Depending on how the entries are stored for each key, different subclasses (like WSetCatalog and WListCatalog) 
	may be derived. 
	Subclasses sould provide methods for managing the sections, while the management of the catalog is provided by
	WGenericCatalog. Technically, a dictionary is used to hold the catalog sections. Differend types of sequences can
	be used to organize the sections, that is the values of the dictionary"""
	
	def __init__(self):
		self.cat = {}
		self.tempOrder = []
	
	def existsKey(self,key):
		return key in self.cat

	def getElementsByKey(self,key):
		if self.existsKey(key):
			return self.cat[key]
		else:
			return None

	def add(self,key,element):
		"""Add an element to the catalog section identified by key."""
		if self.existsKey(key):
			self.addToSection(self.getElementsByKey(key),element)
		else:
			empty = self.makeEmptySection()
			self.addToSection(empty,element)
			self.cat[key] = empty
	
	def inByKeyElement(self,key,value):
		if value in self.getElementsByKey(key):
			return True
		else:
			return False

	def discardByKeyElement(self,key,element):
		if self.inByKeyElement(key,value):
			self.discardFromSection(getElementsByKey(key))

	def iteritems(self):
		return self.cat.iteritems()


	def __str__(self):
		print "__str__"
		s = ""
		for e in self.cat.iteritems():
			s += e.__repr__() + '\n'
		return s

class WListCatalog(WGenericCatalog):
	""" A Catalog where each section is organized as a list."""
	def makeEmptySection(self):
		return []
		
	def addToSection(self,section,element):
		section.append(element)

	def discardFromSection(self,section,element):
		try:
			section.remove(value)
		except(ValueError):
			pass

class WSetCatalog(WGenericCatalog):
	""" A Catalog where each section is organized as a set."""
	def makeEmptySection(self):
		return set([])
		
	def addToSection(self,section,element):
		section.add(element)

	def discardFromSection(self,section,element):
		section.discard(value)


### may be modified such that it implements a catalog	
class WeightedSymmetricGraph:
	def __init__(self,nodes):
		self.nodes = {}
		for n in nodes:
			if n not in self.nodes:
				self.nodes[n] = {}
			else:
				raise DataError, ('Node %s already in Graph.' % n)
				
		
	def hasNode(n):
		return n in self.nodes

	def checkPresence(self,n):
		if n not in self.nodes: 
			raise LookupError, ('Node %s not in Graph.' % n1)
			
	def connect(self,n1,n2,weight=1):
		self.checkPresence(n1)
		self.checkPresence(n2)
			
		self.nodes[n1][n2] = weight
		self.nodes[n2][n1] = weight
	
	def disconnect(self,n1,n2):
		self.checkPresence(n1)
		self.checkPresence(n2)
		try:
			del self.nodes[n1][n2]
			del self.nodes[n2][n1]
		except KeyError:
			pass

	def neighbours(self,n,minweight=None):
		result = []
		for k,i in self.nodes[n].iteritems():
			result.append((k,i))
			
		if minweight != None:
			result =  filter((lambda (k,i):i >= minweight), result)
		return result
		
	def __repr__(self):
		s = ""
		l = []
		for k,n in self.nodes.iteritems():
			l.append((k,n))
		l.sort()
		l2 = map(lambda(x,y):"%s:%s\n"%(repr(x),repr(y)),l)
		return reduce((lambda x,y:x+y),l2)
			

# print weighted graphs		
def printWG(self):
	s = ""
	l = []
	for k,n in self.nodes.iteritems():
		l.append((k,n))
	l.sort()
	l2 = map(lambda(x,y):"%s:%s\n"%(repr(x),repr(y)),l)
	return reduce((lambda x,y:x+y),l2)
		
	

class RouteNetwork:
    def __init__(self):
        self.node_ids = {}
        self.node_labels = []
        self.nodes = []
        self.conn = []
        self.stairs =[]
        
    def addNode(self,label,x,y,z=0):
        self.node_ids[label] = len(self.nodes)
        self.nodes.append((x,y,z))
        self.node_labels.append(label)

    def fixNodes(self):
        i = 0
        icon = []
        
        for i in self.nodes:
            iconn = []
            iconn2 = []
            for j in self.nodes:
                iconn.append(0)
                iconn2.append(0)
            self.conn.append(iconn)
            self.stairs.append(iconn2)

    def getPos(self, label):
        return self.nodes[self.node_ids[label]]

    def getXY(self, label):
        return self.getPos(label)[0:2]

    def getX(self, label):
        return self.getPos(label)[0]

    def getY(self, label):
        return self.getPos(label)[1]

    def getZ(self, label):
        return self.getPos(label)[2]

    def getAllXY(self):
        return map(lambda (x,y,z) : (x,y), self.nodes)

    def getAllXYLabel(self):
        return map(lambda ((x,y,z),label) : (x,y,label), zip(self.nodes,self.node_labels))

    def connectNodes(self, label1, label2):
        self.conn[self.node_ids[label1]][self.node_ids[label2]] = 1        
        self.conn[self.node_ids[label2]][self.node_ids[label1]] = 1

    def stairsBetweenNodes(self, label1, label2):       
        self.stairs[self.node_ids[label1]][self.node_ids[label2]] = 1        
        self.stairs[self.node_ids[label2]][self.node_ids[label1]] = 1
        
    def disconnectNodes(self, label1, label2):
        self.conn[self.node_ids[label1]][self.node_ids[label2]] = 0        
        self.conn[self.node_ids[label2]][self.node_ids[label1]] = 0

    def getConnections(self):
        res = []
        i = 0
        for x in self.conn:
            j = 0
            for y in x:
                if self.conn[i][j] == 1:
                    res.append((self.node_labels[i],self.node_labels[j]))
                j = j+1
            i = i+1
        return res

    def getConnectionsXYXY(self):
        res = []
        i = 0
        for x in self.conn:
            j = 0
            for y in x:
                if self.conn[i][j] == 1:
                    x = (self.nodes[i][0:2] + self.nodes[j][0:2])
                    res.append(x)
                j = j+1
            i = i+1
        return res

    def getConnectionsLXYLXY(self):
        res = []
        i = 0
        for x in self.conn:
            j = 0
            for y in x:
                if self.conn[i][j] == 1:
                    x = ((self.node_labels[i],) + self.nodes[i][0:2] + (self.node_labels[j],) + self.nodes[j][0:2])
                    res.append(x)
                j = j+1
            i = i+1
        return res
    
    def getStairsXYXY(self):
        res = []
        i = 0
        for x in self.stairs:
            j = 0
            for y in x:
                if self.stairs[i][j] == 1:
                    x = (self.nodes[i][0:2] + self.nodes[j][0:2])
                    res.append(x)
                j = j+1
            i = i+1
        return res

    def getStairsLXYLXYsingle(self):
        res = []
        i = 0
        for x in self.stairs:
            j = 0
            for y in x:
                if self.stairs[i][j] == 1 and j >= i:
                    print self.node_labels[i]
                    print self.nodes[i][0:2]
                    x = (self.node_labels[i],) + self.nodes[i][0:2] + (self.node_labels[j],) + self.nodes[j][0:2]
                    res.append(x)
                j = j+1
            i = i+1
        return res
    
    def getStairsXYXYsingle(self):
        res = []
        i = 0
        for x in self.stairs:
            j = 0
            for y in x:
                if self.stairs[i][j] == 1 and j >= i:
                    x = (self.nodes[i][0:2] + self.nodes[j][0:2])
                    res.append(x)
                j = j+1
            i = i+1
        return res

		
			
