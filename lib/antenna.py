

class Antenna(object):
	def __init__(self, pos, radius, grid):
		self._pos = pos
		self._radius = radius
	
		self._grid = grid

		self._users = []


	@property
	def pos(self):
		return self._pos

	@pos.setter
	def pos(self, pos):
		print("Cannot set pos for Antenna object" )


	def connect(self, user):
		if user not in self._users:
			self._users.append( user )
			self._grid.logger.log('op:connection')
			return True
		else:
			return False


	def disconnect(self, user):
		if user in self._users:
			self._users.remove( user )
			self._grid.logger.log('op:disconnection')

			return True
		return False


if __name__ == '__main__':
	pass
