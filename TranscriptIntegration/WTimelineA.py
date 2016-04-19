import logging
import re
from operator import itemgetter

from collections import defaultdict

#############################################################
######    INTERVAL TIMELINE    ##############################
######    INTERVAL TIMELINE    ##############################
######    INTERVAL TIMELINE    ##############################
#############################################################

### alternating increase:
### generate sequence: 0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5, 6, -6, 7, -7, 8, -8, 9, -9, 10
### from sequence      0, 1,  2, 3,  4, 5,  6, 7,  8 ...
###                  1,-1,1,-1...      0,1,1,2,2,3,3
###                  ------------      -------------

def alterInc(x): 	return (2*(x%2)-1)   *   (x+(x%2))/2

###   ! ! !   Don't Touch This Class -- it's essential for SpaDoAK and the Multimodal Corpus ! ! ! ###
###   ! ! !   Don't Touch This Class -- it's essential for SpaDoAK and the Multimodal Corpus ! ! ! ###
###   ! ! !   Don't Touch This Class -- it's essential for SpaDoAK and the Multimodal Corpus ! ! ! ###
###   ! ! !   Don't Touch This Class -- it's essential for SpaDoAK and the Multimodal Corpus ! ! ! ###

## !! make subclasses of it!

class IntervalTimeline(object):
	""" Implements a data structure for handling intervals on one dimension, e.g, time. On this 'timeline', intervals (startpoint, stoppoint, interval id, and additional data) can be defined. 
		Intervals are organised based on their start timestamp *as well as* their stop timestamp. it is important to note that a timestamp is used as an identifier for a particular point in time. 
		however the exact arithmetical representation of seeconds, milliseconds and the like is not used for organising intervals and PITs. The string representing a timestamp is only evaluated
		in terms of identity or difference with other timestamps."""

	last_id = 100
	
	def nextID(self):
		#IntervalTimeline.last_id += 1
		IntervalTimeline.last_id += 1
		return IntervalTimeline.last_id		
	
	def __init__(self):
		self.intervalsByID = {}
		self.intervalIDorder = []
		self.intervalsByStart = defaultdict(list)
		self.intervalsByStop = defaultdict(list)
		###########            self.points = set()
		self.data = {}
		
		
		###############self.pointsByID = {}
		###############self.pointsByTimestamp = {}
		
				############
				############
				##def putPoint( self, timestamp):
					##if timestamp not in self.pointsByTimestamp:
					##	pointID = "PNT%05d" % self.nextID()
					##	self.pointsByTimestamp[timestamp] = pointID
					##	self.pointsByID[pointID] = timestamp
					##	logging.debug("IntervalTimeline:putPoint(%s): new pointID=%s" % (timestamp,pointID))
					##else:
					##	logging.debug("IntervalTimeline:putPoint(%s): old pointID=%s" % (timestamp,self.pointsByTimestamp[timestamp]))

					##return self.pointsByTimestamp[timestamp]
				#############
				#############
	
	def defineInterval(self, startTS, stopTS, iid = None, data = None):
		logging.debug("IntervalTimeline:defineInterval %s" % str((startTS,stopTS,iid,data)))
		if iid == None:
			iid = "INT%05d" % self.nextID()
			if iid in self.intervalsByID:
				raise ValueError("OH OH interval with ID %s already exists" % iid)
		else:
			if iid in self.intervalsByID:
				raise ValueError("interval with ID %s already exists" % iid)
		
		#######                    startID =  self.putPoint(startTS)
		#######                    stopID =  self.putPoint(stopTS)
		
		self.intervalsByID[iid] = (startTS,stopTS)

		self.data[iid] = data
		
		self.intervalsByStart[startTS].append(iid)	
		self.intervalsByStop[stopTS].append(iid)
		self.intervalIDorder.append(iid)
		logging.debug("IntervalTimeline:defineInterval(...): IID: %s" % (iid))
		return iid

	def getInterval(self,iid):
		return self.intervalsByID[iid]

	def getIntervalsStartingAt(self,timestamp):
		return self.intervalsByStart[timestamp]


	def getIntervalsStoppingAt(self,timestamp):
		return self.intervalsByStop[timestamp]


	def __str__(self):
		s = "IntervalTimeline:\n"
		s += "Intervals: " + str(self.intervalsByID)
		s += "Points: " + str(self.pointsByID) + "\n" + str(self.pointsByTimestamp)
		return s
		
		

		
