import math
import numpy
import util
import controller
import random
from antenna import *
from user import *
from util import *

DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)


class AntennaMc(Antenna):

    def __init__(self, id, type, pos, radius, grid, bw = 1.4):
        Antenna.__init__(self, id, type, pos, radius, grid, bw)

    def init_mc(self, antennas, nAntennas):
        if len(self.connected_ues) == 0:
            return
        
        self.i_particles = None
        self.a_particles = None
        self.p_particles = None
        self.history_i_particles = None
        self.history_a_particles = None
        self.history_p_particles = None    
        self.datarate_user_particles = None
        self.consumption_particles = None
    