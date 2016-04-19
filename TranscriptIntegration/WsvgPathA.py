from xml.dom import minidom, Node
import re


### generic XML treewalker
def walk(parent, outFile, level):                               # [1]
    for node in parent.childNodes:
        if node.nodeType == Node.ELEMENT_NODE:
            # Write out the element name.
            printLevel(outFile, level)
            outFile.write('Element: %s\n' % node.nodeName)
            # Write out the attributes.
            attrs = node.attributes                             # [2]
            for attrName in attrs.keys():
                attrNode = attrs.get(attrName)
                attrValue = attrNode.nodeValue
                printLevel(outFile, level + 2)
                outFile.write('Attribute -- Name: %s  Value: %s\n' % \
                    (attrName, attrValue))
            # Walk over any text nodes in the current node.
            content = []                                        # [3]
            for child in node.childNodes:
                if child.nodeType == Node.TEXT_NODE:
                    content.append(child.nodeValue)
            if content:
                strContent = string.join(content)
                printLevel(outFile, level)
                outFile.write('Content: "')
                outFile.write(strContent)
                outFile.write('"\n')
            # Walk the child nodes.
            walk(node, outFile, level+1)
			

def extractPaths(parent):                               # [1]
	""" extract SVG 'path' nodes from XML tree at any level
		returns a list of pairs [('id-string','path-string')]
	"""
	res = []
	for node in parent.childNodes:
		if node.nodeType == Node.ELEMENT_NODE:
			if node.nodeName == 'path':
				attrs = node.attributes
				res.append((attrs['id'].nodeValue,attrs['d'].nodeValue))

			res=res + extractPaths(node)
	return res
				


def extractPathsFromFile(file):
	""" extract the paths from a file (filename or file handle) 
		returns a list of tuples [(idstring,pathstring),...] 
	"""
	doc = minidom.parse(file)
	rootNode = doc.documentElement
	return extractPaths(rootNode)


def extractPathsFromString(str): 
	""" extract the paths from a SVG/XML string 
		returns a list of tuples [(idstring,pathstring),...] 
	"""
	doc = minidom.parseString(str)
	rootNode = doc.documentElement
	return extractPaths(rootNode)
	
	


### parse 'M x1,y1'         ('M <point>') 
reM = re.compile("\s*M\s+(\d+\.\d+),(\d+\.\d+)\s*") 

### parse one curve segment
### 'x1,y1 x2,y2 x3,y3'		('<helper-point> <helper-point> <point>')
reCurveSegment = re.compile("\s*(\d+\.\d+),(\d+\.\d+)\s+(\d+\.\d+),(\d+\.\d+)\s+(\d+\.\d+),(\d+\.\d+)\s*") 

			

def parseNoncurvedBezier(str):
	""" Parse SVG path string of the form 'M p1 C q2 r2 p2   q3 r3 p3  . . . ' 
		where p_ q_ and r_ are points of the form x,y.
		The curve information q_ and r_ is ignored such that a list of pairs (x,y) is returned. 
		Each pair describes a point of a polyline."""

	### we parse svg paths of the following form:
	### -- head --  ---------------- tail ------------------------------ 
	### M <point>	C	<helper-pointA1> <helper-pointA2> <targetpointA>	|   
	###					<helper-pointB1> <helper-pointB2> <targetpointB>	| --tail-- 
	###					...													|

	### the helper points can be ignored when the path is not curved

	### each <point> is a pair of floats <float>,<float>

	points = []		### will contain all points in the path

	m,ccc = str.split('C')	### split the path in the M head and the C tail (see above)

	matchM = reM.match(m)			### the M head is the move command for the starting point
	points.append(tuple(map(float,matchM.groups())))	### append the first point

	# print matchM.groups()

	### parse each curve segment
	for matchC in reCurveSegment.finditer(ccc):
		print matchC.groups()
		### for each curve segment we only extract the last two values x,y
		### (and ignore the first 4 values of the helper points)
		points.append(tuple(map(float,matchC.groups()[-2:])))

	return points
		

def printLevel(outFile, level):
    for idx in range(level):
        outFile.write('    ')

def run(inFileName):                                            # [5]
	outFile = sys.stdout
	doc = minidom.parse(inFileName)
	rootNode = doc.documentElement
	level = 0
	res =  extractPaths(rootNode, outFile, level)

	result = []		### will contain all paths

	### go through all extracted path XML-elements
	### each of the form (id,path-string)
	for id,pathstring in res:
		points = parseNoncurvedBezier(pathstring) 
		
		result.append((id,points))
		


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        print 'usage: python svgParser01.py <infile.xml>'
        sys.exit(-1)
    run(args[0])


if __name__ == '__main__':
    main()