class Interval(object):
	def __init__(self,start,stop):
		self.start = start
		self.stop = stop
		
	def stopsEarlierTS (self,timestamp):
		return self.stop < timestamp
	
	def startsLaterTS (self,timestamp):
		return self.start > timestamp
	
	def overlaps(self,interval):
		return 	((interval.start <= self.start and self.start < interval.stop) or	### Start1 in Interval2  
				(interval.start < self.stop and self.stop <= interval.stop) or		### Stop1 in Interval2
				(self.start <= interval.start and interval.stop <= self.stop))		### interval1 umgreift interval2

	def __repr__(self):
		return '(' + self.start.__repr__() + ',' +  self.stop.__repr__() + ')'
		
		
class ArithmeticTimeLine(IntervalTimeline):
	
	
	""" currently not in use!! """
	
	
	def getIntervalsAfter(self,timestamp):
		"""      X                    --> t
		            *--------+
				   *------+ *-----+
		"""
		pass
		
	def getIntervalsBefore(timestamp):
		pass


################################################################
######    TIMESTAMP OPERATIONS    ##############################
######    TIMESTAMP OPERATIONS    ##############################
######    TIMESTAMP OPERATIONS    ##############################
######    TIMESTAMP OPERATIONS    ##############################
################################################################



def isNativePremiereTS(ts):
	"""Check whether the string is of the native premiere timestamp form hh:mm:ss:ff (interpolated timestamps with offset return false)"""
	m = re.match(r"(?P<hh>\d+):(?P<mm>\d+):(?P<ss>\d+):(?P<ff>\d+)$",ts)
	if m:
		return True
	else:
		return False

### keying of timestamps (for sorting) ########
def keyPremiereTS(ts):
	m = re.match(r"(?P<hh>\d+):(?P<mm>\d+):(?P<ss>\d+):(?P<ff>\d+)",ts)
	if not m: 	raise ValueError ('Timestamp %s does not match!' % ts)
	d = m.groupdict()
	return int(d['hh'])*60*60*25 + int(d['mm'])*60*25 + int(d['ss'])*25.0 + int(d['ff'])

### sometimes a premiere timestamp wants to be offset by a number, which indicates a number of steps away in the sequence data
def keyPremiereTSoffset(ts):
	m = re.match(r"(?P<hh>\d+):(?P<mm>\d+):(?P<ss>\d+):(?P<ff>\d+)(?P<offset>[+-]\d+)?",ts)
	if not m: 	raise ValueError ('Timestamp %s does not match!')
	
	d = m.groupdict()
	
	if d['offset'] == None: d['offset'] = 0
	if int(d['offset']) >=100000:
		raise ValueError("offset too large")
		
	return int(d['hh'])*60*60*25*1000000 + int(d['mm'])*60*25*1000000 + int(d['ss'])*25.0*1000000 + int(d['ff'])*1000000 + int(d['offset'])


def keyElanTS(ts):
	m = re.match(r"(?P<hh>\d+):(?P<mm>\d+):(?P<sec>\d+)(?P<msec>\.\d*)",ts)
	if not m: 	raise ValueError ('Timestamp %s does not match!' % ts)
	d = m.groupdict()

	return int(d['hh'])*60*60*25 + int(d['mm'])*60*25 + (float(d['sec'])+float(d['msec']))*25



##############################################################
######    ANNOTATED SEQUENCE    ##############################
######    ANNOTATED SEQUENCE    ##############################
######    ANNOTATED SEQUENCE    ##############################
##############################################################


BY_INDEX = 1
BY_TIMESTAMP = 2

## pseudo timestamps for identifying the in/outpoints of a subsequence
TS_INPOINT = "INx"
TS_OUTPOINT = "OUTy"


