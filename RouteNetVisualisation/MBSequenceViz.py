### vizualization of sequences of gat encounters. Gates are tyically fixed locations in a layour and each encounter
### (participant touches or passes gate) is captured in a logfile. Every gate has to be identified such that 
### sequences of gate encounters to gether with cate locations can be used to reconstruct a discretized trajectory.
### this module wants to vizualize such sequences given a set of named gate locations.

from MBRouteNet import RouteNetwork

from pyx import *
from random import random
from math import sin,cos,pi

class ElevRouteNetwork(RouteNetwork):
    def __init__(self):
        RouteNetwork.__init__(self)
        self.elev = {}

    def setElevation(self,label,elev):
        self.elev[label] = elev

    def getElev(self,label):
        return self.elev[label]

    def eval(self,label):
        return self.elev[label]


    def setAllElevationsLE(self,labels,elevations):
        tmp = zip(labels,elevations)
        for l,e in tmp:
            self.setElevation(l,e)

    def gain(self,a,b):
        return self.eval(b) - self.eval(a)

    def maxgainExcludeB(self,a,b):
        nn = filter(lambda (l,x) : l!=b , self.getNeighboursLE(a))
        return max( map ( lambda (x,waste) : self.gain(a,x) , nn) )

    def maxgain(self,a):
        nn = self.getNeighboursLE(a)
        return max( map ( lambda (x,waste) : self.gain(a,x) , nn) )


    def penaltyAB(self,a,b):
        return self.maxgain(a) - self.gain(a,b)

    def penaltyABC(self,a,b,c):
        """Penalty for going from node a to node b when coming from c: ( c-> ) a => b.
        The calculation of the maximal gain from node a usually excludes the origin node c.
        If destination b and origin c are equal it means that a backtracking episode begins at node a.
        In this case all neighbours of a (including c) are considered."""
        if b != c:      return self.maxgainExcludeB(a,c) - self.gain(a,b)
        else:           return self.penaltyAB(a,b)

    def penaltyRoute(self,seq):
        if len(seq) == 0:
            return 0
        elif len(seq) == 1:
            return 1
        elif len(seq):
            res = 0
            res = res + self.penaltyAB(seq[0],seq[1])
            print "penalty for %s -> %s: %f" % (seq[0],seq[1],self.penaltyAB(seq[0],seq[1]))

            for i in range(len(seq)-2):
                ### penalty for going from    a       to  b       coming from  c
                res = res + self.penaltyABC(  seq[i+1],   seq[i+2],            seq[i])
                print "penalty for (%s...) %s -> %s : %f" % (seq[i],seq[i+1],seq[i+2],self.penaltyABC(seq[i+1], seq[i+2], seq[i]))

            return res

    def penaltyRouteOhneRuecksperre(self,seq):
        if len(seq) == 0:
            return 0
        elif len(seq) == 1:
            return 1
        elif len(seq):
            res = 0
            res = res + self.penaltyAB(seq[0],seq[1])
            print "penalty for %s -> %s: %f" % (seq[0],seq[1],self.penaltyAB(seq[0],seq[1]))

            for i in range(len(seq)-2):
                ### penalty for going from    a       to  b       coming from  c
                res = res + self.penaltyAB(  seq[i+1],   seq[i+2])
                print "penalty for (%s...) %s -> %s : %f" % (seq[i],seq[i+1],seq[i+2],self.penaltyAB(seq[i+1], seq[i+2]))

            return res

    def meanRouteEval(self,seq):
        total = 0
        for x in seq:
            total = total + self.eval(x)
        return total / len(seq)

    def maxRouteEval(self,seq):
         return max (map (self.eval, seq))

    def minRouteEval(self,seq):
         return min (map (self.eval, seq))


##            p.append(path.moveto(x,y))
##            for i in range(len(seq)-1):
##                x,y = self.offset(self.net.getXY(seq[i+1]))
##                p.append(path.lineto(x,y))
##            self.canvas.stroke(p,[color,deco.earrow])


    def getNeighboursLE(self,label):
        res = []

        j = 0
        for y in self.conn[self.node_ids[label]]:
            if y == 1:
                x =  self.node_labels[j] , self.getElev(self.node_labels[j])
                res.append(x)
            j = j+1

        j = 0
        for y in self.stairs[self.node_ids[label]]:
            if y == 1:
                x =  self.node_labels[j] , self.getElev(self.node_labels[j])
                res.append(x)
            j = j+1

        return res


###  #######################  ###
###  #######################  ###
###   VISUALIZATION CLASSES   ###
###  #######################  ###
###  #######################  ###

class RouteViz:
    def __init__(self,routenet,r=1):
        self.canvas = canvas.canvas()
        self.net = routenet
        self.rad = r
        self.xoffset = -r/2
        self.yoffset = -r/2
        self.rscale = 1
        self.scal = 1.0


