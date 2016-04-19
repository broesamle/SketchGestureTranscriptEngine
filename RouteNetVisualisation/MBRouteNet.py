### representing route networks as specialized graphs with connection matrix.
### IMPORTANT: always call fixNodes() before adding any connections as this initializes the connection matrix.
### special connections can be addes as stairs (if thats of any general help at all; so far, we used it for the günne building, only)



from random import random, randint


class RouteNetwork:
	def __init__(self):
		self.node_ids = {}		# Woerterbuch, in dem zu jedem Label der Index in der Knotenliste und der Verbindungsmattrix abgelegt ist.
		self.node_labels = []	# die labels zu jedem index
		self.nodes = [] 		# die koordinaten als (x,y,z)-Tupel
		self.conn = []			# die verbindungsmatrix
		self.stairs = []		 # die verbindungsmatrix fuer die treppen
		self.nodesFixed = False

	def addNode(self,label,x=0,y=0,z=0):
		if self.nodesFixed == False:
			self.node_ids[label] = len(self.nodes)
			self.nodes.append((x,y,z))
			self.node_labels.append(label)
		else:
			raise Exception,"Attempt to add nodes after fixNodes() was already called!"

	def scaleAllCoords(self,factor):
		self.nodes = map ( lambda (x,y,z) : (x*factor,y*factor,z*factor), self.nodes )

	def scaleAllCoordsXYZ(self,fx,fy,fz):
		self.nodes = map ( lambda (x,y,z) : (x*fx,y*fy,z*fz), self.nodes )

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
		self.nodesFixed = True

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

	def getAllLabel(self):
		return self.node_labels

	def connectNodes(self, label1, label2):
		if self.nodesFixed:
			self.conn[self.node_ids[label1]][self.node_ids[label2]] = 1
			self.conn[self.node_ids[label2]][self.node_ids[label1]] = 1
		else:
			raise Exception, "Attempt to connect Nodes before calling fixNodes!"

	def stairsBetweenNodes(self, label1, label2):
		if self.nodesFixed:
			self.stairs[self.node_ids[label1]][self.node_ids[label2]] = 1
			self.stairs[self.node_ids[label2]][self.node_ids[label1]] = 1
		else:
			raise Exception, "Attempt to connect Nodes before calling fixNodes!"

	def disconnectNodes(self, label1, label2):
		if self.nodesFixed:
			self.conn[self.node_ids[label1]][self.node_ids[label2]] = 0
			self.conn[self.node_ids[label2]][self.node_ids[label1]] = 0
		else:
			raise Exception, "Attempt to connect Nodes before calling fixNodes!"

	def getConnections(self):
		if not self.nodesFixed: raise Exception, "Access to connections before calling fixNodes()"

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

	def getNeighbours(self,label):
		#print "CALL: getNeighbours(%s)" %label
		result = []
		#print self.node_ids
		eigenerindex = self.node_ids[label]
		for i in range(len(self.node_ids)):
			if self.conn[eigenerindex][i] and i != eigenerindex : result.append(self.node_labels[i])
		return result
		
		
class RouteAgent(object):
	def __init__(self, routenet, startlabel):
		self.rn = routenet
		self.loc = startlabel

class RndAgent(RouteAgent):
	def __init__(self, routenet, startlabel, allow180Return = False):
		RouteAgent.__init__(self, routenet, startlabel)
		self.allow180 = allow180Return
		self.oldloc = None


	def walkOneStep (self):
		nei = self.rn.getNeighbours(self.loc)

		if (not self.allow180) and len(nei) >= 2: 	## if no 180 degree returns are allowed, remove the old location where the agent just comes from
			nei.remove(self.oldloc)       # but only if there are at least two neighbours
		self.oldloc = self.loc
		self.loc = nei[randint (0, len(nei) -1)]
		return self.loc

	def walkNSteps(self,n):
		res = []
		for i in range(n):
			res.append(self.walkOneStep())
		return res

	def getLocation(self):
		return self.loc