class AnnotatedSequence(IntervalTimeline):
	""" AnnotatedSequence extends the interval logic provided by IntervalTimeline. A sequence logic  provided additional functionality for filling
		intervals and segments between with text. This way, the logic of annotated text is implemented. The underlying text representation
		(so to say sequential raw data) is enriched by defining intervals. Intervals have -- besides start+stop timestamp and data (see above) a
		start+stop index in the sequence. Each index refers to a position in the sequence data. Each Timestamps become thus related to a sequence index.
		Multiple different timestamps may refer to the same index (for example if there is a longer speech pause while drawing acts have been annotated.)
		Important: While it is the responsibility of AnnotatedSequence to manage sequence data (slicing, indexes etc.) it is not responsible for the
		time arithmetics behind the timestamps. In other wors, timestamps could theoretically be random strings without any inherent timing information.
		What matters is simply the identity of timestamp strings, and the intervals starting and stopping at them. """

	def __init__(self,sequence):
		self.seq = sequence
		self.pointIdxByTS = {}
		self.pointTSByIdx = {}
		self.setPrintRegion()
		
		#self.sectionIdxByLabel = {}
#		self.sectionList = []
		#self.sectionLabelByIdx{}
		
		 
		
		### multiple points (with different timestamps) may have the same index ! ! !
		#self.pointIDByIdx = {}		# does not work ! ! !
		IntervalTimeline.__init__(self)
	
	def setPrintRegion(self,a=None,b=None):		
		self.printIn,self.printOut = a,b

	def __str__(self):
		if self.printIn == None or self.printIn < 0:	
			self.printIn = 0
		if self.printOut == None or len(self.seq) < self.printOut:		
			self.printOut = len(self.seq)
		s = "Annotated Sequence: region (%d,%d)\n" % (self.printIn,self.printOut)
		for iid in self.intervalIDorder:
			startTS,stopTS = self.intervalsByID[iid]
			startIdx,stopIdx = self.pointIdxByTS[startTS] , self.pointIdxByTS[stopTS] 
			data = self.data[iid]
			#print ((self.printIn,startIdx,stopIdx,self.printOut)) 
			if self.printIn <= startIdx and startIdx <= self.printOut  or self.printIn <= stopIdx and stopIdx <= self.printOut  :
				#print "doing"		 
				s += "Interval %s:%s/%d,%s/%d--%s\n" % (iid,startTS,startIdx,stopTS,stopIdx,data)
				
		s += "PITs" + str(range(self.printIn,self.printOut+1)) + ":\n"
		
		for idx in range(self.printIn,self.printOut+1):
			if idx in self.pointTSByIdx:
				pits = self.pointTSByIdx[idx]	
			else:
				pits = []
			if pits != []:	s+= "%d:%s\n" % (idx,str(pits))
			
		#s += "Sequence:" + str(self.seq[self.printIn:self.printOut])
		#for startTS,startIdx,stopTS,stopIdx,subseq in self.iterSegments(self.printIn,self.printOut):
		#	s += "\n[%s/%d]%s" % (startTS,startIdx,str(subseq))
		#s += "[%s/%d]\n" % (stopTS,stopIdx)

		s += str(self.seq)

		self.setPrintRegion()
		return s

	####################################
	### intervals and related operations
	####################################
	def __iter__(self):	return ASeqIntervalIter(self)

	def __len__(self): return len(self.seq)

	def getIntervalSegment(self,iid):
		startTS,stopTS = self.getInterval(iid)
		startIdx,stopIdx = self.pointIdxByTS[startTS] , self.pointIdxByTS[stopTS]
		segment = self.seq[startIdx:stopIdx]
		return (startTS,startIdx,stopTS,stopIdx,segment)

	def addInterval(self, startTS, stopTS, startIdx, stopIdx ,uniqueID = None, data = None, ):

		uniqueID = IntervalTimeline.defineInterval(self, startTS, stopTS, uniqueID, data)

		#(startID,stopID) = self.intervalsByID[uniqueID]

#		if startIdx == None or stopIdx == None:
		logging.debug("BREAK:" + str((startTS, stopTS, uniqueID, data, startIdx, stopIdx)))
#			exit(1)
		self.addPIT(startTS,startIdx)
		self.addPIT(stopTS,stopIdx)
		
#		self.pointIdxByTS[startTS] = startIdx
#		self.pointIdxByTS[stopTS] = stopIdx	

