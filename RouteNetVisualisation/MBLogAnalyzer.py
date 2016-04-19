### Parse line-oriented textbased data files, typically logfiles
### a set of regular expressions can be defined.
### the parsLine method tries them step by step until an expression matches the line.
### after a match was found,  the data are returned as LogEvent instances.
### LogEvent is responsible for keeping the patterns and retreiving the data afterwars
### (?P<groupname>\d*>) could for example produce {'groupname': 431} when retrieved as dictionary 
### and when applied to a number.


import re

from MBGenericUtilities import reListLike


class LogParser(object):
	def __init__(self):
		## Die parserliste enthaelt fuer jeden Typ Logzeile einen regulaeren Ausdruck
		self.parsers = []
		# self.parsers.append(re.compile('TimePositionStamp:'+reListLike(['posx','posy','posz']) ))
		# print 'TimePositionStamp: (?P<zeit>[\d.]*);'+reListLike(['posx','posy','posz'])+';'+reListLike(['look1','look2','look3'])+';'

	def addLineParserRE(self,regexp,eventtype,defaultdata=None):
		self.parsers.append((re.compile(regexp),eventtype,defaultdata))

	def parseLine(self, line):
		for (p,eventtype,defaultdata) in self.parsers:
			m = p.match(line)
			##print line
			if m != None:
				##print "match: %s" % m.groupdict(defaultdata)
				return LogEvent(line,eventtype,m.groupdict(defaultdata))
		return LogEvent(line)
		

class LogEvent(object):
	def __init__(self, logline, eventtype = "ET-Unknown", data = None ):
		self.typ = eventtype
		self.logline = logline
		self.data = data
	def getTimeStamp(self):
		if self.typ != "ET-Unknown":
			return float(self.data['zeitstempel'])
		else: return None

	def getLogLine(self):
		return self.logline

	def getEventType(self):
		return self.typ

	def getData(self, fieldnames,converter=(lambda x:x)):
		result = ()
		for f in fieldnames:
#			print f
#			print self.data[f]
			result = result + (converter(self.data[f]),)
#		print result
		return result

	def printAllData(self):
		print self.data

class LogFile(object):
	def __init__(self, filename, parser=LogParser()):
		self.chain = []
		self.parser = parser

		f = open(filename, "r")

		for line in f:
			if line[-1] == "\n": line = line[:-1]
			self.chain.append(self.parser.parseLine(line))
		f.close()
	
	def __repr__(self):
		s = "MBLogAnalyzer.LogFile:\n"
		for e in self.chain:
			s = s + "[%s] %s\n" % (e.getEventType(),e.getLogLine())
		return s

	def getAllEvents(self):
		return self.chain

	def getEventI(self,i):
		return self.chain[i]

	def getEventsByType(self,eventtype):
		return self.getEventsByFilter((lambda x: x.getEventType() == eventtype))

	def getEventsByFilter(self,f):
		"""
		f:	filtering function; return those elements e with f(e) == True.
		i:	index of first element
		j:  index of element following the last element in the range
		"""
		return filter (f,self.chain)

