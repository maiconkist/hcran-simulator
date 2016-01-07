UE_CONNECT = 0
UE_DISCONNECT = 1


class Controller(object):

    def __init__(self, grid):
        self._grid = grid

        self._ue_connected_map = {}
        self._ue_disconnected_map = {}

    def event(self, op, antenna, ue=None):
        """ Entry point for all event from the BBU
        @param op Operation code.
        @param op Operation code.
        """
        if op == UE_CONNECT:
            self.ue_connected(antenna, ue)
        elif op == UE_DISCONNECT:
            self.ue_disconnected(antenna, ue)
        else:
            pass

    def ue_connected(self, antenna, ue):
        """
        @param antenna Antenna obj.
        @param ue User obj.
        """
        self._ue_connected_map[ue] = antenna

        self._grid.logger.log("op:connection, user:" + str(ue) +
                              ", antenna:" + str(antenna))

        if ue in self._ue_disconnected_map:
            old_antenna = self._ue_disconnected_map[ue]

            if old_antenna.bbu != antenna.bbu:
                self._grid.logger.log("op:bbu_change, user:" + str(ue) +
                                      ", from:" + str(old_antenna.bbu) +
                                      ", to:" + str(antenna.bbu))

    def ue_disconnected(self, antenna, ue):
        """
        @param antenna Antenna obj.
        @param ue User obj.
        """
        self._grid.logger.log("op:disconnection, user:" + str(ue) +
                              ", antenna:" + str(antenna.pos))

        self._ue_disconnected_map[ue] = antenna
