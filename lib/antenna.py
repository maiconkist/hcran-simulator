import math
import util


class Antenna(object):
    def __init__(self, pos, radius, grid):
        self._pos = pos
        self._radius = radius
        self._grid = grid
        self._radius = radius

        self._users = []

        self._bbu = util.nearest(self, grid.bbus)
        self._bbu.register(self)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        print("Cannot set pos for Antenna object")

    @property
    def radius(self):
        return self._radius

    def connect(self, user):
        if user not in self._users and util.dist(user, self) < self.radius:
            self._users.append(user)
            self._bbu.notify("op:connection", self, user)
            return True

        elif user in self._users:
            # already connected, nothing to do
            return True

        else:
            return False

    def disconnect(self, user):
        if user in self._users:
            self._users.remove(user)
            self._bbu.notify("op:disconnection", self, user)
            return True
        return False
