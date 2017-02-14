from __future__ import print_function, division
from math import *
from copy import copy
from random import randint, sample
import matplotlib.pyplot as plt

r = None
c = None
maxLoad = None
prodObjs = None

score = 0
T = 0
maxT = 0

global finishedTurnsDistrib
finishedTurnsDistrib = []

def addIfNotExists(key, val, dict_):
	if key in dict_:
		dict_[key] += val
	else:
		dict_[key] = val

def distanceCompare(pos1, pos2):
	return (pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2

def distanceTurns(pos1, pos2):
	return int(ceil(sqrt(distanceCompare(pos1, pos2))))


class Product(object):
	def __init__(self, id, weight):
		self.id = id
		self.weight = weight


class Warehouse(object):
	def __init__(self, id, pos, products):
		self.id = id
		self.pos = pos
		self.products = products
		self.futureProducts = copy(products)

	def maxAvailProducts(self, reqProducts):
		retProducts = {}
		for pid in reqProducts:
			quantity = min(reqProducts[pid], self.futureProducts[pid])
			retProducts[pid] = quantity
		return retProducts


	def preTakeProducts(self, products):
		if not self.hasProducts(products):
			raise ValueError("Not enough products")

		for pid in products:
			self.futureProducts[pid] -= products[pid]

	def takeProducts(self, products):
		for pid in products:
			if self.products[pid] < products[pid]:
				raise ValueError("Not enough products")
			self.products[pid] -= products[pid]

	def hasProducts(self, products):
		for pid in products:
			if not self.hasProduct(pid, products[pid]):
				return False
		return True

	def hasProduct(self, pid, quantity):
		if self.futureProducts[pid] < quantity:
			return False
		return True


class Order(object):
	finishedOrders = {}

	def __init__(self, id, pos, products):
		self.id = id
		self.pos = pos
		self.products = products
		self.futureProducts = copy(products)
		self.finished = False

	def preFinished(self):
		for pid in self.futureProducts:
			if self.futureProducts[pid] > 0:
				return False
		return True

	def preDeliverProducts(self, products):
		self.checkProductsCompatible(products, self.futureProducts)
		for pid in products:
			self.futureProducts[pid] -= products[pid]

	def deliverProducts(self, products):
		self.checkProductsCompatible(products, self.products)
		isFinished = True
		for pid in products:
			self.products[pid] -= products[pid]
			if self.products[pid] > 0:
				isFinished = False
		self.finished = isFinished

	def checkProductsCompatible(self, deliverProducts, selfProducts):
		"""Check whether order and products are compatible 
			(order must contain products)
		"""
		for pid in deliverProducts:
			if pid not in selfProducts:
				raise ValueError("Products are not compatible with the order")
			if deliverProducts[pid] > selfProducts:
				raise ValueError("Products has too many items for this order")
		return True


class Drone(object):

	def __init__(self, pos):
		self.pos = pos
		self.products = {}
		self.dest = None
		self.destCommand = None
		self.destProducts = None
		self.curOrders = None
		self.lastOrder = None
		self.loadWeight = 0
		self.movementTurns = 0

	def busy(self):
		return self.dest is not None

	def leftWeight(self):
		return maxLoad - self.loadWeight

	def setLoad(self, warehouse, products, orders):
		for p in products:
			if not self.canTakeProducts(warehouse, p):
				raise ValueError("A constraint is violated: cannot load products")

		self.dest = warehouse
		self.destCommand = "LOAD"
		self.destProducts = products
		self.movementTurns = 0
		self.curOrders = orders
		for i in range(len(orders)):
			orders[i].preDeliverProducts(products[i])

	def wait(self):
		pass

	def setDeliver(self, orders, products):
		"""
		orders: list of orders
		products: list of dictionary of products (1 dict per order)
		"""
		self.dest = orders[0]
		self.destCommand = "DELIVER"
		self.destProducts = products
		self.movementTurns = 0

	def canTakeProducts(self, warehouse, products):
		weight = self.loadWeight
		for pid in products:
			#if not warehouse.hasProduct(pid, products[pid]):
			#	return False
			weight += prodObjs[pid].weight * products[pid]
			if weight > maxLoad:
				return False
		return True

	def doTurn(self):
		if self.movementTurns == distanceTurns(self.pos, self.dest.pos):
			# We have arrived at the destination
			if self.destCommand == "LOAD":
				#print("LOADED")
				for p in self.destProducts:
					self.dest.takeProducts(p)
					for pid in p:
						addIfNotExists(pid, p[pid], self.products)
						self.loadWeight += prodObjs[pid].weight * p[pid]
				self.pos = self.dest.pos
				self.dest = None
				self.destCommand = None
			elif self.destCommand == "DELIVER":
				#print("DELIVERING")
				order = self.curOrders[0]
				order.deliverProducts(self.destProducts[0])
				# Unload weight
				for pid in self.destProducts[0]:
					self.products[pid] -= self.destProducts[0][pid]
					self.loadWeight -= prodObjs[pid].weight * \
						self.destProducts[0][pid]
				# Check finished and update score:
				if order.finished and order.id not in Order.finishedOrders:
					global score
					score += int(ceil((maxT - T) / maxT * 100))
					Order.finishedOrders[order.id] = 1
					finishedTurnsDistrib.append(T)
				self.lastOrder = self.curOrders[0]
				self.pos = self.dest.pos
				del self.destProducts[0]
				del self.curOrders[0]
				#print("Current order length %d" % (len(self.curOrders)))
				if len(self.curOrders) > 0:
					self.dest = self.curOrders[0]
					#print("new destination %s - cur pos %s" % (self.dest.pos, self.pos))
				else:
					self.dest = None
					self.destCommand = None
					self.curOrders = None
				#print("Busy drone %s" % (self.busy()))
				self.movementTurns = 0
		else:
			self.movementTurns += 1


def chooseOrder(orderIs, orderObjs, drone):
	# Minimum distance
	min_v = sorted(orderIs, key=lambda t: distanceCompare(drone.pos, orderObjs[t].pos))
	return min_v
	# Random
	#return sample(orderIs, min(20, len(orderIs)))


def simulate(r, c, maxT, maxLoad, products, warehouses, orders, drones):
	# Initial params
	oids_size = 5
	incompleteOrders = range(0, len(orders))
	global score, T, finishedTurnsDistrib, actualOidsSize
	score = 0
	T = 0
	finishedTurnsDistrib = []
	actualOidsSize = []
	Order.finishedOrders = {}

	try:
		while T < maxT:
			#print("T %d/%d" % (T, maxT))
			for drone in drones:
				if not drone.busy():
					if drone.curOrders is not None:
						#print("COMMAND DELIVER")
						# Means we just loaded
						drone.setDeliver(drone.curOrders, drone.destProducts)
					else:
						if drone.lastOrder is None:
							oids = chooseOrder(incompleteOrders, orders, drone)[0:oids_size]
						else:
							# Pick an incomplete order
							if len(Order.finishedOrders.keys()) == len(orders):
								raise StopIteration()
							if len(incompleteOrders) == 0:
								drone.wait()
								continue
							else:
								ordered_oid = chooseOrder(incompleteOrders, orders, drone)
								oids = ordered_oid[0:oids_size]
							
						# Pick a warehouse with the products
						whouseScores = {}
						for wi in range(len(warehouses)): whouseScores[wi] = 0
						for wi, whouse in enumerate(warehouses):
							whouseDist = distanceCompare(drone.pos, whouse.pos) + \
										 distanceCompare(whouse.pos, orders[oids[0]].pos)
							leftWeight = drone.leftWeight()
							for oid in oids:
								if whouse.hasProducts(orders[oid].futureProducts):
									whouseScores[wi] += 1000000 / whouseDist
								else:
									maxAvailProducts = \
										whouse.maxAvailProducts(orders[oid].futureProducts)
									numAvail = sum(maxAvailProducts.values())
									whouseScores[wi] = numAvail * 1000 / whouseDist
						whouse = warehouses[max(whouseScores, key=whouseScores.get)]
						# Which products to load?
						finalOids = []
						leftWeight = drone.leftWeight()
						loadProducts = []
						for oid in oids:
							loadPs = whouse.maxAvailProducts(orders[oid].futureProducts)
							canTakeAnything = False
							for pid in loadPs:
								weightAvail = int(floor(leftWeight / prodObjs[pid].weight))
								# if weightAvail < loadPs[pid]:
								# 	print("Not enough load weight")
								# else:
								# 	print("Not enough warehouse capacity")
								loadPs[pid] = min(loadPs[pid], weightAvail)
								if loadPs[pid] > 0: canTakeAnything = True
								leftWeight -= loadPs[pid] * prodObjs[pid].weight
							if canTakeAnything == True:
								finalOids.append(oid)
								whouse.preTakeProducts(loadPs)
								loadProducts.append(loadPs)
							if leftWeight <= 0:
								break
						if len(finalOids) == 0:
							print("HELP")
							finalOids = [oids[0]]
							loadProducts.append({})
						actualOidsSize.append(len(finalOids))
						finalOrders = [orders[i] for i in finalOids]
						#print("Loading orders %s" % (finalOids))
						drone.setLoad(whouse, loadProducts, finalOrders)
						for order in finalOrders:
							if order.preFinished():
								# Ensure we avoid sending drones to deliver the same stuff.
								for i, o in enumerate(incompleteOrders):
									if o == order.id:
										del incompleteOrders[i]
										break

				drone.doTurn()
			T += 1
	except StopIteration as e:
		print("No More Orders at time %d" % T)
	print("SCORE: %d" % score)
	return score


def parse_input(fname):
	with open(fname, 'r') as fh:
		params = fh.readline().split(' ')
		global r
		r = int(params[0])
		global c
		c = int(params[1])
		D = int(params[2])
		global maxT
		maxT = int(params[3])
		global maxLoad
		maxLoad = int(params[4])

		global prodObjs
		prodObjs = {}
		warehouseObjs = []
		orderObjs = []
		droneObjs = []

		# Products
		pTypes = int(fh.readline())
		productTypes = {}
		prods = fh.readline().split(' ')
		for pid in range(len(prods)):
			prodObjs[pid] = Product(pid, int(prods[pid]))

		# Warehouses
		nWarehouses = int(fh.readline())
		for wid in range(nWarehouses):
			pos = fh.readline().split(' ')
			pos = [int(pos[0]), int(pos[1])]
			prodsInW = fh.readline().split(' ')
			products = {}
			for pid in range(len(prodsInW)):
				products[pid] = int(prodsInW[pid])
			warehouse = Warehouse(wid, pos, products)
			warehouseObjs.append(warehouse)

		# Orders
		nOrders = int(fh.readline())
		for oid in range(nOrders):
			pos = fh.readline().split(' ')
			pos = [int(pos[0]), int(pos[1])]
			nItems = int(fh.readline())
			items = fh.readline().split(' ')
			products = {}
			for spid in items:
				pid = int(spid)
				if pid in products:
					products[pid] += 1
				else:
					products[pid] = 1
			order = Order(oid, pos, products)
			orderObjs.append(order)

	# Drones
	for did in range(D):
		droneObjs.append(Drone([0,0]))

	return {
		'products': prodObjs, 
		'warehouses': warehouseObjs, 
		'orders': orderObjs, 
		'drones': droneObjs,
		'r': r,
		'c': c,
		'maxT': maxT,
		'maxLoad': maxLoad
	}


if __name__ == "__main__":
	fnames = ["mother_of_all_warehouses.in", "busy_day.in", "redundancy.in"]
	finalScore = 0
	for fname in fnames:
		params = parse_input("/home/gmeanti/source/hashcode/qualification_round_2016.in/" + fname)
		print("time %d - %dx%d grid - %d products %d drones %d warehouses %d orders" % 
			(params['maxT'], params['r'], params['c'], len(params['products'].keys()), 
			 len(params['drones']), len(params['warehouses']), len(params['orders'])))

		finalScore += simulate(**params)
		fig, ax = plt.subplots()
		ax.hist(finishedTurnsDistrib)
		ax.set_title("Finished turns")
		ax.set_xlabel("turn")
		ax.set_ylabel("number of finished orders")
		fig, ax = plt.subplots()
		ax.hist(actualOidsSize)
	plt.show()
	print("FINAL SCORE %d" % finalScore)

