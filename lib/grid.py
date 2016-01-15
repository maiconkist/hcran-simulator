import random
import scipy.spatial

import re


class Log():
    """
    """
    logs = []

    mapper = {"op:connection": 0,
              "op:disconnection": 0,
              "op:bbu_change": 0,
              "op:antenna_bw_update": 0,
              "op:antenna_impossible_cap":0,
              "good_cap":0,
              "good_cap_sum":0,
              "bad_cap":0,
              "bad_cap_sum":0,
              }


    @staticmethod
    def log(m):

        if 'op:connection' in m:
            Log.mapper['op:connection'] += 1
        elif 'op:disconnection' in m:
            Log.mapper['op:disconnection'] += 1
        elif 'op:bbu_change' in m:
            Log.mapper['op:bbu_change'] += 1
        elif 'op:antenna_bw_update' in m:
            Log.mapper['op:antenna_bw_update'] += 1
        elif 'op:antenna_impossible_cap' in m:
            Log.mapper['op:antenna_impossible_cap'] += 1
        elif 'op:antenna_good_cap' in m:
            Log.mapper['good_cap'] += 1

            regex = re.compile("per_used:([0-9]*\.[0-9]*)")
            Log.mapper['good_cap_sum'] += float( regex.findall(m)[0] )
        elif 'op:antenna_bad_cap' in m:
            Log.mapper['bad_cap'] += 1

            regex = re.compile("per_used:([0-9]*\.[0-9]*)")
            Log.mapper['bad_cap_sum'] += float( regex.findall(m)[0] )


        Log.logs.append(m)

class Grid(object):

    def __init__(self, size=(1000, 1000)):
        """
        """
        self._size = size

        self._user = []
        self._antennas = []
        self._bbus = []
        self._controllers = []

        self._antenna_tree = None

        self._initialized = 0

    def add_user(self, user):
        """
        """
        self._user.append(user)

    def add_antenna(self, antenna):
        """
        """
        self._antennas.append(antenna)

    def add_bbu(self, bbu):
        """
        """
        self._bbus.append(bbu)

    def add_controller(self, cntrl):
        """
        """
        self._controllers.append(cntrl)

    @property
    def bbus(self):
        """
        """
        return self._bbus

    @property
    def users(self):
        """
        """
        return self._user

    @property
    def size(self):
        """
        """
        return self._size

    @property
    def logger(self):
        """
        """
        return Log()

    def random_pos(self):
        """
        """
        x = random.randrange(0, self.size[0])
        y = random.randrange(0, self.size[1])
        return [x, y]

    @property
    def antenna_tree(self):
        """
        """
        return self._antenna_tree

    def init(self):
        """
        """
        if self._antenna_tree is None:
            self._antenna_tree = scipy.spatial.KDTree(
                [a.pos for a in self._antennas]
            )

    def step(self, time):
        """
        """
        self.init()

        # move for 1 second (ue must perform operations)
        for ue in self._user:
            ue.move(time)

        # update ue (after performing movements )
        for ue in self._user:
            ue.update()

        # update antennas
        for antenna in self._antennas:
            antenna.update()

        # update bbus
        for bbu in self._bbus:
            bbu.update()

        # update controllers
        for cntrl in self._controllers:
            cntrl.update()
