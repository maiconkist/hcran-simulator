def can_change_antenna(ue, cur_antenna, next_antenna):
    import math

    def dist(p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def power(ue, antenna):
        d = dist(ue.pos, antenna.pos)
        return math.pow(10.0, (1.0/10.0))*math.pow(4*math.pi*d, 2) if d < antenna.radius else 0

    if cur_antenna == next_antenna:
        return None

    p1 = power(ue, cur_antenna) if cur_antenna is not None else 0
    p2 = power(ue, next_antenna) if next_antenna is not None else 0

    if cur_antenna is not None and next_antenna is not None:
        if len(cur_antenna.connected_ues) == len(next_antenna.connected_ues):
            if p1 > 0 and p1 > p2 and cur_antenna.can_fit_ue(ue):
                return  cur_antenna
            elif p2 > 0 and p2 > p1 and next_antenna.can_fit_ue(ue):
                return next_antenna
        elif len(cur_antenna.connected_ues) > len(next_antenna.connected_ues):
            return cur_antenna
        else:
            return next_antenna

    if p1 > 0 and p1 > p2:
        return cur_antenna
    elif p2 > 0 and p2 > p1:
        return next_antenna


class User(object):
    HIGH_RATE_USER    = 0
    LOW_RATE_USER     = 1

    def __init__(self, id, pos, moving_strategy, grid, user_type=1):
        """
        """

        self._id = id
        self._pos = pos
        self._moving_strategy = moving_strategy
        self._grid = grid

        self._tx_rate = 0.0
        self._txs = []
        self._bad_connection = 0.0
        self._connected_antenna = None
        self._type = user_type
        self.antenna_in_range = []  #range of antennas available to serve UE
        self.power_connected_antenna = 0
        #self.antenna = None

    @property
    def x( self ):
        return self.pos[0]

    @property
    def y( self ):
        return self.pos[1]

    def add_antenna_in_range( self, antenna ):
        if not antenna in self.antenna_in_range:
            self.antenna_in_range.append( antenna )

    def get_near_antennas( self ):
        return self.antenna_in_range

    @property
    def pos(self):
        """
        """
        return self._pos

    def move(self, step):
        """
        """
        # move User instance according to moving_strategy
        if self._moving_strategy != None:
            self._pos = self._moving_strategy(self._id)


    @property
    def demand(self):
        """ Demand of the UE. Fixed in 5mbps
        """
        # 5 Mb/s
        return 5 * 10 ** 6

    @property
    def tx_rate(self):
        """
        """
        return self._tx_rate

    @tx_rate.setter
    def tx_rate(self, tx_rate):
        """
        """
        self._tx_rate =  tx_rate

    @property
    def total_tx(self):
        """
        """
        return sum(self._txs)

    def stablish_connection(self, new_antenna):
        """
        """
        if new_antenna is None:
            raise ValueError


        # Do nothing if trying to connect to same antenna
        if self._connected_antenna == new_antenna:
            return True

        # if connection to new antenna is ok
        if new_antenna.connect(self):
            # disconnect from actual antenna and update
            if self._connected_antenna is not None:
                self._connected_antenna.disconnect(self)
            self._connected_antenna = new_antenna
            return True
        else:
            return False

    def _update_connection(self):
        """
        """
        antenna = self._grid.antenna_tree
        dist_list, idx_list = antenna.query([self._pos, ], min(10, len(antenna.data)))

        # for each antenna, from the closest to the farthest
        # for d, idx in zip(dist_list[0], idx_list[0]):
        for d, idx in zip(dist_list[0], idx_list[0]):
            the_antenna = can_change_antenna(self, self._connected_antenna, self._grid._antennas[idx])
            # if antenna in question if better than the current one (and its NOT the current one)
            if the_antenna is not None and the_antenna != self._connected_antenna:
                # if could stablish connection to antenna in question, break
                # repeat for the next closer antenna otherwise
                if self.stablish_connection(the_antenna):
                    return True

        return False

    def _transmit(self):
        """
        """
        self._txs.append(self.tx_rate)


        # Check if user is experiencing a bad connections
        if self._tx_rate < self.demand:
            # 1 second
            self._bad_connection += 1
        else:
            # insert log if UE had a bad connection for more than 10 seconds
            if self._bad_connection > 9:
                self._grid.logger.log("op:bad_connection, user:" + str(self) +
                                      ", duration: " + str(self._bad_connection) +
                                      ", avg_rate:" + str(sum(self._txs[-10:])/10.0))
            self._bad_connection = 0

    def update(self):
        """
        """
        self._transmit()
        self._update_connection()


    def __str__(self):
        """
        """
        return str(self._id)
