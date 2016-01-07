import util
import controller


class Antenna(object):
    def __init__(self, pos, radius, grid):
        self._pos = pos
        self._radius = radius
        self._grid = grid
        self._radius = radius

        self._ues = []

        # Register to the closest BBU
        self._bbu = util.nearest(self, grid.bbus)
        self._bbu.register(self)

    @property
    def pos(self):
        """
        """
        return self._pos

    @pos.setter
    def pos(self, pos):
        """
        """
        print("Cannot set pos for Antenna object")

    @property
    def radius(self):
        """
        """
        return self._radius

    @property
    def bbu(self):
        """
        """
        return self._bbu

    def connect(self, ue):
        """
        """
        if ue not in self._ues and util.dist(ue, self) < self.radius:
            self._ues.append(ue)
            self._bbu.event(controller.UE_CONNECT, self, ue)
            return True

        elif ue in self._ues:
            # already connected, nothing to do
            return True

        else:
            return False

    def disconnect(self, ue):
        """
        """
        if ue in self._ues:
            self._ues.remove(ue)
            self._bbu.event(controller.UE_DISCONNECT, self, ue)
            return True
        return False

    def __str__(self):
        return str(self.pos)
