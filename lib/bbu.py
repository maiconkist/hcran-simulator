class BBU(object):
    def __init__(self, pos, controller, grid):
        self._pos = pos
        self._grid = grid
        self._controller = controller

        self._antennas = []

    @property
    def pos(self):
        return self._pos

    def register(self, antenna):
        """
        @param antenna
        """
        self._antennas.append(antenna)

    def event(self, op, antenna, ue):
        """ Entry point for events in antennas.

        @param op_str Events from controller class
        @param antennas Antenna obj
        @param ue User obj
        """
        self._controller.event(op, antenna, ue)

    def __str__(self):
        """
        """
        return str(self._pos)
