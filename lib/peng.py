#########################################################
# @file     energy_efficient_n_bs.py
# @author   Gustavo de Araujo
# @date     11 Abr 2016
#########################################################

from antenna import Antenna
from grid import Grid
from user import *
from util import *
import math
import csv
import numpy

class PengProperties(object):

    L = 10

    def __init__(self, rrh, ues, total_rbs):
        self.rrh = rrh
        self.h = []

        ## Attributes
        self.a          = []
        self.h          = []
        self.p          = []
        self.M          = []         #n usuario de baixa demanda (30%)
        self.N          = []         #n usuarios de alta demanda (70%)

        self.b0         = 1         #nao tem ainda
        self.n0         = 1         #nao tem ainda
        self.drn        = 0         #tem no base conf Utils tem o calcula da distancia entre usuario e antena
        self.hrn        = 0         #tem no base conf Utils tem o calcula da distancia entre usuario e antena
        self.dmn        = 450
        self.hmn        = 0         #nao tem ainda
        self.p_max      = 20        #potencia maxima 20 ou 30
        self.pm_max     = 43
                                    #provavelemnte teremos de mudar para um vetor de usuarios
        self.K          = total_rbs
        self.prc        = 0.1
        self.pbh        = 0.2
        self.eff        = 4
        self.dr2m       = 125
        self.hr2m       = 1         #nao sei o valor, mas nao pode ser zero
        self.tolerancia = 0.001

        self.epsilon_beta       = 0.1
        self.epsilon_lambda     = 0.1
        self.epsilon_upsilon    = 0.1

        ## Calculate by some equation
        self.cinr                    = []   #(1)
        self.p                       = []   #
        self.w                       = []   #(24)

        self.data_rate               = 0    #(2) C
        self.total_power_consumition = 0    #(5) P
        self.energy_efficient        = 0    #(7) y
        self.c                       = 0

        self.sub_bn                  = 0
        self.sub_lambda_k            = 0
        self.sub_ipsilon             = 0

        self.bn                      = 0    #(32)
        self.lambdak                 = 0    #(33)
        self.ipsilon                 = 0    #(34)

        ###########################
        #Initialize variables
        ###########################

        #Classificate Users in N or M
        for ue in ues:
            if ue._type == User.HIGH_RATE_USER:
                self.N.append(ue)
            else:
                self.M.append(ue)

        self.cinr = numpy.zeros((len(self.N) + len(self.M), self.K))
        self.w = numpy.zeros((len(self.N) + len(self.M), self.K))
        self.h = numpy.zeros((len(self.N) + len(self.M), self.K))
        self.a = numpy.zeros((len(self.N) + len(self.M), self.K))
        self.p = numpy.zeros((len(self.N) + len(self.M), self.K))
        self.pm = self.pm_max / len(self.M)
        self.betan = numpy.zeros((len(self.N) + len(self.M), 2))
        self.lambdak = numpy.zeros((self.K, 2))
        self.upsilonl = [1, 1]


    ##################################
    #Functions
    ##################################
    def obtain_matrix(self):
        #Initialize matrix
        for i in range (0, len(self.N) + len(self.M)):
            for k in range (0, self.K):
                if i < len(self.N):
                    self.cinr[i][k] = self.calculate_cirn(self.N[i]._type)
                else:
                    self.cinr[i][k] = self.calculate_cirn(self.M[i-len(self.M)]._type)

        for n in range(0, len(self.N) + len(self.M)):
            for k in range (0, self.K):
                self.w[n][k] = self.calculate_waterfilling_optimal(n, k)
                hp1 = self.cinr[n][k] * self.w[n][k]
                hp2 = (1 - (self.cinr[n][k]*self.w[n][k]))

                if hp1 < 1:
                    hp1 = 1

                if hp2 < 1:
                    hp2 = 1

                self.h[n][k] = ((1 + self.betan[n][0]) * math.log(hp1)) -(((1
                    + self.betan[n][0]) / math.log(2)) * hp2)

        self.calculate_a_matrix()
        self.calculate_data_rate()
        self.calculate_power_consumition()
        self.calculate_energy_efficient()

    def k_for_omega1(self):
        return ((self.drn * self.hrn)/(self.b0 * self.n0))

    def k_for_omega2(self):
        return (self.drn * self.hrn)/((self.pm * self.dmn
            * self.hmn)+(self.b0 * self.n0))

    def calculate_cirn(self, reu_type):
        #Nao e a Antena e o usuario. Trocar TODO
        #Classificar no momento da associacao
        if reu_type == User.HIGH_RATE_USER:
            return self.k_for_omega1()
        else:
            return self.k_for_omega2()


    def calculate_waterfilling_optimal(self, n, k):
        p1 = (self.b0 * (1 + self.betan[n][0])) 
        p2 = math.log((self.energy_efficient * self.eff) + (self.lambdak[k][0]
                * self.dr2m * self.hr2m) + self.upsilonl[0])
        return p1 / p2

    def calculate_p_matrix_element(self, n, k):
        if self.cinr[n][k] < 1:
            h1 = 0
        else:
            h1 = (1 - 1 / self.cinr[n][k])

        result = self.w[n][k] - h1 
       
        if result < 0:
            result = 0
        
        return result

    def calculate_a_matrix(self):
        n_max = 0
        for n in range(0, len(self.N) + len(self.M)):
            for k in range(0, self.K):
                if n_max < self.h[n][k]:
                    n_max = self.h[n][k]

            for i in range(0, self.K):
                if i == n_max:
                    self.a[n][k] = 1
                    self.p[n][k] = self.calculate_p_matrix_element(n, k)
                else:
                    self.a[n][k] = 0
                    self.p[n][k] = 0 

    def calculate_subgradient_lambda(self, k):
        result = 0
        soma = 0
        if (self.N[n]._type == User.HIGH_RATE_USER):
            for k in range (0, self.K):
                soma += self.a[n][k] * self.p[n][k] * self.dr2m * self.hdr2m
            result = self.delta_0 - soma

        return result

    def calculate_subgradient_upsilon(self):
        soma = 0
        for n in range(0, self.N):
            for k in range(0, self.K):
                soma += self.a[n][k] * self.b[n][k]

        return self.pm * soma

    #(32) TODO
    def calculate_beta_n_l1(self, n):
        result = self.betan[n][0] - (self.epsilon_beta * self.sub_bn[n])
        if result > 0:
            return result
        else:
            return 1

    #(33) TODO
    def calculate_lamdak_l1(self,k):
        result = self.lambdak[k][0] - (self.epsilon_lambda * self.sub_lambda)
        if result > 0:
            return result
        else:
            return 1

    #(34) TODO
    def calculate_upsilon_l1(self):
        result = self.upsilonl[0] - (self.epsilon_upsilon * self.sub_upsilon)
        if result > 0:
            return result
        else:
            return 1

    def calculate_data_rate_n(self, n):
        for k in range(0, self.k):
            result += (self.a[n][k] * self.b0
                * math.log(1+(self.cinr[n][k]* self.p[n][k])))

        return result

    def calculate_subgradient_beta(self, n):
        result = 0
        c = self.calculate_data_rate_n(n)
        if ((n > 0) and (n < len(self.N))):
            result = self.c - self.nr
        else:
            result = c - self.ner

        return result            

    def update_l(self, l):
        for n in range(0, len(self.N) + self.M):
            self.sub_bn[n] = self.calculate_subgradient_beta(n)
            self.betan[n][1] = self.calculate_beta_n_l1(n)

        for k in range(0,self.K):
            self.sub_lambda_k[k] = self.calculate_subgradient_lambda(k)
            self.lambdak[k][1] = self.calculate_lamdak_l1(k)

        self.sub_upsilon = self.calculate_subgradient_upsilon()
        self.upsilonl[1] = self.calculate_upsilon_l1()

    def swap_l(self, n, k):
        self.betan[n][0] = self.betan[n][1]
        self.lambdak[k][0] = self.lambdak[k][1]
        self.upsilonl[0] = self.upsilonl[1]

    #C (2)
    def calculate_data_rate(self):
        result = 0
        for n in range(0, self.M + self.N): 
            result += calculate_data_rate_n(n) 

        return result

    def calculate_data_rate_n(self, n):
        for k in range(0, self.k):
            result += (self.a[n][k] * self.b0
                * math.log(1+(self.cinr[n][k]* self.p[n][k])))

        self.data_rate = result

    #P (3)
    def calculate_power_consumition(self):
        result = 0
        for n in range(0, self.N + self.M):
            for k in range(0, self.k):
                result += ((self.a[n][k] * self.p[n][k]) + self.prc + self.pbh)

        self.total_power_consumition = eff*result

    #Y (6)
    def calculate_energy_efficient(self):
        self.energy_efficient = self.calculate_data_rate()/self.calculate_power_consumition()

    #def max_dif(self):


class Peng(object):

    I = 10

    def __init__(self):
        self.antennas = []
        self.users = []
        self.active_antennas = []

    def run(self, grid):
        rrhs = grid._antennas
        ues = grid._user
        rrhs_used = []

        rrh = rrhs[0]
        for ue in ues:
            ue._connected_antenna = rrh
            
        peng_property = PengProperties(rrh, ues, grid.TOTAL_RBS)

        for ii in range(0, self.I):
            for rrh in rrhs:
                dif = 1
                while (dif < peng_property.tolerancia):
                    peng_property.obtain_matrix()

                    peng_property.update_l()
                    peng_property.swap_l()
                    #dif = peng_property.dif_max()

