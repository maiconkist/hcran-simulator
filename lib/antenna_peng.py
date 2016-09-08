import math
import numpy
import util
import controller
from antenna import *
from user import *


class AntennaPeng(Antenna):

    def __init__(self, id, type, pos, radius, grid, bw = 1.4):
        Antenna.__init__(self, id, type, pos, radius, grid, bw)

    def init_peng(self, antennas):
        self.K = Antenna.TOTAL_RBS
        self.N = len(self.connected_ues)

        if self.N < 1:
            return

        self.others = antennas
        self.sigma = numpy.zeros((self.N, self.K))
        self.i = numpy.zeros((self.N, self.K))
        self.noise_plus_interference = numpy.zeros((self.N, self.K))
        self.a = numpy.zeros((self.N, self.K))
        self.p = numpy.zeros((self.N, self.K))
        self.h = numpy.zeros((self.N, self.K))
        self.w = numpy.zeros((self.N, self.K))
        self.c = numpy.zeros((self.N, self.K))

        self.p_energy_efficient.append(1)

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

        self.upsilonl = [1,1]
        self.sub_betan = 1
        self.sub_lambdak = 1
        self.sub_upsilonl = 1

    def update_antennas(self, antennas):
        self.others = antennas

    def obtain_snr(self):
        for n in range(0, self.N):
            for k in range (0, self.K):
                self.i[n][k] = 0
                ue = self.connected_ues[n]
                for antenna in self.others:
                    if(antenna.a != None):
                        ue_ant_index = numpy.argmax(antenna.a[:, k])
                        #print "pos = ", ue_ant_index, k
                        if antenna.a[ue_ant_index, k] > 0:
                            R  =  util.dist(ue, antenna)
                            self.i[n][k] += abs(util.friis(antenna.p[ue_ant_index, k], Antenna.T_GAIN, Antenna.R_GAIN, R, Antenna.WAVELENTH))#dBm       

    def near_macro(self, bs_list):
        near_bs = None 
        near_dist = None
        for bs in bs_list:
            if near_bs == None:
                near_bs = bs
                near_dist = util.dist(self, bs)
            else:
                d = dist(self, bs)
                if d < near_dist:
                    near_dist = d
                    near_bs = bs
        return near_bs

    def obtain_sigma(self, n, k):
        if (self.type == Antenna.RRH_ID): #RRH
            macro = self.near_macro(self._grid.bs_list)
            dMue = util.dist(macro, self.connected_ues[n])#distancia rrh to user
            dMn = 31.5 + 35.0 * math.log10(dMue) #pathloss
            hRnk = 1#channel gain
            hMnk = 1#channel gain
            Pm = self.PMmax #pmax
            b0 = self.B0#bandwidth
            N0 = util.sinr(self.p[n][k], self.i[n][k], util.noise()) # estimated power spectrum density of both the sum of noise and weak inter-RRH interference (in dBm/Hz)
            dRue = util.dist(self, self.connected_ues[n])#distancia rrh to user#distancia rrh to user
            dRn = 31.5 + 40.0 * math.log10(dRue)
            return (dRn*hRnk)/(Pm*dMn*hMnk+b0*N0)
        else: #MACRO
            dMue = util.dist(self, self.connected_ues[n])#distancia rrh to user
            dMn = 31.5 + 35.0 * math.log10(dMue) #pathloss
            hMnk = 1#channel gain
            b0 = self.B0#bandwidth
            N0 = util.sinr(self.p[n][k], self.i[n][k], util.noise()) # estimated power spectrum density of both the sum of noise and weak inter-RRH interference (in dBm/Hz)
            #print dMn, hMnk, b0, N0
            return (dMn*hMnk)/(b0*N0)
                    

    def obtain_matrix(self):
        # Obtain snir, W and H
        for n in range(0, self.N):
            for k in range (0, self.K):
                self.sigma[n][k] = self.obtain_sigma(n, k)
                self.w[n][k] = self.waterfilling_optimal(n, k)
                h1 = self.sigma[n][k] * self.w[n][k]
                h2 = ((1 + self.betan[n][0]) * numpy.log(h1))
                h3 = ((1 + self.betan[n][0]) / numpy.log(2)) 
                h4 = (1 - (1 / h1))

                if h2 < 1:
                    h2 = 0
                if h4 < 1:
                    h4 = 0

                self.h[n][k] = h2 - (h3 * h4)
        
        self.a = numpy.zeros((self.N, self.K))
        nn = 0
        for k in range(0, self.K):
            n_max = -9999
            for n in range(0, self.N):
                if n_max < self.h[n][k]:
                    nn = n
                    n_max = self.h[n][k]
            self.a[nn][k] = 1

    def waterfilling_optimal(self, n, k):
        p1 = (Antenna.B0 * (1 + self.betan[n][0])) 
        p2 = math.log((self.p_energy_efficient[len(self.p_energy_efficient)-1]
            * Antenna.EFF) + (self.lambdak[k][0] * Antenna.DR2M * Antenna.HR2M) + 
            self.upsilonl[0])
        return p1 / p2

    ################################
    # Subgrad calculation
    def sub_c(self):
        for n in range(0, self.N):
            for k in range(0, self.K):
                self.c[n][k] = self.a[n][k] * self.B0 * math.log(1
                        + (self.sigma[n][k] * self.p[n][k]))

    def obtain_sub_betan(self, n):
        soma = 0
        for k in range(0, self.K):
            soma += self.c[n][k]

        if ((n > 0) and n < (self.N)):
            self.sub_betan = soma - Antenna.NR
        else:
            self.sub_betan = soma - Antenna.NER

    def obtain_sub_lambdak(self, k):
        soma = 0
        for n in range (0, self.N):
            if self.connected_ues[n]._type == User.LOW_RATE_USER:
                self.sub_lambdak = 0
            else:
                soma += self.a[n][k] * self.p[n][k] * self.DR2M * self.HR2M
        self.sub_lambdak = Antenna.D_0 - soma

    def obtain_sub_upsilonl(self):
        soma = 0
        for n in range(0, self.N):
            for k in range (0, self.K):
                soma += self.a[n][k] * self.p[n][k]
        self.sub_upsilonl = Antenna.PRmax - soma
       
    #################################
    # Lagrange
    def obtain_lagrange_betan(self, n):
        self.obtain_sub_betan(n)
        result = self.betan[n][0] - (Antenna.E_BETA * self.sub_betan)
        #print "betan " + str(result)
        if result > 0:
            self.betan[n][1] = result
        else:
            self.betan[n][1] = 0

    def obtain_lagrange_lambdak(self, k):
        self.obtain_sub_lambdak(k)
        result = self.lambdak[k][0] - (self.E_LAMBDA
                * self.sub_lambdak)
        if result > 0:
            self.lambdak[k][1] = result
        else:
            self.lambdak[k][1] = 0

    def obtain_lagrange_upsilonl(self):
        self.obtain_sub_upsilonl()
        result = self.upsilonl[0] - (self.E_UPSILON
                * self.sub_upsilonl)
        if result > 0:
            self.upsilonl[1] = result
        else:
            self.upsilonl[1] = 0

    def update_lagrange(self):
        self.sub_c()
        #print "snir:"
        #print numpy.matrix(self.sigma)
        #print "p:"
        #print numpy.matrix(self.p)
        #raw_input("")

        for n in range(0, self.N):
            self.obtain_lagrange_betan(n)

        for k in range(0, self.K):
            self.obtain_lagrange_lambdak(k)

        self.obtain_lagrange_upsilonl()
       
    def max_dif(self):
        max_beta = -9999
        max_lambdak = -9999
        for n in range(0, self.N):
            if self.betan[n][0] > 0 :
                beta = (self.betan[n][1] - self.betan[n][0]) / self.betan[n][0]
            else:
                beta = (self.betan[n][1] - self.betan[n][0])

            if beta > max_beta:
                max_beta = beta

        for k in range(0, self.K):
            if self.lambdak[k][0] > 0:
                lambdak = (self.lambdak[k][1] - self.lambdak[k][0]) / self.lambdak[k][0]
            else:
                lambdak = (self.lambdak[k][1] - self.lambdak[k][0])

            if lambdak > max_lambdak:
                max_lambdak = lambdak
   
        if self.upsilonl[0] != 0:
            max_upsilonl = (self.upsilonl[1] - self.upsilonl[0]) / self.upsilonl[0]
        else:
            max_upsilonl = self.upsilonl[1] - self.upsilonl[0]

        #print ("max_beta: " + str(max_beta) + " ,max_lambdak: "
        #        + str(max_lambdak) + " ,max_upsilonl: " + str(max_upsilonl))
        return max(max_beta, max_lambdak, max_upsilonl)

    def swap_l(self):
        for n in range(0, self.N):
            self.betan[n][0] = self.betan[n][1]
    
        for k in range(0, self.K):
            self.lambdak[k][0] = self.lambdak[k][1]
        
        self.upsilonl[0] = self.upsilonl[1]

    def peng_obtain_energy_efficient(self):
        self.obtain_data_rate()
        self.obtain_power_consumition()
        self.p_energy_efficient.append(self.data_rate/self.power_consumition)
