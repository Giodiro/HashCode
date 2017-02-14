from __future__ import print_function, division
from math import *
from copy import copy
from random import randint, sample
import random
import matplotlib.pyplot as plt
import operator
from collections import deque, OrderedDict
import bisect


def isInRect(x, tl, br):
	if x[0] < tl[0] or x[1] < tl[1]:
		return False
	if x[0] > br[0] or x[1] > br[1]:
		return False
	return True

def satisfiesUpperBound(tl, br, H):
	return (br[0] - tl[0]) * (br[1] - tl[1]) <= H

def satisfiesLowerBound(tl, br, L, grid):
	numT = 0
	numC = 0
	for x in range(tl[0], br[0]):
		for y in range(tl[1], br[1]):
			if grid[x][y] == 'T':
				numT += 1
			else:
				numC += 1
			if numT >= L and numC >= L:
				return True
	return False


def tryGrowSlice(tl, L, H, grid):
	br = copy(tl)
	coord = 0
	edgeCoords = set()
	while True:
		# Alternate coordinates
		coord = 1 - coord
		if coord in edgeCoords:
			continue
		br[coord] += 1
		try:
			grid[br[0]][br[1]]
		except IndexError:
			br[coord] -= 1
			edgeCoords.add(coord)
			if len(edgeCoords) == 2:
				break
		if not satisfiesUpperBound(tl, br, H):
			br[coord] -= 1
			break
	if satisfiesLowerBound(tl, br, L, grid):
		return br
	return None


def calcScore(slices):
	sliceArea = 0
	for s in slices:
		sliceArea += (s[1][0] - s[0][0]) * (s[1][1] - s[0][1])
	return sliceArea

def simulate(rows, cols, L, H, grid):
	slices = []
	sliceGrid = []
	for r in range(rows):
		sliceGrid.append([])
		for c in range(cols):
			sliceGrid[-1].append(0)
	startingPositions = OrderedDict({(0, 0): 1})
	evaledPositions = set()
	while len(startingPositions) > 0:
		pos = startingPositions.popitem(last=False)[0]
		evaledPositions.add(pos)
		slc = tryGrowSlice(list(pos), L, H, grid)
		added = False
		if slc is not None:
			overlaps = False
			for x in range(pos[0], slc[0]):
				for y in range(pos[1], slc[1]):
					if sliceGrid[x][y] == 1:
						overlaps = True
			if not overlaps:
				slices.append((pos, slc))
				print("Appending slice [%d %d], [%d %d] of size %d. tot %d slices" % 
					(pos[0], pos[1], slc[0], slc[1], 
					(slc[0] - pos[0]) * (slc[1] - pos[1]), len(slices)))
				for x in range(pos[0], slc[0]):
					for y in range(pos[1], slc[1]):
						sliceGrid[x][y] = 1
				for posistion in startingPositions.keys():
					if isInRect(posistion, pos, slc):
						del startingPositions[posistion]
				add1 = (pos[0], slc[1]+1)
				add2 = (slc[0]+1, pos[1])
				if add1 not in evaledPositions:
					startingPositions[add1] = 1
				if add2 not in evaledPositions:
					startingPositions[add2] = 1
				added = True
		if not added:
			add1 = (pos[0]+1, pos[1])
			add2 = (pos[0], pos[1]+1)
			add3 = (pos[0]+1, pos[1]+1)
			if add1[0] < rows and add1 not in evaledPositions:
				startingPositions[add1] = 1
			if add2[1] < cols and add2 not in evaledPositions:
				startingPositions[add2] = 1
			if add3[0] < rows and add3[1] < cols and add3 not in evaledPositions:
				startingPositions[add3] = 1

	return calcScore(slices), slices

def writeOutput(fname, slices):
	with open(fname, 'w') as fh:
		fh.write("%d\n" % len(slices))
		for s in slices:
			fh.write("%d %d %d %d\n" % (s[0][0], s[0][1], s[1][0]-1, s[1][1]-1))

def parse_input(fname):
	with open(fname, 'r') as fh:
		params = fh.readline().split(' ')
		rows = int(params[0])
		cols = int(params[1])
		L = int(params[2])
		H = int(params[3])
		grid = []
		for r in range(rows):
			rowParams = fh.readline()
			grid.append([])
			for c in range(cols):
				grid[-1].append(rowParams[c])
	return {
		'rows': rows,
		'cols': cols,
		'L': L,
		'H': H,
		'grid': grid
	}

if __name__ == "__main__":
	fnames = ["big.in", "medium.in", "small.in", "example.in"]
	finalScore = 0
	fname = fnames[0]
	params = parse_input("/home/gmeanti/source/hashcode/practice/" + fname)
	(score, slices) = simulate(**params)
	writeOutput("pizza_%s_%d.out" % (fname, score), slices)
	print("FINAL SCORE %d" % score)

