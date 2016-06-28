import xml.dom.minidom as xml
import re

TRAJ_ORDINARY = 1
TRAJ_SODIPODI = 2

#STROKE_SINGLE = 1
#STROKE_MULTI = 2

#DASH_NONE = 0
#DASH_DRAW = 1
#DASH_HAND = 2

#FILL_NONE = 0
#FILL_HATCH = 1

#MOVE_ONEWAY = 0
#MOVE_OSCIL = 1
#MOVE_REPEAT = 2

#implemented as dictionary
#class StrokeTrajectory(object):
#   def __init__(self,nodeID=None,trajType=TRAJ_ORDINARY,svgpath=None,centre=None,dash=DASH_NONE,move=MOVE_ONEWAY,fill=FILL_NONE)
#       if nodeID:
#       nodeID: self.nodeID = nodeID
#       trajType: self.trajType = trajType
#       svgpath self.svgpath = svgpath
#       centre =self.centre = centre
#       dash = dself.dash = dash
#       move = mself.move = move
#       fill = fself.fill = fill

class SVGDocument(object):
    def __init__(self,filename):
        self.filename = filename
        dom = xml.parse(filename)
        self.dom = dom

        #self.layers = relevantlayers

        self.pathnodes = {}
        self.imagenodes = []

        self.handleDocument(dom.documentElement)

        #self.handleCorpus(dom.getElementsByTagName("annotatedtranscript")[0])
        #pass

    #selectNode = (lambda (node,repeat,elType,extmed) : node)

    def handleDocument(self,docel):
        ns = docel.childNodes

        for n in ns:
            try:
                groupmode = n.getAttribute('inkscape:groupmode')
                layername = n.getAttribute('inkscape:label')
            except AttributeError:
                groupmode = 'X'
                layername = 'X'

            if groupmode == 'layer':
                self.handleLayer(n)

    def handleLayer(self,layer):
        node = layer.firstChild
        while node:
            if node.nodeType == node.ELEMENT_NODE:
                if node.tagName == 'path':
                    self.pathnodes[node.getAttribute('id')] = node
                    ### simple path
                    ### sodipodi
                elif node.tagName == 'g':
                    self.pathnodes[node.getAttribute('id')] = self.handleNestedGroup(node)
                elif node.tagName == 'image':
                    self.imagenodes.append(node)
            node = node.nextSibling

    def handleNestedGroup(self,grouel):
        node = grouel.firstChild
        result = []
        while node:
            try:
                if node.tagName == 'path':
                    result.append(node)
                elif node.tagName == 'g':
                    msg = "!!  Nested Group: %s" % grouel.getAttribute('id')
                    print (msg)
                    #raise InputError(msg)
                    result = result + self.handleNestedGroup(node)
            except AttributeError:
                pass
            node = node.nextSibling
        return result

    def getSodiPodiXY(self,nodeid):
        if nodeid not in self.pathnodes:
            raise ValueRetrieveError("getSodiPodiXY:Node not found %s" % nodeid)
        node = self.pathnodes[nodeid]

        return self.getXYfromSodiPodiNode(node)

    def getXYfromSodiPodiNode(self,node):

        x,y = node.getAttribute('sodipodi:cx') , node.getAttribute('sodipodi:cy')
        if x == "" or y == "":
            raise ValueRetrieveError("no valid coordinates in SodiPodi: %s " % nodeid)

        transf = node.getAttribute('transform')
        if transf:
            m = re.match(r"translate\((\+?-?\d*\.?\d*e?-?\d?\d?),(\+?-?\d*\.?\d*e?-?\d?\d?)\)",transf)
            if not m:
                raise InputError("getXYfromSodiPodiNode: invalid translation.")
            tx,ty =  m.groups()[:2]
            tx,ty = float(tx),float(ty)
        else:
            tx,ty = 0.0,0.0

        return (float(x)+tx,float(y)+ty)


    def getTrajDataFromNode(self,node):
        if node.tagName != 'path':
            raise InputError('node should be a path' % node)

        traj = {}
        traj['nodeID'] = node.getAttribute('id')
        traj['svgpath'] = node.getAttribute('d')
        if node.hasAttribute('sodipodi:type') and node.getAttribute('sodipodi:type') == 'star':
            traj['centre'] = self.getXYfromSodiPodiNode(node)
            traj['type'] = TRAJ_SODIPODI
        else:
            traj['type'] = TRAJ_ORDINARY

        pathstyle = node.getAttribute('style')
        ###stroke-dasharray:12, 1
        m = re.search('stroke-dasharray:([\d\.\,\s]+)',pathstyle)
        traj['role'] = 'you should not read this! the role of a trajectory in a stroke has to be defined...'
        if m:
            dasharray = m.groups()[0].split(',')
            da = [float(x) for x in dasharray]


            if  len(da) == 2 and da[0] > da[1]:
                traj['role'] = 'DRAW'
                #traj['dash'] = "__"

            elif  len(da) == 4 and da[1] == da[3] and da[0] > da[2]:
                #traj['dash'] = "_."
                traj['role'] = 'HAND'
            elif len(da) == 2 and da[0] < da[1] and da[0]*3 < da[1]:
                ### stroke-dasharray:1, 6
                traj['role'] = "DRAW-LIGHT"
            else:
                raise InputError("unrecognized dash pattern")
        else:
            traj['role'] = 'MOVE'

        #EXAMPLES:
        #marker-start:url(#Arrow1Lend-1);marker-end:url(#Arrow1Lstart-8)
        #marker-start:url(#Arrow1Lend);marker-end:url(#Arrow1Lstart)
        #marker-start:url   (#Arrow1Lend-1)
        m1 = re.search('marker-start:url\(([#\w-]+)\)',pathstyle)
        m2 = re.search('marker-end:url\(([#\w-]+)\)',pathstyle)
        if m1:
            if not m2:
                raise InputError("there should be either both or none: marker-start and marker-end")

            arrow1 = m1.groups()[0]
            arrow2 = m2.groups()[0]
            if  arrow1.find('#Arrow1Lend') == 0 and arrow2.find('#Arrow1Lstart') == 0:
                traj['move'] = "OSCILLATE"
            elif arrow1.find('#Arrow1Lstart') == 0 and arrow2.find('#Arrow1Lend') == 0:
                traj['move'] = "REPEAT"
            else:
                raise InputError("unrecognized arrow pattern")
        else:
            if m2:
                raise InputError("there should be either both or none: marker-start and marker-end")
            traj['move'] = "ONCE"

        m1 = re.search('fill-opacity:0.392',pathstyle)
        if m1:
            if traj['move'] != 'ONCE':
                raise InputError("diffuse movement modifier in invalid combination with REPEAT OR OSCILLATE")
            traj['move'] = 'DIFFUSE'

        ### HATCHING / SCHRAFFUR
        m1 = re.search('fill:url\(#Polkadots',pathstyle)
        if m1:
            if traj['move'] != 'ONCE':
                raise InputError("hatch dots in invalid combination with REPEAT, OSCILLATE, DIFFUSE etc.")
            traj['move'] = 'HATCH_DOTS'


        m1 = re.search('fill:url\(#Wavy',pathstyle)
        if m1:
            if traj['move'] != 'ONCE':
                raise InputError("hatch dots in invalid combination with REPEAT, OSCILLATE, DIFFUSE etc.")
            traj['move'] = 'HATCH'

        ## doch handschlag z.b.
        #if traj['role'] == "HAND" and traj['move'] != "ONCE":
        #   raise InputError("Hand edge path should not have movement modifiers: role:HAND / move:%s" % traj['move'])

        #print "TRAJ.move:%s" % traj['move']
        return traj

    def getStroke(self,strokeID):
        """ returns either one path data dictionary OR a list of them if it is a group of trajectories (for a multi finger gesture)"""
        if strokeID not in self.pathnodes:
            return None

        node = self.pathnodes[strokeID]
        if type(node) == list:
            ### its a group of things
            pathdata = []
            for n in self.pathnodes[strokeID]:
                pathdata.append(self.getTrajDataFromNode(n))
        else:
            pathdata = self.getTrajDataFromNode(self.pathnodes[strokeID])
        return pathdata

    def getImageByFname(self, imageFname):
        for node in self.imagenodes:
            if node.getAttribute('xlink:href')[-len(imageFname):] == imageFname:
                break

        x,y = node.getAttribute('x'), node.getAttribute('y')
        w,h = node.getAttribute('width'),node.getAttribute('height')
        filepath = node.getAttribute('xlink:href')
        return (x,y,w,h,filepath)