#		self.pointTSByIdx[startIdx].append(startTS)		# # # this should work ! ! !
#		self.pointTSByIdx[stopIdx].append(stopTS)		
		
		logging.debug("ASeq:addInterval: (%s,%d)-(%s,%d)" % (startTS,startIdx,stopTS,stopIdx))
		return uniqueID
		
	def appendAsInterval(self, startTS, stopTS, seq, uniqueID = None, data = None):
		
		startIdx = len(self.seq)
		self.seq += seq
		stopIdx = len(self.seq)
		
		uid = self.addInterval(startTS, stopTS, startIdx, stopIdx, uniqueID=uniqueID, data=data, )
		#logging.debug("ASeq:appendAsInterval %s: %s/%d,%s/%d; %s, %s) ...%s" % (uid, startTS, startIdx, stopTS, stopIdx, uniqueID, data, seq[-40:]))
		logging.debug("ASeq:appendAsInterval %s: %s/%d,%s/%d; %s, %s)" % (uid, startTS, startIdx, stopTS, stopIdx, uniqueID, data))
		#print "APPEND INTERVAL %s %s: [%s/%d..%s/%d] %s" % (uid,data,startTS,startIdx,stopTS,stopIdx,seq)
		
		return uid
	
	def append(self,seq):
		self.appendSequence(seq)
		
	def appendSequence(self,seq):
		#logging.debug("ASeq:append: ...%s" % str(seq[-40:]))
		self.seq.append(seq)

	def appendPIT(self,timestamp):
		self.addPIT(timestamp,Idx=None)		## Idx = None ---> end of sequence will be used
			
	def addPIT(self,timestamp,Idx=None):
		""" add a PIT but change neither the sequence data nor the interval logic of IntervalTimeline""" 
		if Idx == None:
			Idx = len(self.seq)
		logging.debug("ASeq:addPIT: %s/%d" % (timestamp,Idx))

		self.pointIdxByTS[timestamp] = Idx
		
#		self.pointIDByIdx[startIdx] = startTS		# # # does not work ! ! !

		# # # but this should work ! ! !
		if Idx in self.pointTSByIdx:
			self.pointTSByIdx[Idx].append(timestamp)
		else:
			self.pointTSByIdx[Idx] = [timestamp] 
		
	def existsTimestamp(self,timestamp):
		return timestamp in self.pointIdxByTS
		
	def touchingIntervalsByIdx(self,a,b):
		resultSet = set([])
		resultList = []
		
		for idx in range(a,b):
			if idx in self.pointTSByIdx:
				TSs = self.pointTSByIdx[idx]
				
				for TS in TSs:
					if TS in self.intervalsByStart:
						for iid in self.intervalsByStart[TS]:
							#print iid					
							startTS, stopTS = self.intervalsByID[iid]
							startIdx,stopIdx = self.pointIdxByTS[startTS] , self.pointIdxByTS[stopTS]
							data = self.data[iid]
							
							interv = (iid,startTS,startIdx,stopTS,stopIdx,data)
							resultList.append(interv)
							resultSet.add(iid)

					if TS in self.intervalsByStop:
						for iid in self.intervalsByStop[TS]:
							
							if iid not in  resultSet:
								startTS, stopTS = self.intervalsByID[iid]
								startIdx,stopIdx = self.pointIdxByTS[startTS] , self.pointIdxByTS[stopTS]
								data = self.data[iid]
								
								interv = (iid,startTS,startIdx,stopTS,stopIdx,data)
								resultList.append(interv)
								resultSet.add(iid)
		
		return resultList		
		

	##################################################
	### Points and segments between Points 
	### considered indepentent of the interval logic.
	##################################################				
	def iterSegments(self,a=0,b=None,slicing=BY_INDEX,sortPoints=BY_TIMESTAMP,pointKey=(lambda x:x)):
		"""	get an iterator over segments -- that is from timestamp to timestamp (be it start or stop of any interval)
			timestampKey defines how the timestamps will be sorted (default is itemgetter(1) -- the index in the sequence, not the logical timestamp )
		"""

		### getting the key element for sorting the point list
		if sortPoints == BY_TIMESTAMP:
			logging.debug("sorting BY_TIMESTAMP")
			getter=itemgetter(0)
		elif sortPoints == BY_INDEX: 
			logging.debug("sorting BY_INDEX")
			getter=itemgetter(1)
		else:
			raise ValueError("invalid value for parameter sortpoints %s" % sortpoints)	

		pointsortKey= lambda x : pointKey(getter(x))

		plist = []		## will be filled with pairs: (<timestamp>,<index>)
		
		if slicing == BY_INDEX:
			logging.debug("slicing BY_INDEX")

			if b == None:		b = len(self.seq)
			for ts,idx in self.pointIdxByTS.iteritems():
				#logging.debug("iterSegments(%d,%d): ts,idx=(%s,%d)" % (a,b,ts,idx) )
				#print ( "testing" + str((ts,idx)) )
				if a <= idx and idx <= b: 	
					#print "appendit"
					plist.append((ts,idx))
			

			#for p in plist:		print ("%s %s" % (p,pointsortKey(p)))
			plist.sort(key=pointsortKey)
			
			#print "sorted plist:" + str(plist)
			for ts,idx in plist:
				logging.debug("sortedPIT:%s(%s)/%d" % (ts,str(pointKey(ts)),idx))
			return ASeqSegmentIter(self,plist, (TS_INPOINT,a),(TS_OUTPOINT,b), )

		elif slicing == BY_TIMESTAMP:
			logging.debug("slicing BY_TIMESTAMP")
			for ts,idx in self.pointIdxByTS.iteritems():
				if a <= timestampKey(ts) and timestampKey(ts) <= b:
					plist.append((ts,idx))
									
			plist.sort(key==pointsortKey)
			for ts,idx in plist:
				logging.debug("PIT:%s(%f)/%d" % (ts,pointKey(ts),idx))

			return ASeqSegmentIter(self,plist,(a,pointIdxByTS[a]),(b,pointIdxByTS[b]))

		else:
			raise ValueError("invalid value for parameter slicing %s" % slicing)

	def getPointsByIdx(self,idx):
		""" Return all Points in Time (PITs) that refer to the position idx in the sequence data """
		if idx in self.pointTSByIdx:
			return self.pointTSByIdx[idx]		### a list of timestamps, which identify PITs referring to that idx
		else:
			return []

	def getTSforIdx(self,idx,direct='LOW'):
		offset = 0
		#direction = 0
		newidx = idx
		#print("getTSforIdx: %d" % idx)
		#a,b = max(0,idx-30) , min(len(aseq),idx+30)
		timestampsAtNewIdx = self.getPointsByIdx(newidx)
		#print "%d: %s" % (newidx,timestampsAtNewIdx)
		while timestampsAtNewIdx == []:
			#print "%d: %s" % (newidx,timestampsAtNewIdx)
			offset += 1
			newidx = idx + alterInc(offset)
			#print "blubb " , newidx
			if newidx < 0:
