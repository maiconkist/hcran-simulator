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
        self.h                     = []
        self.p                     = []
        self.betan                 = []
        self.lambdak               = []
        self.upsilonl              = []
        self.v_M                   = []
        self.v_N                   = []

        self.b0         = 0         #não tem ainda
        self.n0         = 0         #não tem ainda
        self.drn        = 0         #tem no base conf. Utils tem o calcula da distancia entre usuario e antena
        self.hrn        = 0         #tem no base conf. Utils tem o calcula da distancia entre usuario e antena
        self.dmn        = 450
        self.hmn        = 0         #não tem ainda
        self.p_max      = 20        #potencia máxima 20 ou 30
        self.pm_max     = 43
        self.M          = 0         #n usuario de baixa demanda (30%)
        self.N          = 0         #n usuarios de alta demanda (70%)
                                    #provavelemnte teremos de mudar para um vetor de usuários
        self.K          = Grid.TOTAL_RBS 
        self.prc        = 0.1
        self.pbh        = 0.2
        self.eff        = 4
        self.dr2m       = 125
        self.hr2m       = 0
        self.tolerancia = 0.001

        self.epsilon_beta       = 0.1
        self.epsilon_lambda     = 0.1
        self.epsilon_upsilon    = 0.1

        ## Calculate by some equation
        self.cinr                    = []   #(1)
        self.p                       = []   #
        self.w                       = []   #(24)

        self.pm                      = self.pm_max / self.M
        self.data_rate               = 0    #(2) C
        self.total_power_consumition = 0    #(5) P
        self.energy_efficient        = 0    #(7) y

        self.bn                      = 0    #(32)
        self.lambda_k                = 0    #(33)
        self.ipsilon                 = 0    #(34)

        #Initialize variables
        self.betan[0]       = 1
        self.lambdak[0]     = 1
        self.upsilonl[0]    = 1

        #Initialize matrix
        for n in range(0, self.N):
            for k in range (0, self.K):
                self.cinr[n][k] = self.calculate_cirn(rrh._reu_type)
                self.w[n][k] = self.calculate_waterfilling_optimal(n, k)
                hp1 = ((1 + self.betan) * math.log(self.cinr[n][k] * self.w[n][k]))
                hp2 = math.log(2) * (1 - (self.cinr[n][k]*self.w[n][k]))

                if hp1 < 0:
                    hp1 = 0

                if hp2 < 0:
                    hp2 = 0

                self.h[n][k] = hp1 -(((1 + self.betan) / math.log(2)) * hp2)
                #self.p[n][k] = self.calculate_p_matrix_element(n, k)
                #Colocar calculo do p somente quando a[n][k] for 1

        self.calculate_a_matrix()

    def calculate_a_matrix(self):
        n_max = 0
        for n in range(0, self.N):
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

    def calculate_p_matrix_element(self, n, k):
        result = self.w[n][k] - (1 - 1 / self.cnir[n][k])
       
        if result < 0:
            result = 0
        
        return result

    def calculate_waterfilling_optimal(self, n, k):
        p1 = (self.b0 * (1 + self.betan[0])) 
        p2 = math.log((self.energiy_efficient * self.eff) + self.lambdak[0]
                * self.dr2m * self.hr2m + self.upsilon[0])
        return p1 / p2

    def k_for_omega1(self):
        return ((self.drn * self.hrn)/(self.b0 * self.n0))

    def k_for_omega2(self):
        return (self.drn * self.hrn)/((self.pm * self.dmn
            * self.hmm)+(self.b0 * self.n0))

    def calculate_cirn(self, reu_type):
        #Não é a Antena é o usuario. Trocar TODO
        #Classificar no momento da associação

        if reu_type == Antenna.RUE_HIGH_RATE:
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
                * math.log(1+(self.cinr[n][k]* self.p[n][k])))

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
    def calculate_subgradient_beta(self, n):
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

    #(30)
    def calculate_subgradient_lambda(self, k, type):
        result = 0
        soma = 0
        if (type == RUE_LOW_RATE):
            for n in range (0, self.N):
                soma += self.a[n][k] * self.p[n][k] * self.dr2m * self.hdr2m
            result = self.delta_0 - soma

        return result

    #(31)
    def calculate_subgradient_upsilon(self):
        soma = 0
        for n in range(0, self.N):
            for k in range(0, self.K):
                soma += self.a[n][k] * self.b[n][k]

        return pm * soma

    #(32) TODO
    def calculate_beta_n_l1(self):
        return self.betan[0] - (self.epsilon_beta * self.epsilon_beta)

    #(33) TODO
    def calculate_lamdak_l1(self):
        return self.lambdak[0] - (self.epsilon_lambda * self.epsilon_lambda)

    #(34) TODO
    def calculate_upsilon_l1(self):
        return self.upsilon[0] - (self.epsilon_upsilon * self.epsilon_upsilon)


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
            
                #Classicar o usuário como alta ou baixa demanda
                #Adicionar REU a RRH e classificar como N ou M

            peng_property = PengProperties(rrh)
            for i in range(0, I):
                for rrh in rrhs:
                    #Inicializa beta, lambda e v
                    dif = 1
                    l = 0
                    while (dif < self.tolerancia): 
                        #verifica se os multiplicadoes são menores que a tolerancia

                        #Atualizar valores de beta, lambda e v (l+1)
                        #e recalcula as matris a, p, h, etc...
                        l = l + 1
                #executa só o else do algoritmo y(i) = ...

'''
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

'''
'''

            '''

