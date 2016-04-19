### visualization of trajectories, that is sequences of (x,y)-pairs representing locations 
### usually locations correspond to timesteps of equal distance.


from pyx import *
from random import random
from math import sin,cos,pi

def colmap_grayA (x):
	return color.rgb(x,x,x)

def colorMap_GrayA (x):
	m = 0.90
	b = 0
	xx = m*x + b
	print "colorMap_GrayA (%f) = color.rgb(%f,%f,%f)" % (x,xx,xx,xx)
	return color.rgb(xx,xx,xx)


def colorMap_KunterbuntA (x):
	print x
	if 0. <= x and x <= 1.0/6.0:       return color.rgb(1,									x*6,								0)
	elif 1.0/6.0 < x and x <= 2.0/6.0: return color.rgb(round(1 - ((x - 1.0/6.0) *6),7),	1,									0)
	elif 2.0/6.0 < x and x <= 3.0/6.0: return color.rgb(0,									1,									round((x - 2.0/6.0) *6,7))
	elif 3.0/6.0 < x and x <= 4.0/6.0: return color.rgb(1,									round(1 - ((x - 3.0/6.0) *6),7),	1)
	elif 4.0/6.0 < x and x <= 5.0/6.0: return color.rgb(round((x - 4.0/6.0) *6,7),			0,									1)
	elif 5.0/6.0 < x and x <= 6.0/6.0: return color.rgb(1,									0,									round(1 - ((x - 5.0/6.0) *6),7))
	else:

		print "internal program error AA: x = %f" % x
		raise Exception()


def colorMap_KunterbuntB (x):
	return color.hsb(x-int(x),1,1)

def colorMap_KunterbuntC (x):
	return color.hsb(round((x-int(x)),1),1,1)



#     def drawRouteNetwork(self):
#         for (x1,y1,x2,y2) in self.net.getConnectionsXYXY():
#             self.canvas.stroke(path.line(x1,y1,x2,y2),[style.linewidth(2*self.rad),color.grey(0.85)])
#
#         for (x1,y1,x2,y2) in self.net.getStairsXYXYsingle():
#             self.canvas.stroke(path.line(x1,y1,x2,y2),[style.linewidth(self.rad*0.75),color.grey(0.85),style.linestyle.dashed])
#
#         for (x,y,l) in self.net.getAllXYLabel():
#             self.canvas.stroke(path.circle(x,y,self.rad*1.15),[deco.filled([color.grey(1.0)])])
#             ##self.canvas.text(x,y,l,[text.size(5),text.valign(0.5,0.5),text.halign(0.5,0.5)])
#             #self.canvas.text(x+self.rad,y+self.rad,l,[text.size(5),text.valign(0.5),text.halign(0.5,0.5)])
#             self.canvas.text(x+self.rad,y+self.rad,l,[text.size(5)])

def rndcolor():
	return color.rgb(random()*0.75, random()*0.75, random()*0.75)


class TrajectViz(object):
	def __init__(self,scale=1,radius=1,textsize=1,mirrorx=False,mirrory=False):
		self.rad = radius
		self.scale = scale
		self.tsize = textsize
		self.canvas = canvas.canvas()

		if mirrorx: 	self.mx = -1.0
		else:           self.mx = 1.0
		if mirrory: 	self.my = -1.0
		else:           self.my = 1.0

	def writePDFfile(self,filename):
		self.canvas.writePDFfile(filename)

	def writeEPSfile(self,filename):
		self.canvas.writeEPSfile(filename)

	def drawTrajectory(self,traj,cmap=(lambda x:color.rgb(0,0,0))):
		traj = map (lambda (x,y): (x*self.scale*self.mx , y*self.scale*self.my), traj)

		if len(traj) == 0:
			pass
		elif len(traj) == 1:
			x,y = traj[0]
			self.canvas.stroke(path.circle(x,y,self.rad))
		else:
			x1,y1 = traj[0]
			c = 0.0
			for x,y in traj[1:]:
				#self.canvas.stroke(path.line(x1,y1,x,y),[cmap(c/(len(traj)-1))])
				self.canvas.stroke(path.line(x1,y1,x,y),[cmap(c/250.0)])
				if int(c) % 15 == 0: self.canvas.text(x,y,"%d" % int(c/15) ,[text.size(self.tsize),cmap(c/250.0)])
				x1,y1 = x,y
				c = c + 1

	def drawText( self, s, x, y, attribs=[text.size(5)] ):
		s = s.replace("_","\_")
		self.canvas.text(x,y,s,attribs)

	def drawGates(self,gates,color=color.rgb(0,0,0)):
		"""
		gates:	list of tuples (x-location,y-location,radius,label)
		color:	color to draw with
		"""

		gates = map( lambda (x,y,r,l) : (x*self.scale*self.mx,y*self.scale*self.my,r*self.scale,l), gates)

		for x,y,rad,lab in gates:
			self.canvas.stroke(path.circle(x,y,rad),[color])
			self.canvas.text(x,y,lab,[text.size(self.tsize),text.valign.middle,color])

	def drawCircle(self,x,y,r,color=color.rgb(0,0,0)):
			self.canvas.stroke(path.circle(x*self.scale*self.mx,y*self.scale*self.my,r*self.scale),[color])


### old code for drawing one trajectory as one path
#			p = path.path()
#			x,y = traj[0]
#			#print "start path: %f , %f" % x,y
#			p.append(path.moveto(x,y))
#			for i in range(len(traj)-1):
#				x,y = traj[i+1]
#				p.append(path.lineto(x,y))
#				# print "continue: %f , %f" % x,y
#			self.canvas.stroke(p,[color,deco.earrow])


# 	def offset(self,p):
# 		x,y = p
# 		a = random() * 2 * pi
# 		r = random() * self.rad
# 		xoff = cos(a) * r
# 		yoff = sin(a) * r
# 		##print "(%f,%f)" % (xoff,yoff)
# 		return x + xoff, y + yoff