#				print "True1"
				reachedStart = True

				### if we reached the start of the sequence the alternating ing search scheme has to be changed
				### this is done here . . .
				logging.debug("makeOffsetTS: reached the start")
				#offset *= -1		### don't flip it --- its positive anyway
				offset = offset/2 + 1

				newidx = idx + offset
				#logging.debug("makeOffsetTS: checking newindex/offset: %d/%d" % (newidx,offset))
				while self.getPointsByIdx(newidx) == []:
					offset = offset+1		## search in positive direction
					#offset /= 2
					newidx = idx + offset
					if newidx > len(self):
						raise ValueError("no timestamp found to derive index-based interpolation timestamp.")
					#logging.debug("makeOffsetTS: checking newindex/offset: %d/%d" % (newidx,offset))
				break
			if newidx > len(self):
#				print "True2"
				reachedEnd = True
				### . . . and here similarly for the case that the end is reached
				logging.debug("makeOffsetTS: reached the end")
				offset = -offset/2 ### flip the offset (for search at the other end)
#				print offset
				newidx = idx + offset
#				print newidx
				logging.debug("makeOffsetTS: checking newindex/offset: %d/%d" % (newidx,offset))
				while self.getPointsByIdx(newidx) == []:
					offset -= 1		## search in positive direction
					#offset /= 2
					newidx = idx + offset
					if newidx < 0:
						raise ValueError("no timestamp found to derive index-based interpolation timestamp.")
					logging.debug("makeOffsetTS: checking newindex/offset: %d/%d" % (newidx,offset))
				break
			timestampsAtNewIdx = self.getPointsByIdx(newidx)
			#logging.debug("makeOffsetTS: checking newindex/offset: %d/%d" % (newidx,offset))


		ts = self.getPointsByIdx(newidx)
		ts.sort(key=keyPremiereTSoffset)

		if newidx < idx:
			### the reference position is to the 'left'
			#then we refer to the biggest timestamp at that position/index
			newTS = ts[-1]
		elif newidx > idx:
			### to the right; we take tha smallest
			newTS = ts[0]
		else:
			if direct == 'LOW':
				newTS = ts[0]
			elif direct == 'HIGH':
				newTS = ts[-1]
			else:
				raise ValueError("getTSforIdx: invalid direction indication: %s" % direct)

		if newidx != idx:
			if '+' in newTS:
				newTS,xxxxxx,tsoffset = newTS.partition('+')
				newTS += "%+05d" % ((idx-newidx) + int(tsoffset))
			elif '-' in newTS:
				newTS,xxxxxx,tsoffset = newTS.partition('-')
				newTS += "%+05d" % ((idx-newidx) - int(tsoffset))
			else:
				### it is not an offset timestamp
				newTS += "%+05d" % (idx-newidx)

		logging.debug("makeOffsetTS: new timestamp %s (based on idx %d and timestamps %s)" % (newTS,newidx,ts))

		return newTS

	##################################################
	### Modifying sequence data without referring to intervals and Points in time
	### (internal indexes may have to be adapted by these methods of cource)
	##################################################				

	def removePartSeq(self,a,b):
		logging.debug("removePartSeq: %s" % str((a,b)))
		#logging.debug("removePartSeq:%s" % str(self.pointTSByIdx))

		### iterate all indexes of the deleted part
		for i in range(a,b):
			### safe timestamps at old idx i
			### if there are any
			if i in self.pointTSByIdx:
				timestamps = self.pointTSByIdx[i]
				del self.pointTSByIdx[i] 						### remove data from the old index
				if a in self.pointTSByIdx: 
					self.pointTSByIdx[a] += timestamps	### move the TSs from within the deleted area to the start index
				else:
					self.pointTSByIdx[a] = timestamps

				for ts in timestamps:
					self.pointIdxByTS[ts] = a					### adapt the indexes of each moved timestamp
				
		### iterate all indexes of the part behind the deleted part
		delta = (b - a)
		for i in range(b,len(self.seq)+1):
			if i in self.pointTSByIdx:
				timestamps = self.pointTSByIdx[i]
				del self.pointTSByIdx[i]

				if (i-delta) in self.pointTSByIdx:
					self.pointTSByIdx[i-delta] += timestamps
				else:
					self.pointTSByIdx[i-delta] = timestamps
					
				for ts in timestamps:
					self.pointIdxByTS[ts] = i-delta	
		#logging.debug("moved timestamps to %d: %s" % (i-delta,str(timestamps)))
		#logging.debug("new index for timestamp %s: %d" % (ts,i-delta))

		self.seq = self.seq[:a] + self.seq[b:]
		
		#logging.debug("removePartSeq:%s" % str(self.pointTSByIdx))
		############ old implementation working without        pointTSByIdx
		#		for timestamp,index in self.pointIdxByTS.iteritems():
		#			if index > a:			## index points to somewhere in or behind the removed part
		#				#logging.debug("ASeq:removePartSeq(%d,%d):pointMoves (%s,%d)" % (a,b,point,index))
		#
		#				if index <= b:		## index points to somewhere in the removed part
		#					self.pointIdxByTS[timestamp] = a		# bent it to the start of the removed part
		#					
		#				else:				### .. points to somewhere behind the removed part
		#					self.pointIdxByTS[timestamp]  -= (b - a)  	# deminish it by the size of the removed part
		#					newidx = self.pointIdxByTS[timestamp]		
	

	def insertPartSeq(self, insertidx, seq):
		delta = len(seq)
		### runs along decreasing order
		for i in range(len(self.seq),insertindex):
			timestamps = self.pointTSByIdx[i]

			self.pointTSByIdx[i+delta] += timestamps
			del self.pointTSByIdx[i]
			
			for ts in timestamps:
				self.pointIdxByTS[timestamp] = i+delta	
		self.seq.insert(insertidx,seq)

		############ old implementation working without        pointTSByIdx
		#		for timestamp,insertindex in self.pointIdxByTS.iteritems():
		#			if index > insertidx:	## index points to somewhere in or behind new part
		#				self.pointIdxByTS[timestamp]  += (b - a)  	# increase it by the size of the removed part
		

	def append(self,seq):
		self.seq += seq
		
	def checkConsistent(self):
		#self.intervalsByID = {}
		#self.intervalIDorder = []
		#self.intervalsByStart = defaultdict(list)
		#self.intervalsByStop = defaultdict(list)

		#self.seq = sequence
		#self.pointIdxByTS = {}
		#self.pointTSByIdx = defaultdict(list)

		
		print "ASeq:checking consistency"


		###           ###
		### INTERVALS ###
		###           ###

		### Interval ID order 
		for iid in self.intervalIDorder:
			if iid not in self.intervalsByID:
				raise ValueError("Inconsistency intervalIDorder/intervalsByID:" + iid )
			
		###	
		### Intervals BY START
		for startTS, IIDs in self.intervalsByStart.iteritems():
			for iid in IIDs:
				if iid not in self.intervalsByID:
					raise ValueError("Inconsistency intervalsByStart/intervalsByID:" + iid)
				else:
					a,b = self.intervalsByID[iid]
					print "a,b:" + str((a,b))
					if a != startTS:
						raise ValueError("Inconsistency intervalsByStart/intervalsByID: %s %s!=%s" % (iid,startTS,a))
		
		###	
		### intervals BY STOP
		for stopTS, IIDs in self.intervalsByStop.iteritems():
			for iid in IIDs:
				if iid not in  self.intervalsByID:
					raise ValueError("Inconsistency intervalsByStop/intervalsByID:" + iid)
				else:
					a,b = self.intervalsByID[iid]
					print ((a,b))
					if b != stopTS:
						raise ValueError("Inconsistency intervalsByStop/intervalsByID: %s %s != %s" % (iid,stopTS,b))

		###
		### intervals BY ID
		for iid,(startTS,stopTS) in self.intervalsByID.iteritems():
			### interval id order
			if iid not in self.intervalIDorder:
				raise ValueError("Inconsistency intervalsByID/intervalIDorder:" + iid )


			### intervals BY START_TS
			if startTS not in self.intervalsByStart:
				raise ValueError("Inconsistency intervalsByID/intervalsByStart:" + startTS )
			else:
				if iid not in self.intervalsByStart[startTS]:
					raise ValueError("Inconsistency intervalsByID/intervalsByStart: %s not in %s (intervalsByStart[%s])" % (iid,self.intervalsByStart[startTS],startTS))

			### intervals BY STOP_TS						
			if stopTS not in self.intervalsByStop:
				raise ValueError("Inconsistency intervalsByID/intervalsByStop:" + stopTS )
			else:
				if iid not in self.intervalsByStop[stopTS]:
					raise ValueError("Inconsistency intervalsByID/intervalsByStop: %s not in %s (intervalsByStop[%s])" % (iid,self.intervalsByStart[stopTS],stopTS))

			if startTS not in self.pointIdxByTS:
				raise ValueError("Inconsistency intervalsByID/pointIdxByTS:" + startTS + ' (startTS)')				
				
			if stopTS not in self.pointIdxByTS:
				raise ValueError("Inconsistency intervalsByID/pointIdxByTS:" + stopTS  + ' (stopTS)')


		###
		### INDEXES / TIMESTAMPS
		###

				
				
		for ts,idx in self.pointIdxByTS.iteritems():
			if idx not in self.pointTSByIdx:
				raise ValueError("Inconsistency IDX/TS:" + ts)
			else:
				if ts not in self.pointTSByIdx[idx]:
					raise ValueError("Inconcistency IDX/TS: %d %s!=%s" % (idx,ts,self.pointTSByIdx[idx]))
					
			if idx < 0 or len(self.seq)+1 < idx :
				raise ValueError("inconsistent lenght/idx %d;%d" % (len(self.seq),idx)) 
					
			
		allTSs = []	
				
		for idx,TSs in self.pointTSByIdx.iteritems():
			for ts in TSs:
				if ts not in self.pointIdxByTS:
					raise ValueError("Inconsistency TS/IDX:" + str(idx))
				else:
					if idx != self.pointIdxByTS[ts]:
						raise ValueError("Inconsistency TS/IDX: %d != %d (%s) " % (idx,self.pointIdxByTS[ts],ts))
						 
				
				
			allTSs += TSs
			
		if len(set(allTSs)) != len(allTSs):
			raise ValueError("duplicated elements")		
			
		return True
		
			


