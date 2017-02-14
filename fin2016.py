from __future__ import print_function, division
from math import *
from copy import copy
from random import randint, sample
import matplotlib.pyplot as plt
import operator
import bisect

maxT = 0
degToAS = 3600
photoDict = {}

def index(a, x):
    'Locate the leftmost value exactly equal to x'
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    raise ValueError

def find_lt(a, x):
    'Find rightmost value less than x'
    i = bisect.bisect_left(a, x)
    if i:
        return a[i-1]
    raise ValueError

def find_le(a, x):
    'Find rightmost value less than or equal to x'
    i = bisect.bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError

def find_gt(a, x):
    'Find leftmost value greater than x'
    i = bisect.bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def find_ge(a, x):
    'Find leftmost item greater than or equal to x'
    i = bisect.bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

class Satellite(object):
	def __init__(self, lat, long, v, w, d):
		self.lat = lat
		self.long = long
		self.v = v
		self.w = w
		self.d = d
		self.cameraLat = 0
		self.camDirection = (1, 0)
		self.cameraLong = 0

	def tryMove(self, numTurns):
		lat = self.lat
		long = self.long
		v = self.v
		for i in range(numTurns):
			(lat, long, v) = self.tryMoveSingle(lat, long, v)
		return (lat, long, v)

	def tryMoveSingle(self, cLat, cLong, cV):
		tentativeNewLat = cLat + cV
		if tentativeNewLat > 90*degToAS: # (90deg)
			nLat = 180*degToAS - tentativeNewLat
			nLong = -180*degToAS + cLong - 15
			nV = -cV
		elif tentativeNewLat < -90*degToAS:
			nLat = -180*degToAS - tentativeNewLat
			nLong = -180*degToAS + cLong - 15
			nV = -cV
		else:
			nLat = tentativeNewLat
			nLong = cLong - 15
			nV = cV
		if nLong < -648000:
			nLong = 1296000 + nLong
		elif nLong > 647999:
			nLong = -1296000 + nLong
		return (nLat, nLong, nV)

	def move(self):
		(nLat, nLong, nV) = self.tryMoveSingle(self.lat, self.long, self.v)
		self.lat = nLat
		self.long = nLong
		self.v = nV

	def moveCamera(self, dLat, dLong):
		self.canMoveCamera(dLat, dLong)
		self.cameraLat += dLat
		self.cameraLong += dLong

	def cameraPos(self, curLat, curLong):
		return (curLat + self.cameraLat, curLong + self.cameraLong)

	def canMoveCamera(self, dLat, dLong):
		if dLat > self.w or dLong > self.w:
			raise ValueError("Moving camera by more than allowed")
		if abs(self.cameraLat + dLat) > self.d or \
		   abs(self.cameraLong + dLong) > self.d:
		   raise ValueError("Camera is outside its range")

	def tryCanMoveCamera(self, dLat, dLong):
		try:
			self.canMoveCamera(dLat, dLong)
		except ValueError:
			return False
		return True



	def findImagesInRange(self, numTurns, photos):
		images = []
		cLat = self.lat
		cLong = self.long
		cV = self.v
		for t in range(numTurns):
			cPos = self.cameraPos(cLat, cLong)
			try:
				rangeLongImgs = (find_ge(longSortedKeys, cPos[1] - self.w*(t+1)),
								find_le(longSortedKeys, cPos[1] + self.w*(t+1)))
				rangeLatImgs = (find_ge(latSortedKeys, cPos[0] - self.w*(t+1)),
								find_le(latSortedKeys, cPos[0] + self.w*(t+1)))
			except ValueError:
				return []
			latImgs = latSorted[rangeLatImgs[0]:rangeLatImgs[1]]
			longImgs = longSorted[rangeLongImgs[0]:rangeLongImgs[1]]
			latImgsSet = set([i[2] for i in latImgs])
			longImgsSet = set([i[2] for i in longImgs])
			imgs = latImgsSet.intersection(longImgsSet)
			if len(imgs) > 0:
				for imgId in imgs:
					for i in latImgs:
						if i[2] == imgId:
							break
					fullImg = i
					coll = fullImg[3]
					if coll.isInRange:
						images.append((fullImg[0], fullImg[1], fullImg[3]))

		return images

	def takePhoto(self, col, lat, long, t):
		cPos = self.cameraPos()
		dCameraLat = lat - cPos[0]
		dCameraLong = long - cPos[1]
		self.moveCamera(dCameraLat, dCameraLong)
		col.takePhoto(lat, long, t)

	def randomMoveCam(self):
		cPos = self.cameraPos()
		dLat = self.w + 1
		dLong = 0
		while not self.tryCanMoveCamera(dLat, dLong):
			dLat = randint(-self.w, self.w)
			dLong = randint(-self.w, self.w)
			if abs(self.cameraLat + dLat) > self.d:
				dLat = -dLat
			if abs(self.cameraLong + dLong) > self.d:
				dLong = -dLong
		self.moveCamera(dLat, dLong)

latSorted = []
longSorted = []
photoId = 0

