#########################################################
# @file     energy_efficient_n_bs.py
# @author   Gustavo de Araujo
# @date     17 Mar 2016
#########################################################

import math
import util

class Cluster(object):

    def __init__(self, id, pos, grid):
        self._pos = pos
        self._grid = grid
        self._id = id

    @property
    def x(self):
        return self.pos[0]

    @property
    def y(self):
        return self.pos[1]

    @property
    def pos(self):
        """
        """
        return self._pos

    @pos.setter
    def pos(self, pos):
        """
        """
        print("Cannot set pos for Custer object")

