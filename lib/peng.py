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
import os
import time

DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

class PengProperties(object):

    L = 10

    def __init__(self, rrh, ues, total_rbs):
        self.rrh = rrh
        self.h = []

        ## Attributes
        self.a          = []
        self.h          = []
        self.p          = []
        self.M          = []
        self.N          = []

        self.b0         = 180
        self.n0         = -17
        self.drn        = 1         #Calculado na funcao
        self.hrn        = 1         #tem no base conf Utils tem o calcula da distancia entre usuario e antena
        self.dmn        = 450
        self.hmn        = 1
        self.p_max      = 20        #potencia maxima 20 ou 30
        self.pm_max     = 43
        
        self.K          = total_rbs
        self.prc        = 0.1
        self.pbh        = 0.2
        self.eff        = 4
        self.dr2m       = 125       #calcular
        self.hr2m       = 1 
        self.tolerancia = 0.001

        self.nr         = 600
        self.ner        = 400

        self.epsilon_beta       = 0.1
        self.epsilon_lambda     = 0.1
        self.epsilon_upsilon    = 0.1

        self.delta_0 = 1

        ## Calculate by some equation
        self.cinr                    = []   #(1)
        self.p                       = []   #
        self.w                       = []   #(24)

        self.data_rate               = 0    #(2) C
        self.total_power_consumition = 0    #(5) P
        self.energy_efficient        = 0    #(7) y
        self.c                       = 0

        self.sub_bn                  = 0
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
        self.sub_bn = numpy.zeros((len(self.N) + len(self.M),1))
        self.sub_lambda_k = numpy.zeros((self.K,1))
       
        self.pm = self.pm_max / len(self.M)
        self.betan = numpy.zeros((len(self.N) + len(self.M), 2))

        self.lambdak = numpy.zeros((self.K, 2))
        for k in range(0, self.K):
            for l in range(0,2):
                self.lambdak[k][l] = 1

        for n in range(0, len(self.N) + len(self.M)):
            for l in range(0,2):
                self.betan[n][l] = 1

        self.upsilonl = [1, 1]

    ##################################
    #Functions
    ##################################
    def obtain_matrix(self):
        #Initialize matrix

        #Refazer
        for i in range (0, len(self.N)):
            for k in range (0, self.K):
                self.cinr[i][k] = self.calculate_cirn(self.N[i])

        for i in range (len(self.N), len(self.N) + len(self.M)):
            for k in range (0, self.K):
                self.cinr[i][k] = self.calculate_cirn(self.M[len(self.N) - i])

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
                        
        #print(numpy.matrix(self.w))
        self.calculate_a_matrix()
        self.calculate_data_rate()
        self.calculate_power_consumition()
        self.calculate_energy_efficient()

    def k_for_omega1(self, reu):
        drn = dist(reu, self.rrh)
        return ((drn * self.hrn)/(self.b0 * self.n0))

    def k_for_omega2(self, reu):
        drn = dist(reu, self.rrh)
        return (drn * self.hrn)/((self.pm * self.dmn
            * self.hmn)+(self.b0 * self.n0))

    def calculate_cirn(self, reu):
        if reu._type == User.HIGH_RATE_USER:
            debug_printf("User.HIGH_RATE_USER")
            return self.k_for_omega1(reu)
        else:
            debug_printf("User.LOW_RATE_USER")
            return self.k_for_omega2(reu)

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
        nn = 0
        for k in range(0, self.K):
            n_max = -9999
            for n in range(0, len(self.N) + len(self.M)):
                if n_max < self.h[n][k]:
                    nn = n
                    n_max = self.h[n][k]

            self.a[nn][k] = 1
            self.p[nn][k] = self.calculate_p_matrix_element(nn, k)


    def calculate_subgradient_lambda(self, k):
        result = 0
        soma = 0
        if (len(self.N) > 0):
            for n in range (0, len(self.N)):
                soma += self.a[n][k] * self.p[n][k] * self.dr2m * self.hr2m
            result = self.delta_0 - soma

        return result

    def calculate_subgradient_upsilon(self):
        soma = 0
        for n in range(0, len(self.N)):
            for k in range(0, self.K):
                soma += self.a[n][k] * self.p[n][k]

        return self.pm * soma

    #(32)
    def calculate_beta_n_l1(self, n):
        result = self.betan[n][0] - (self.epsilon_beta * self.sub_bn[n])
        if result > 0:
            return result
        else:
            return 1

    #(33)
    def calculate_lamdak_l1(self,k):
        result = self.lambdak[k][0] - (self.epsilon_lambda * self.sub_lambda_k[k])
        if result > 0:
            return result
        else:
            return 1

    #(34)
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
            result = self.c - self.ner

        return result            

    def update_l(self):
        for n in range(0, len(self.N) + len(self.M)):
            self.sub_bn[n] = self.calculate_subgradient_beta(n)
            self.betan[n][1] = self.calculate_beta_n_l1(n)

        for k in range(0, self.K):
            self.sub_lambda_k[k] = self.calculate_subgradient_lambda(k)
            self.lambdak[k][1] = self.calculate_lamdak_l1(k)

        self.sub_upsilon = self.calculate_subgradient_upsilon()
        self.upsilonl[1] = self.calculate_upsilon_l1()

    def swap_l(self):
        for n in range(0, len(self.N) + len(self.M)):
            self.betan[n][0] = self.betan[n][1]
    
        for k in range(0, self.K):
            self.lambdak[k][0] = self.lambdak[k][1]
        
        self.upsilonl[0] = self.upsilonl[1]

    #C (2)
    def calculate_data_rate(self):
        result = 0
        for n in range(0, len(self.M) + len(self.N)): 
            result += self.calculate_data_rate_n(n) 

        self.data_rate = result

    def calculate_data_rate_n(self, n):
        result = 0
        for k in range(0, self.K):
            result += (self.a[n][k] * self.b0
                * math.log(1+(self.cinr[n][k]* self.p[n][k])))

        return result

    #P (3)
    def calculate_power_consumition(self):
        result = 0
        for n in range(0, len(self.N) + len(self.M)):
            for k in range(0, self.K):
                result += ((self.a[n][k] * self.p[n][k]) + self.prc + self.pbh)

        self.total_power_consumition = self.eff*result

    #Y (6)
    def calculate_energy_efficient(self):
        self.energy_efficient = self.data_rate/self.total_power_consumition

    def max_dif(self):
        max_beta = -9999
        max_lambdak = -9999
        for n in range(0, len(self.N) + len(self.M)):
            beta = (self.betan[n][1] - self.betan[n][0]) / self.betan[n][0]
            if beta > max_beta:
                max_beta = beta

        for k in range(0, self.K):
            lambdak = (self.lambdak[k][1] - self.lambdak[k][0]) / self.lambdak[k][0]
            if lambdak > max_lambdak:
                max_lambdak = lambdak
    
        max_upsilonl = (self.upsilonl[1] - self.upsilonl[0]) / self.upsilonl[0]

        #print "max_beta: " + str(max_beta) + ", max_lambdak: " + str(max_lambdak) + ", max_upsilonl: " + str(max_upsilonl)
    
        return max(max_beta, max_lambdak, max_upsilonl)

