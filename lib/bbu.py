class BBU(object):
    def __init__(self, pos, controller, grid):
        self._pos = pos
        self._grid = grid
        self._controller = controller

        self._antennas = []

        self._controller.register(self)

    @property
    def pos(self):
        """
        """
        return self._pos

    @property
    def antennas(self):
        """
        """
        return self._antennas

    def register(self, antenna):
        """
        @param antenna
        """
        self._antennas.append(antenna)

    def event(self, op, antenna, ue=None):
        """ Entry point for events in antennas.

        @param op_str Events from controller class
        @param antennas Antenna obj
        @param ue User obj
        """
        self._controller.event(op, antenna, ue)

    def update(self):
        """ Operations performed after UEs movement
        """
        pass

    def __str__(self):
        """
        """
        return str(self._pos)
