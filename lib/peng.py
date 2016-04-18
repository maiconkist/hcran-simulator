#########################################################
# @file     energy_efficient_n_bs.py
# @author   Gustavo de Araujo
# @date     11 Abr 2016
#########################################################

from antenna import Antenna
from grid import Grid
from util import *
import math
import csv

class PengProperties(object):

    RUE_HIGH_RATE    = 0
    RUE_LOW_RATE     = 1
    I = 10
    L = 10

    def __init__(self, rrh):
        self.rrh = rrh
        self.h = []

        ## Attributes
        self.a                     = []
        self.p                     = []
        self.beta                  = []
        self.betan                 = []
        self.lambdak               = []
        self.upsilonl              = []
        self.epsilon               = []
        self.subgradient_beta_n    = []
        self.subgradient_lambda_k  = []
        self.subgradient_upsilon_l = []

        self.b0         = 0
        self.n0         = 0
        self.drn        = 0
        self.hrn        = 0
        self.dmn        = 0
        self.hmn        = 0
        self.p_max      = 0
        self.M          = 0
        self.N          = 0
        self.prc        = 0
        self.pbh        = 0
        self.eff        = 0
        self.lambd      = 0
        self.upsilon    = 0
        self.dr2m       = 0
        self.hdr2m      = 0
    
        ## Calculate by some equation
        self.cnir                    = []   #(1)
        self.p                       = []   #
        self.w                       = []   #(24)

        self.pm                      = 0    #()
        self.data_rate               = 0    #(2) C
        self.total_power_consumition = 0    #(5) P
        self.energy_efficient        = 0    #(7) y

        self.bn                      = 0    #(32)
        self.lambda_k                = 0    #(33)
        self.ipsilon                 = 0    #(34)

        #self.b0 = self.rrh._cur_ch_bw
        #self.n0 = 0 #TODO

    def k_for_omega1(self):
        return ((self.drn * self.hrn)/(self.b0 * self.n0))

    def k_for_omega2(self):
        return (self.drn * self.hrn)/((self.pm * self.dmn
            * self.hmm)+(self.b0 * self.n0))

    def calculate_cirn(self, reu_type):
        if reu_type == RUE_HIGH_RATE:
            return k_for_omega1()
        else:
            return k_for_omega2()

    #C (2)
    def calculate_data_rate(self):
        result = 0
        for n in range(0, self.M + self.N): 
            result += calculate_data_rate_n(n) 

        return result

    def calculate_data_rate_n(self, n):
        for k in range(0, self.k):
            result += (self.a[n][k] * self.b0
                * math.log(1+(self.cnir[n][k]* self.p[n][k])))

        return result

    #P (3)
    def calculate_power_consumition(self):
        result = 0
        for n in range(0, self.N + self.M):
            for k in range(0, self.k):
                result += ((self.a[n][k] * self.p[n][k]) + self.prc + self.pbh)

        return eff*result

    #Y (6)
    def calculate_energy_efficient(self):
        return self.calculate_data_rate()/self.calculate_power_consumition()

    #(28)
    def subgradient_beta(self, n):
        result = 0
        if ((n > 0) and (n < self.N)):
            c = self.calculate_data_rate_n(n)
            result = c - nr
            
        return result            
       
    #(29)
    def calculate_subgradient_beta2(self, n):
        result = 0
        if (((self.N + 1) > n) and (n < (self.N + self.M))):
            c = self.calculate_data_rate_n(n)
            result = c - nr

        return result            

    def calculate_subgradient_lambda(self, k, type):
        result = 0
        soma = 0
        if (type == RUE_LOW_RATE):
            for n in range (0, self.N):
                soma += self.a[n][k] * self.p[n][k] * self.dr2m * self.hdr2m
            result = self.delta_0 - soma

        return result

    def calculate_subgradient_ipsilon(self):
        soma = 0
        for n in range(0, self.N):
            for k in range(0, self.K):
                soma += self.a[n][k] * self.b[n][k]

        return pm * soma

    #(32)
    def calculate_beta_n_l_1(self, l):
        self.betan[l+1] = self.betan[l] - self.epsilon[l+1] * self.subgradient_beta_n[l+1]

    #(33)
    def calculate_lambda_k(self, l):
        self.lambdak[l+1] = self.lambdak[l] - self.epsilon[l+1] * sekf.subgradient_lambda_k[l+1]

    #(34)
    def calculate_subgradient_ipsilon(self, l):
        self.ipsilon[l+1] = self.

class Peng(object):

    def __init__(self):
        self.antennas = []
        self.users = []
        self.active_antennas = []

    def run(self, grid):
        rrhs = grid._antennas
        ues = grid._user
        rrhs_used = []

        for ue in ues:
            distance = 10000
            near = rrhs[0]
            for rrh in rrhs:
                #Pega a antenas mais proxima que tenha RBs disponiveis
                d = dist(ue,rrh)
                r = (grid.TOTAL_RBS -1 -len(rrh.resources))

                if rrh.type == Antenna.BS_ID:
                    if (d < distance) and (r >= calculate_necessary_rbs(ue,
                        rrh)) and d < Antenna.BS_RADIUS:
                        distance = d
                        near = rrh
                elif rrh.type == Antenna.RRH_ID:
                    if (d < distance) and (r >= calculate_necessary_rbs(ue,
                        rrh)) and d < Antenna.RRH_RADIUS:
                        distance = d
                        near = rrh

            #Inicio da proxima faixa de RBs
            begin_rbs = len(near.resources)
            end_rbs = begin_rbs + calculate_necessary_rbs(ue, rrh) -1

            if near.type == Antenna.BS_ID:
                begin_rbs += grid.TOTAL_RBS_RRH
                if (end_rbs < grid.TOTAL_RBS):
                   ue.from_rb = begin_rbs
                   ue.to_rb = end_rbs
                   ue._connected_antenna = near
                   ue.power_connected_antenna = friis(ue,near)
               
            else: #near.type == Antenna.RRH_ID:
                if (end_rbs < grid.TOTAL_RBS_RRH):
                   ue.from_rb = begin_rbs
                   ue.to_rb = end_rbs
                   ue._connected_antenna = near
                   ue.power_connected_antenna = friis(ue,near)

            for rb in range(begin_rbs, end_rbs + 1):
                near.resources.append(rb)
                grid.matrix_resources[near._id][rb] = ue._id

            
        for ue in reversed(ues):
            if ((ue._connected_antenna != None) and 
               (ue._connected_antenna.type == Antenna.BS_ID) and 
               (len(ue._connected_antenna.resources) < grid.TOTAL_RBS)):
                ue.to_rb = grid.TOTAL_RBS - 1
                for rb in range (ue.from_rb, ue.to_rb + 1):
                    ue._connected_antenna.resources.append(rb)
                    grid.matrix_resources[ue._connected_antenna._id][rb] = ue._id

            elif ((ue._connected_antenna != None) and
               (ue._connected_antenna.type == Antenna.RRH_ID) and
               (len(ue._connected_antenna.resources) < grid.TOTAL_RBS_RRH)):
                for rb in range (ue.from_rb, ue.to_rb + 1):
                    ue._connected_antenna.resources.append(rb)
                    grid.matrix_resources[ue._connected_antenna._id][rb] = ue._id

        #Peng
        for rrh in rrhs:
            proper = PengProperties(rrh)
            print rrh.
                






