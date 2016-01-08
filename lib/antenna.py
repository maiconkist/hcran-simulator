import util
import controller


class Antenna(object):

    def __init__(self, pos, radius, grid):

        # position tupe
        self._pos = pos
        # antenna coverage radius
        self._radius = radius
        # Grid object
        self._grid = grid
        # Channel bw (none in the start)
        self._cur_ch_bw = None
        # Channel BW required
        self._ch_bw_required = None
        # List of connected UEs
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

    @property
    def demand(self):
        return self._ch_bw_required

    @property
    def ch_bw(self):
        return self._cur_ch_bw

    @property
    def ch_bw_demand(self):
	return self._ch_bw_required

    @ch_bw.setter
    def ch_bw(self, new_bw):
        self._cur_ch_bw = new_bw

    def connect(self, ue):
        """ Called by ue when user connects

        @param ue UE connecting
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
        """ Called by ue when disconnects

        @param ue UE disconnecting
        """
        if ue in self._ues:
            self._ues.remove(ue)
            self._bbu.event(controller.UE_DISCONNECT, self, ue)
            return True
        return False

    def total_rb_demand(self):
        """ Check the total RBs required to satisfy UEs demands
        """
        def snr_to_bit(snr):
            if snr <= 6.0:
                return 1
            elif snr <= 9.4:
                return 2
            elif snr <= 16.24:
                return 4
            else:
                return 6

        rb_map = {}
        for ue in self._ues:
            # calculate the total RBs for each UE
            # mult per 84 because: 84 ofdm symbons in a RB
            rb_map[ue] = ue.demand / (snr_to_bit(util.snr(ue, self, 0)) * 84.0)
        return sum(rb_map.values())

    @staticmethod
    def rb_demand_to_ch_bw(rb_demand):
        """ Minimum channel BW based on RB demand

        @param rb_demand Total RB demand
        """
        if rb_demand <= (6 * 2000):
            return 1.4
        elif rb_demand <= (15 * 2000):
            return 3.0
        elif rb_demand <= (25 * 2000):
            return 5.0
        elif rb_demand <= (50 * 2000):
            return 10.0
        elif rb_demand <= (75 * 2000):
            return 15.0
        elif rb_demand <= (100 * 2000):
            return 20.0
        else:
            return None

    def update(self):
        """
        """
        # we assume a 20MHz channel,
        self._ch_bw_required = self.rb_demand_to_ch_bw(self.total_rb_demand())

        if self._ch_bw_required != self._cur_ch_bw:
            self._bbu.event(controller.ANTENNA_BW_UPDATE, self)

    def __str__(self):
        """
        """
        return str(self.pos)