class Peng(object):

    I = 10

    TOTAL_RBS = 2

    def __init__(self, m, u, c):
        self.antennas = []
        self.users = []
        self.active_antennas = []
        self.macros = m
        self.users = u
        self.cenario = c

    def run(self, grid, arq):
        antennas = grid._antennas
        ues = grid._user
        

        ######################
        # Associa usuario na 
        # antena mais proxima
        ######################
        for ue in ues:
            distance = 10000
            users_no_met = 0
            near = antennas[0]
            for antenna in antennas:
                d = dist( ue, antenna ) 
                if antenna.type == Antenna.BS_ID:
                    if d < distance and d<Antenna.BS_RADIUS:
                        distance = d
                        near = antenna
                elif antenna.type == Antenna.RRH_ID:
                    if d < distance and  d<Antenna.RRH_RADIUS:
                        distance = d
                        near = antenna

                ue._connected_antenna = near
                near._ues.append(ue)        

        ######################
        # Peng Process 
        ######################
        for ant in antennas:
            ant.init_peng(Peng.TOTAL_RBS, antennas, Peng.I)
        
        dif = 1000
        tolerancia = 0.01
        for i in range(0, Peng.I):
            c = 0
            p = 0
            print "I: " + str(i)
            init = time.time()
            for ant in antennas:
                #if (len(ant._ues) == 0):
                 #   continue
                while dif > tolerancia:
                    ant.update_matrix()
                    ant.update_l()
                    dif = ant.max_dif()
                    ant.swap_l()

                ant._l += 1
                ant.data_rate()
                c += ant._data_rate
                ant.power_consumition()
                p += ant._total_power_consumition
                ant.energy_efficient()
                ee = ant._energy_efficient[ant._l-1]

            end = time.time()
            print "Escreve"
            arq.write(str(self.macros) + "," + str(len(antennas)) + ","
                    + str(self.users) + "," + str(self.cenario) + "," + str(i) + "," + str(c)
                    + "," + str(p) + "," +str(c/p) + "," + str(end-init) + "\n")

'''
        for ii in range(0, self.I):
            debug_printf("*** Outer Loop: " + str(ii))
            for rrh in rrhs:
                dif = 10 
                while (dif > peng_property.tolerancia):
                    debug_printf("*** Inner Loop: " + str(iteration))
                    peng_property.obtain_matrix()
                    peng_property.update_l()
                    dif = peng_property.max_dif()
                    peng_property.swap_l()
                    debug_printf("*** Diff: " + str(dif)
                            + " peng_property.tolerancia: " + str(peng_property.tolerancia))
                    iteration += 1
                    
                    #wait()
            peng_property.print_matrix()
'''                    