class ASeqIntervalIter(object):
	""" Iterates intervals in an annotated sequence
		This logic follows the annotated intervals as entities. Here, portions of text may be ommitted (when there is no interval) 
		or others may be retrieved multiply (when there are multiple intervals)"""
	def __init__(self,annosequence):
		self.idlist = annosequence.intervalIDorder
		self.aseq = annosequence
		logging.debug("new interval iterator: " % self.idlist)
		
	def next(self):
		### is this the end??
		if len(self.idlist) == 0:
			raise StopIteration
		
		
		### the current intervals id
		iid = self.idlist[0]
		#logging.debug("ASeqIntervalIter: interval iteration item: %s" % iid)
		### step the list
		self.idlist = self.idlist[1:]
		

		startTS, stopTS = self.aseq.intervalsByID[iid] 
		logging.debug("ASeqIntervalIter: %s Start/Stop TS: %s/%s" % (iid,startTS, stopTS))
		
		#startTS,stopTS = self.aseq.pointsByTS[startPID] , self.aseq.pointsByTS[stopPID]
		startIdx,stopIdx = self.aseq.pointIdxByTS[startTS] , self.aseq.pointIdxByTS[stopTS] 
		data = self.aseq.data[iid]
		subseq = self.aseq.seq[startIdx:stopIdx]
		return ((iid,startTS,startIdx,stopTS,stopIdx,data,subseq))
		
	def __iter__(self):
		return self




