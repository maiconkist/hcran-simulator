import math

class Antenna(object):
    def __init__(self, pos, radius, grid):
        self._pos = pos
        self._radius = radius
        self._grid = grid
        self._radius = radius

        self._users = []


    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        print("Cannot set pos for Antenna object" )

    @property
    def radius(self):
        return self._radius

    def connect(self, user):
        def dist(p1, p2):
            return math.sqrt(abs(p1[0] - p2[0]) ** 2 + abs(p1[1] - p2[1]) ** 2)

        if user not in self._users and dist(user.pos, self.pos) < self.radius:
            self._users.append( user )
            self._grid.logger.log("op:connection, antenna:" + str(self.pos) + ", user:" + str(user._id) + ", pos:" + str(user.pos))
            return True
        elif user in self._users:
            # already connected, nothing to do
            pass
        else:
            return False


    def disconnect(self, user):
        if user in self._users:
            self._users.remove( user )
            self._grid.logger.log("op:disconnection, antenna:" + str(self.pos) + ", user:" + str(user._id)+ ", pos:" + str(user.pos))

            return True
        return False
