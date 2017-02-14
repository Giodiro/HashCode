from __future__ import print_function, division
from math import *
from copy import copy
from random import randint, sample
import random
import matplotlib.pyplot as plt
import operator
import bisect

#random.seed(1)

def inRange(x, a, b):
	return x >= a and x < b

class Pool():
	def __init__(self, id, nRows):
		self.id = id
		self.nRows = nRows
		self.servers = []

	def addServer(self, server):
		self.servers.append(server)

	def rowCapacities(self):
		rowCapacities = [0 for r in range(self.nRows)]
		for s in self.servers:
			rowCapacities[s.loc[0]] += s.capacity
		return rowCapacities

	def calcPoolScore(self):
		rowCapacities = self.rowCapacities()

		return sum(rowCapacities) - max(rowCapacities)

	def totalCapacity(self):
		rowCapacities = self.rowCapacities()
		return sum(rowCapacities)

	def rowCapacity(self, row):
		rowCapacities = self.rowCapacities()
		return rowCapacities[row]

	def wantRows(self):
		haveRows = set([s.loc[0] for s in self.servers])
		allRows = set(range(self.nRows))
		wantRows = allRows.difference(haveRows)
		if len(wantRows) > 0:
			return list(wantRows)
		rowScores = [0 for r in range(self.nRows)]
		for s in self.servers:
			rowScores[s.loc[0]] += s.capacity
		return sorted(range(self.nRows), key=lambda i: rowScores[i])[:5]


class Server():
	def __init__(self, id, size, capacity):
		self.size = size
		self.capacity = capacity
		self.loc = None
		self.pool = None
		self.id = id

	def isAssigned(self):
		return self.loc is not None

	def setLoc(self, row, slot):
		self.loc = [row, slot]

	def setPool(self, pool):
		self.pool = pool

	def __str__(self):
		if self.loc is not None:
			return "%d(%d)" % (self.loc[1], self.size)
		else:
			return "%d" % self.size
	def __repr__(self):
		if self.loc is not None:
			return "%d(%d)" % (self.loc[1], self.size)
		else:
			return "%d" % self.size


def simulate(servers, rows, slots, numPools, grid2):
	capServers = sorted(servers, key=lambda s: s.capacity/(s.size/2), reverse=True)
	print("Remaining servers: %s" % [s.capacity for s in capServers])

	serverGrid = []
	for r in range(rows):
		serverGrid.append([])
	# Insert the servers in the grid
	fullAddedServer = True
	passDir = 1
	addedServers = 0
	addedCapacity = 0
	while fullAddedServer:
		fullAddedServer = False
		if passDir > 0:
			rowRange = range(rows)
		else:
			rowRange = range(rows-1, -1, -1)
		for r in rowRange:
			row = grid2[r]
			si = 0
			addedServer = False
			try:
				while not addedServer:
					# Place the next server by capacity in the row
					server = capServers[si]
					for ri, _range in enumerate(row):
						if server.size <= _range[1] - _range[0]:
							server.setLoc(r, _range[0])
							row[ri][0] = _range[0] + server.size
							if row[ri][0] == row[ri][1]:
								del row[ri]
							del capServers[si]
							addedServer = True
							fullAddedServer = True
							serverGrid[r].append(server)
							addedServers += 1
							addedCapacity += server.capacity
							break
					si += 1
			except IndexError: # No more servers
				pass
		passDir = passDir*-1
	for r in range(rows):
		print("%2d:   %s" % (r, grid2[r]))
		#print("      %s" % sorted(serverGrid[r], key=lambda s: s.loc[1]))
	print("Remaining servers: %s" % [s.capacity for s in capServers])

	averageCapacity = addedCapacity / numPools
	averageRowCapacity = averageCapacity / rows

	pools = []
	# Place the servers into pools
	for pi in range(numPools):
		pools.append(Pool(pi, rows))
	passDir = 1
	while addedServers > 0:
		if passDir > 0:
			poolRange = range(numPools)
		else:
			poolRange = range(numPools - 1, -1, -1)

		for pi in poolRange:
			neededRows = pools[pi].wantRows()
			availableServers = sum([len(serverGrid[row]) for row in neededRows])
			if availableServers == 0:
				neededRows = sample(range(rows), rows)
			serverScores = {}
			for row in neededRows:
				rowScore = (averageRowCapacity - pools[pi].rowCapacity(row))
				for si in range(len(serverGrid[row])):
					score = rowScore + \
						    averageRowCapacity - (pools[pi].rowCapacity(row) + serverGrid[row][si].capacity)
					score += (averageCapacity - (pools[pi].totalCapacity() + serverGrid[row][si].capacity))
					serverScores[(row, si)] = score
			if len(serverScores) > 0:
				(row, si) = max(serverScores, key=serverScores.get)
				pools[pi].addServer(serverGrid[row][si])
				del serverGrid[row][si]
				addedServers -= 1

		passDir = passDir*-1
	# rowCapacities = []
	# for pool in pools:
	# 	rowCapacities.append(pool.totalCapacity())
	# fig, ax = plt.subplots()
	# ax.hist(rowCapacities, bins=numPools)
	# plt.show()


	scores = []
	for pool in pools:
		scores.append(pool.calcPoolScore())
		print("Pool %d score %f" % (pool.id, scores[-1]))
	return min(scores)






def parse_input(fname):
	with open(fname, 'r') as fh:
		stats = fh.readline().split(' ')
		rows = int(stats[0])
		slots = int(stats[1])
		unavail = int(stats[2])
		numPools = int(stats[3])
		numServers = int(stats[4])

		#grid = scipy.sparse.dok_matrix((rows, slots))
		grid2 = []
		for row in range(rows):
			grid2.append([[0, slots]])

		for i in range(unavail):
			unavailSlot = fh.readline().split(' ')
			r = int(unavailSlot[0])
			s = int(unavailSlot[1])
			#grid[r, s] = -1 # Unavailable
			row = grid2[r]
			for ri, _range in enumerate(row):
				if inRange(s, _range[0], _range[1]):
					row.insert(ri, [_range[0], s])
					row.insert(ri + 1, [s + 1, _range[1]])
					del row[ri + 2]
					break
			grid2[r] = row


		servers = []
		for i in range(numServers):
			serverProps = fh.readline().split(' ')
			size = int(serverProps[0])
			capacity = int(serverProps[1])
			servers.append(Server(i, size, capacity))
		return {
			'rows': rows,
			'slots': slots,
			'numPools': numPools,
			'servers': servers,
			#'grid': grid,
			'grid2': grid2
		}



if __name__ == "__main__":
	fnames = ["dc.in"]
	finalScore = 0
	fname = fnames[0]
	params = parse_input("/home/gmeanti/source/hashcode/qualification_round_2015.in/" + fname)
	finalScore += simulate(**params)
	print("FINAL SCORE %d" % finalScore)