class ASeqSegmentIter(object):
	""" Iterates segments in an annotated sequence where a segment is defined as the portion of time lying between two subsequent points in time. 
		In other words, progressing along the timeline, whenever the configuration of intervals changes (one or mor intervals begin/end) at a point in time, 
		the former segment ends and a new one starts. This logic is usefull for printing consequtive text from the sequence while marking annotation
		intervals present or abscent."""
		
		
	def __init__(self,annosequence,plist,startPt,stopPt):
		self.plist = plist
		logging.debug("ASeqSegmentIter:__init__(...): plist=%s" % self.plist)
		#print "huhuhhu"
		#print plist
		self.aseq = annosequence
		self.startPt,self.stopPt = startPt,stopPt	## we begin in the beginning .. and stop in the end
		
		self.goOn = True
		
	def next(self):
		### is this the end??
		if not self.goOn:
			raise StopIteration
			
		if len(self.plist) == 0:
			currStop = self.stopPt		## last interval goes until the stop Point 
			self.goOn = False
		else:
			### step the list
			currStop = self.plist[0]
			self.plist = self.plist[1:]
		
		startTS,startIdx = self.startPt 
		stopTS,stopIdx = currStop

		subseq = self.aseq.seq[startIdx:stopIdx]

		self.startPt = currStop		## move the startPt one forward

		return ((startTS,startIdx,stopTS,stopIdx,subseq))

	def __iter__(self):
		return self




