import math
import numpy
import util
import controller
from antenna import *
from user import *


class AntennaPeng(Antenna):

    def __init__(self, id, type, pos, radius, grid, bw = 1.4):
        Antenna.__init__(self, id, type, pos, radius, grid, bw)


    def init_peng(self, rbs, antennas):
        self.K = rbs
        self.N = len(self._ues)

        if self.N < 1:
            return

        self.others = antennas
        self.cnir = numpy.zeros((self.N, self.K))
        self.a = numpy.zeros((self.N, self.K))
        self.p = numpy.zeros((self.N, self.K))
        self.h = numpy.zeros((self.N, self.K))
        self.w = numpy.zeros((self.N, self.K))

        self.energy_efficient        = []
        self.energy_efficient.append(0)

        self.data_rate               = 0
        self.total_power_consumition = 0
        
        self.pm                      = Antenna.PMmax / self.N

        # Multiplicadores Lagrange 
        self.betan                   = numpy.zeros((self.N, 2))
        for n in range(0, self.N):
            for l in range(0, 2):
                self.betan[n][l] = 1

        self.lambdak                 = numpy.zeros((self.K, 2))
        for k in range(0, self.K):
            for l in range(0, 2):
                self.lambdak[k][l] = 1

        self.upsilonl                = [1,1]

    def obtain_matrix(self):
        for n in range(0, self.N):
            for k in range (0, self.K):
                self.cnir[n][k] = util.peng_power_interfering(self._ues[n], k,
                        self.others)
                self.w[n][k] = self.waterfilling_optimal(n, k)
                h1 = self.cnir[n][k] * self.w[n][k]
                h2 = ((1 + self.betan[n][0]) * numpy.log(h1))
                h3 = ((1 + self.betan[n][0]) / numpy.log(2)) 
                h4 = (1 - (1 / h1))

                if h2 < 1:
                    h2 = 0
                if h4 < 1:
                    h4 = 0

                self.h[n][k] = h2 - (h3 * h4)


    def waterfilling_optimal(self, n, k):
        p1 = (Antenna.B0 * (1 + self.betan[n][0])) 
        p2 = math.log((self.energy_efficient[len(self.energy_efficient)-1]
            * Antenna.EFF) + (self.lambdak[k][0] * Antenna.DR2M * Antenna.HR2M) + 
            self.upsilonl[0])
        return p1 / p2

    
