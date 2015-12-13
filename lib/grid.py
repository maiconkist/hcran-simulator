from sorted_collection import *

import random
import scipy.spatial


class Grid(object):

	def __init__(self, size=(0,1000)):
		self._size = size


		self._user = []
		self._antenna = []
		self._antenna_tree = None

		self._initialized = 0


	def add_user(self, user ):
		self._user.append( user )


	def add_antenna(self, antenna):
		self._antenna.append( antenna )

	@property
	def logger(self):
		class log():
			@staticmethod
			def log(m):
				print m

		return log()


	def random_pos(self):
		x = random.randrange(self._size[0], self._size[1])
		y = random.randrange(self._size[0], self._size[1])
		return [x, y]


	@property
	def antenna_tree(self):
		return self._antenna_tree


	def init(self):
            	self._antenna_tree  = scipy.spatial.KDTree( [ a.pos for a in  self._antenna ] )


	def step(self, time):
		self.init()

		# move for 1 second (ue must perform operations)
		for ue in self._user:
			ue.move( time )
		# update ue (after performing movements )
		for ue in self._user:
			ue.update()
