import scipy


def connectability(ue, cur_antenna, next_antenna):
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

    if p1 > 0 and p1 > p2:
        return None
    elif p2 > 0 and p2 > p1:
        return next_antenna
    else:
        return None


class User(object):

    def __init__(self, id, pos, moving_strategy, grid):

        self._id = id
        self._pos = pos
        self._moving_strategy = moving_strategy
        self._grid = grid

        self._connected_antenna = None


    @property
    def pos(self):
        return self._pos

    def move(self, step):
        # move User instance according to moving_strategy
        self._pos = self._moving_strategy(self._id)


    def stablish_connection(self, new_antenna):
        # if connection to new antenna is ok
        if new_antenna.connect(self):
            # disconnect from actual antenna and update
            if self._connected_antenna is not None:
                self._connected_antenna.disconnect(self)
            self._connected_antenna = new_antenna
            return True
        else:
            return False

    def update(self):
        antenna = self._grid.antenna_tree
        dist_list, idx_list = antenna.query([self._pos, ], min(10, len(antenna.data)))

        # for each antenna, from the closest to the farthest
        for d, idx in zip(dist_list[0], idx_list[0]):
            # if antenna in question if better than the current one (and its NOT the current one)
            if connectability(self, self._connected_antenna, self._grid._antenna[idx]):
                # if could stablish connection to antenna in question, break
                # repeat for the next closer antenna otherwise
                if self.stablish_connection(self._grid._antenna[idx]):
                    return True

        return False