class Collection():
	def __init__(self, id, value, numPhotos, numRanges):
		self.id = id
		self.value = value
		self.numPhotos = numPhotos
		self.numRanges = numRanges
		self.ranges = []
		self.photos = {}
		self.remainingPhotos = 0
		self.totalPhotos = 0
		self.isInRange = False
		self.hasMoreRanges = True
		self.isCompleted = False

	def addPhoto(self, lat, long):
		if lat not in self.photos:
			self.photos[lat] = {}
		if long not in self.photos[lat]:
			self.photos[lat][long] = 0
		self.photos[lat][long] += 1
		# Save the photo in the global photo dictionary
		global photoDict
		if lat not in photoDict:
			photoDict[lat] = {}
		if long not in photoDict[lat]:
			photoDict[lat][long] = []
		photoDict[lat][long].append(self)
		global photoId
		latSorted.append((lat, long, photoId, self))
		longSorted.append((lat, long, photoId, self))
		photoId += 1
		self.remainingPhotos += 1
		self.totalPhotos += 1

	def addRange(self, tstart, tend):
		self.ranges.append([tstart, tend])
		# Sort by tstart
		self.ranges = sorted(self.ranges, key=lambda t: t[0])

	def takeTurn(self, t):
		"""
		Remove ranges which have passed and update the isInRange flag
		"""
		try:
			firstRange = self.ranges[0]
			while t > firstRange[1]:
				del self.ranges[0]
				firstRange = self.ranges[0]
		except IndexError: # No more ranges
			self.isInRange = False
			self.hasMoreRanges = False
			return
		if t > firstRange[0]:
			self.isInRange = True
		else:
			self.isInRange = False

	def takePhoto(self, lat, long, t):
		if not self.isInRange:
			raise ValueError("Collection not in range")
		if lat not in self.photos or \
			long not in self.photos[lat] or \
			self.photos[lat][long] == 0:
			raise ValueError("Photo does not exist in this collection")
		self.photos[lat][long] -= 1
		self.remainingPhotos -= 1
		global photoDict
		for i, coll in enumerate(photoDict[lat][long]):
			if coll.id == self.id:
				del photoDict[lat][long][i]
				if len(photoDict[lat][long]) == 0:
					del photoDict[lat][long]
				break

def simulate(satellites, collections):
	global photoDict, latSorted, longSorted, latSortedKeys, longSortedKeys
	# Sort global latSorted, longSorted
	latSorted.sort(key=lambda t: t[0])
	latSortedKeys = [a[0] for a in latSorted]
	longSorted.sort(key=lambda t: t[1])
	longSortedKeys = [a[1] for a in longSorted]
	score = 0
	T = 0
	while T < maxT:
		if T % 1000 == 0:
			print("Time %d out of %d" % (T, maxT))
		#print("sat 0: %f ; %f" % (satellites[0].lat/degToAS, satellites[0].long/degToAS))
		for sid, sat in enumerate(satellites):
			# Find images which are in range of this satellite,
			# Sort by value of the image, Take photo
			images = sat.findImagesInRange(1, photoDict)
			if len(images) > 0:
				print(len(images))
				imgScores = {}
				for img in images:
					imgScore = img[2].value / img[2].remainingPhotos
					imgScores[img] = imgScore
				bestImage = max(imgScores.iteritems(), key=operator.itemgetter(1))[0]
				sat.takePhoto(bestImage[2], bestImage[0], bestImage[1], T)
				print("Taken photo in collection %d from sat %d" % (bestImage[2].id, sid))
				if bestImage[2].remainingPhotos == 0:
					# Update score
					score += bestImage[2].value
					print("FINISHED collection %d - score %d" % (bestImage[2].id, score))
					del collections[bestImage[2].id]
			else:
				sat.randomMoveCam()
			sat.move()
		for col in collections:
			col.takeTurn(T)
		T += 1
	return score

def parse_input(fname):
	with open(fname, 'r') as fh:
		global maxT
		maxT = int(fh.readline())
		# Satellites
		numSat = int(fh.readline())
		satellites = []
		for i in range(numSat):
			satProps = fh.readline().split(' ')
			lat = int(satProps[0])
			long = int(satProps[1])
			v = int(satProps[2])
			w = int(satProps[3])
			d = int(satProps[4])
			satellites.append(Satellite(lat, long, v, w, d))
		# Image collections
		numCollections = int(fh.readline())
		collections = []
		for i in range(numCollections):
			collectionProps = fh.readline().split(' ')
			val = int(collectionProps[0])
			numPhotos = int(collectionProps[1])
			numRanges = int(collectionProps[2])
			collection = Collection(i, val, numPhotos, numRanges)
			# Photo locations
			for j in range(numPhotos):
				photoLoc = fh.readline().split(' ')
				lat = int(photoLoc[0])
				long = int(photoLoc[1])
				collection.addPhoto(lat, long)
			for j in range(numRanges):
				photoRange = fh.readline().split(' ')
				tstart = int(photoLoc[0])
				tend = int(photoLoc[1])
				collection.addRange(tstart, tend)
			collections.append(collection)

	return {
		'satellites': satellites,
		'collections': collections
	}


if __name__ == "__main__":
	fnames = ["constellation.in", "forever_alone.in", "overlap.in", "weekend.in"]
	finalScore = 0
	fname = fnames[0]
	params = parse_input("/home/gmeanti/source/hashcode/final_round_2016.in/" + fname)
	tot_images = 0
	for coll in params['collections']:
		tot_images += coll.totalPhotos
	print('total images %d in %d collections' % (tot_images, len(params['collections'])))
	finalScore += simulate(**params)
	print("FINAL SCORE %d" % finalScore)