#########################################

	####################################
	### intervals and related operations
	####################################
#	def newSection(self,Name):
#		#self.sectionIdxByName[Name] = len(self.aseq)
#		self.sectionList.append((Name,len(self.aseq)))
#
#	def getSectionAB(self,Name):
#		a = None
#		b = None
#		for n,i in self.sectionList:
#			if a != None:
#				### then we found a in the last round, we set b and leave the loop
#				b = i
#				break
#			if n == Name:
#				a = i
#
#		if b == None:
#			### then a was found in the last round and there was no following section
#			### the section goes until the end
#			b = len(self.aseq)
#		return (a,b)
#
#
#	def getAllSections(self):
#		result = []
#
#		this,last = None,None
#		for n,i in self.sectionList:
#			this = i
#			th
#			if this != None and last != None:
#				result.append(())
#			last = this








#########################################




#print "****Test Text****"
#aseq = AnnotatedSequence("Test Text")
#print "****--anhang--****"
#aseq.appendAsInterval("ts1","ts3","--anhang--")
#print aseq
#print "****ts0/5,ts2,10****"
#aseq.addInterval("ts0","ts2",5,10)
#print aseq
#aseq.checkConsistent()
#print "****remove 9,11****"
#aseq.removePartSeq(0,10)
#print aseq
#aseq.checkConsistent()

#for x in aseq.iterSegments(): print x


