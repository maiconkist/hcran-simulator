import scipy


def connectability(ue, cur_antenna, next_antenna):
	import math
	def dist(p1, p2):
		return math.sqrt(abs(p1[0] - p2[0]) ** 2 + abs(p1[1] - p2[1]) ** 2)

	d1 = dist(ue._pos, cur_antenna._pos)  if cur_antenna  != None   else 999999
	d2 = dist(ue._pos, next_antenna._pos) if next_antenna != None else 999999

	if d1 < d2 and d1 <= cur_antenna._radius:
		return None
	elif d2 <= next_antenna._radius:
		return next_antenna
	else:
		return None

class User(object):

	def __init__(self, pos, moving_strategy, grid):
		self._pos = pos
		self._moving_strategy = moving_strategy
		self._grid = grid

		self._connected_antenna = None


	def move(self, step):
		self._pos = self._moving_strategy( self._pos )


	def stablish_connection(self, new_antenna):
		# if connection to new antenna is ok
		if new_antenna.connect( self ):
			# disconnect from actual antenna and update
			if self._connected_antenna != None:
				self._connected_antenna.disconnect(self)
			self._connected_antenna = new_antenna
		

	def update(self):
		antenna = self._grid.antenna_tree
		dist_list, idx_list = antenna.query( [ self._pos, ], len(antenna.data) )

		for d, idx in zip(dist_list[0], idx_list[0]):
			if connectability(self, self._connected_antenna, self._grid._antenna[ idx ]):
				if self.stablish_connection( self._grid._antenna[ idx ] ):
					break



if __name__ == '__main__':
	pass
