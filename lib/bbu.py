
class BBU(object):
    def __init__(self, pos, grid):
        self._pos = pos
        self._grid = grid

        self._antennas = []

    @property
    def pos(self):
        return self._pos

    def register(self, antenna):
        self._antennas.append(antenna)

    def notify(self, op_str, antenna, user):
        self._grid.logger.log(op_str + ", antenna:" + str(antenna.pos) + ", user:" + str(user._id) + ", pos:" + str(user.pos))
