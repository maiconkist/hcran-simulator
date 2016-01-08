UE_CONNECT = 0
UE_DISCONNECT = 1
ANTENNA_BW_UPDATE = 2


class Controller(object):

    def __init__(self, grid):
        self._grid = grid

        self._bbus = []

        self._pending = []
        self._ue_connected_map = {}
        self._ue_disconnected_map = {}
        self._antenna_bw_update = {}

    def register(self, bbu):
        """ Called by BBUs

        @param bbu BBU registering
        """
        self._bbus.append(bbu)

    def event(self, op, antenna, ue=None):
        """ Entry point for all event from the BBU
        @param op Operation code.
        @param op Operation code.
        """
        self._pending.append((op, antenna, ue))

    def update(self):
        """
        """
        for op, antenna, up in self._pending:
            if op == UE_CONNECT:
                self.ue_connected(antenna, ue)
            elif op == UE_DISCONNECT:
                self.ue_disconnected(antenna, ue)
            elif op == ANTENNA_BW_UPDATE:
                self._antenna_bw_update[antenna] = True
            else:
                pass

        if True in self._antenna_bw_update.values():
            self.antenna_update()

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

    def antenna_update(self):
        """
        """
        antennas = [a for a in [bbu.antennas for bbu in self._bbus]]

        print(len(antennas))

        for antenna in antennas:
            if antenna.ch_bw != antenna.bw_demand:
                self._grid.logger.log("op:antenna_bw_update, antenna:" +
                                      str(antenna) +
                                      ", from:" + str(antenna.bw) +
                                      ", to:" + str(antenna.bw_demand))
                antenna.ch_bw = antenna.bw_demand