##### falls man irgendwann mal mit scalierung anfangen will ...
# 	def setScale (self,scale):
# 		self.scal = scale
# 
# 	def scaleX (self,x):
# 		return self.scal*x
# 
# 	def scaleSeq (self,s):
# 		return map (self.scaleX,s)

    def drawRouteNetwork(self):
        for (x1,y1,x2,y2) in self.net.getConnectionsXYXY():
            self.canvas.stroke(path.line(x1,y1,x2,y2),[style.linewidth(2*self.rad),color.grey(0.85)])

        for (x1,y1,x2,y2) in self.net.getStairsXYXYsingle():
            self.canvas.stroke(path.line(x1,y1,x2,y2),[style.linewidth(self.rad*0.75),color.grey(0.85),style.linestyle.dashed])

        for (x,y,l) in self.net.getAllXYLabel():
            self.canvas.stroke(path.circle(x,y,self.rad*1.15),[deco.filled([color.grey(1.0)])])
            ##self.canvas.text(x,y,l,[text.size(5),text.valign(0.5,0.5),text.halign(0.5,0.5)])
            #self.canvas.text(x+self.rad,y+self.rad,l,[text.size(5),text.valign(0.5),text.halign(0.5,0.5)])
            self.canvas.text(x+self.rad,y+self.rad,l,[text.size(5)])

    def drawRoute(self,seq,color=None):
        if color == None: color = self.color()
        
        if len(seq) == 0:
            pass
        elif len(seq) == 1:
            x,y = self.net.getXY(seq[0])
            self.canvas.stroke(path.circle(self.offsetX(x)+self.xoffset,y+self.yoffset,self.rad*0.1))
        else:
            p = path.path()
            x,y = self.offset(self.net.getXY(seq[0]))
            p.append(path.moveto(x,y))
            for i in range(len(seq)-1):
                x,y = self.offset(self.net.getXY(seq[i+1]))
                p.append(path.lineto(x,y))
            self.canvas.stroke(p,[color,deco.earrow])            
    
    def offset(self,p):
        x,y = p
        a = random() * 2 * pi
        r = random() * self.rad
        xoff = cos(a) * r
        yoff = sin(a) * r
        ##print "(%f,%f)" % (xoff,yoff)
        return x + xoff, y + yoff


    def color(self):
        return color.rgb(random()*0.75, random()*0.75, random()*0.75)
        
    def writePDFfile(self,filename):
        self.canvas.writePDFfile(filename)
        
    def writeEPSfile(self,filename):
        self.canvas.writeEPSfile(filename)
        

class ElevViz(RouteViz):
    def __init__(self,routenet,r=1,rscale=1,ascale=1):
        RouteViz.__init__(self,routenet,r)
        self.rscale = rscale    ### wie stark werden die absoluten werte hervorgehoben (knotenradius)
        self.ascale = ascale    ### wie stark werden die unterschiede hervorgehoben (pfeildicke)
        

    def drawElevation(self,f=(lambda x:x)):
        print "es wird gedruckt"

        for (l1,x1,y1,l2,x2,y2) in self.net.getStairsLXYLXYsingle():
            g = self.net.gain(l1,l2)
            fg = g * self.rscale * self.ascale
            print "fg = %f" % fg
            if g > 0:
                self.canvas.stroke(path.line(x1,y1,x2,y2),[style.linewidth(fg),color.rgb(1,0.5,0.5),deco.arrow(size=fg*4,angle=28)])
            elif g < 0:
                self.canvas.stroke(path.line(x2,y2,x1,y1),[style.linewidth(-fg),color.rgb(1,0.5,0.5),deco.arrow(size=-fg*4,angle=28)])
            else:
                #ggf [...,style.linestyle.dashed])
                self.canvas.stroke(path.line(x2,y2,x1,y1),[style.linewidth(self.rad*0.1),color.rgb(1,0.5,0.5)])

        for (l1,x1,y1,l2,x2,y2) in self.net.getConnectionsLXYLXY():
            g = self.net.gain(l1,l2)
            fg = g * self.rscale * self.ascale
            print "fg = %f" % fg
            if g > 0:
                self.canvas.stroke(path.line(x1,y1,x2,y2),[style.linewidth(fg),color.rgb(0.5,0.5,1),deco.arrow(size=fg*4,angle=28)])
            elif g < 0:
                self.canvas.stroke(path.line(x2,y2,x1,y1),[style.linewidth(-fg),color.rgb(0.5,0.5,1),deco.arrow(size=-fg*4,angle=28)])
            else:
                self.canvas.stroke(path.line(x2,y2,x1,y1),[style.linewidth(self.rad*0.1),color.rgb(0.5,0.5,1)])

        for (x,y,l) in self.net.getAllXYLabel():
            print "%d %d %s %f" % (x,y,l,self.net.getElev(l)*self.rscale)
#            self.canvas.stroke(path.circle(x,y,self.net.getElev(l)*self.rscale),[deco.filled([color.grey(1.0)])])
            #self.canvas.stroke(path.circle(x,y,f(self.net.getElev(l))*self.rscale),[deco.filled([color.grey(1.0)])])
            self.canvas.stroke(path.circle(x,y,f(self.net.getElev(l))*self.rscale))
            self.canvas.text(x+self.rad,y+self.rad,"%s (%f)"%(l,self.net.getElev(l)),[text.size(5)])

##r = RouteNetwork()
##r.addNode("AA",10,20)
##r.addNode("BB",20,20)
##r.addNode("CC",30,40)
##r.addNode("DD",50,10)
##r.fixNodes()
##print r.conn
##r.connectNodes('AA','DD')
##r.connectNodes('BB','DD')
##r.connectNodes('AA','CC')
##
##v = RouteViz(r)
##v.drawRouteNetwork()
##v.writePDFfile("test")


