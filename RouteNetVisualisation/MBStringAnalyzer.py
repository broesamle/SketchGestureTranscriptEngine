### generic string analysis facilites based on regular expressions,
### handling of multiple patterns and counting of matches in larger texts.


import re

class StringAnalyzer(object):
	def __init__(self):
		## Die parserliste enthaelt fuer jedes Pattern einen regulaeren Ausdruck
		self.parsers = []
		# self.parsers.append(re.compile('TimePositionStamp:'+reListLike(['posx','posy','posz']) ))
		# print 'TimePositionStamp: (?P<zeit>[\d.]*);'+reListLike(['posx','posy','posz'])+';'+reListLike(['look1','look2','look3'])+';'

	def addPattern(self,regexp,patternname):
		self.parsers.append((re.compile(regexp),patternname))

	def countAllPatterns(self,s):
		result = {}
		for rex,name in self.parsers:
			result[name] = len(rex.findall(s))
		return result
