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
import random

DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

class Peng(object):

    I = 10

    TOTAL_RBS = 10

    def __init__(self, m, u, c):
        self.antennas = []
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
                    print "dif: " + str(dif)
                    print "tolerancia: " + str(tolerancia)
                    ant.update_matrix()
                    ant.update_l()
                    dif = ant.max_dif()
                    ant.swap_l()
                    #print numpy.matrix(ant._cnir)
                    #wait()


                ant._l += 1
                ant.data_rate()
                c += ant._data_rate
                ant.power_consumition()
                p += ant._total_power_consumition
                ant.energy_efficient()
                ee = ant._energy_efficient[ant._l-1]

            end = time.time()
            print "Escreve"
            string = "PENG[H:" + str(self.macros) + ";S:2" + ";U:" +  str(self.users) + "]"
            #string2 = "iteracao,c,p,ee,temp\n"
            string2 = str(i) + "," + str(c) + "," + str(p) + "," + str(c/p) + "," + str(end-init) + "\n"
            arq.write(string + sitring2)

    def roleta(EE, nJogadas):
        nArea = len(EE)
        area = np.zeros(shape=(nArea))
        result = np.zeros(shape=(nJogadas))
        total = sum(EE)
        ant = 0;
        for q in range(0, len(EE)):
            area[q] = ant + EE[q]
            ant = area[q]

        print EE
        print area

        for q in range(0, nJogadas):
            rd = random.uniform(0.0, total)
            for t in range(0, len(area)):
                if rd < area[t]:
                    result[q] = t
                    break

        return result

    def run_monte_carlo(self, grid):
        iMax = 10
        rrhs = len(grid._antennas)
        antennas = grid._antennas    
        ues = grid._user
        
        #######################
        # Associa usuario na 
        # antena mais proxima
        # Repliquei o codigo
        # e uma PESSIMA PRATICA
        ########################
        for ue in ues:
            distance = 10000
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
       

        for i in range(0, iMax):
            init = time.time()
            for rrh in range(0, rrhs):
                antennas[rrh].init_monte_carlo()
                #CALCULAR O A ZUADO DA INTERFERENCIA BASEADA NA MELHOR MATRIZ DE CADA RRH
                for rr in antennas:
                    if rr._id != antennas[rrh]._id:
                        antennas[rrh]._others_ant.append(antennas[rrh])

                    rr.init_peng(Peng.TOTAL_RBS, antennas[rrh]._others_ant, i)

                for n in range (0, len(antennas[rrh]._ues)):
                    for k in range (0, Peng.TOTAL_RBS):
                        antennas[rrh]._cnir[n][k] = peng_power_interfering(antennas[rrh]._ues[n], k, antennas[rrh]._others_ant)
                        antennas[rrh]._w[n][k]= antennas[rrh].mt_waterfilling_optimal(n, k, antennas[rrh].EE[i])

                if(i == 0):
                    # Generating the first M particles
                    for z in range(0,antennas[rrh].M):
                        for y in range(0,antennas[rrh].K): #RB
                            r = random.randint(-(antennas[rrh].N/3), antennas[rrh].N)-1 #Usuario
                            if r > 0:
                                antennas[rrh].a[z,r,y] = 1
                                antennas[rrh].p[z,r,y] = antennas[rrh].calculate_p_matrix_element(r, y) # aqui tu calcula p
                                antennas[rrh].i[z,r,y] = antennas[rrh]._cnir[r][y]
                                antennas[rrh].doPartialCalc(z,r,y)                                 
                        antennas[rrh].doFinalCalc(z, rrh)
                else:
                    antennas[rrh].rol = roleta(antennas[rrh].EE, antennas[rrh].M)
                    antennas[rrh].aAnt = antennas[rrh].a
                    antennas[rrh].clean()
                    # Raises the temperature
                    antennas[rrh].Temp = antennas[rrh].Temp + 0.01
                    for z in range(0,antennas[rrh].M):
                        mSel = antennas[rrh].aAnt[antennas[rrh].rol[z]]
                        for y in range(0,antennas[rrh].K):
                            # como gerar a matriz a baseada na mSel?????
                            if random.choice([True, False, False]): #30% de chance de trocar
                                r = random.randint(-(antennas[rrh].N/3), antennas[rrh].N)-1
                                if r > 0:        
                                    antennas[rrh].a[z,r,y] = 1
                                    antennas[rrh].p[z,r,y] =  antennas[rrh].calculate_p_matrix_element(r, y)# aqui tu calcula p
                                    antennas[rrh].i[z,r,y] =  self._cnir[r][y]# matriz de interferencia ja deve existir
                                    antennas[rrh].doPartialCalc(z,r,y)
                            else:
                                r = antennas[rrh].aAnt.index(max(antennas[rrh].aAnt[z,:,y]))
                                antennas[rrh].a[z,r,y] = 1
                                antennas[rrh].p[z,r,y] = antennas[rrh].calculate_p_matrix_element(r, y) ## aqui tu calcula p
                                antennas[rrh].i[z,r,y] = self._cnir[r][y] # matriz de interferencia ja deve existir
                                antennas[rrh].doPartialCalc(z,r,y)
                        antennas[rrh].doFinalCalc(z,rrh)
                        antennas[rrh].mt_update_l(z)

# values.index(min(values))


                print "Max value element : ", max(antennas[rrh].EE)
                index = numpy.argmax(antennas[rrh].EE)
                antennas[rrh].best_a = antennas[rrh].a[index]
                antennas[rrh].best_p = antennas[rrh].p[index]
                antennas[rrh].best_i = antennas[rrh].i[index]
                #PARA CADA RRH A ATUAL E O A DE MELHOR EE
                #SENDO O P CORREPONDETE A A O P ATUAL

                p = antennas[rrh].mt_power_consumition(antennas[rrh].best_a, antennas[rrh].best_p)
                c = antennas[rrh].mt_data_rate(antennas[rrh].best_a, antennas[rrh].best_i,antennas[rrh].best_p)
                print p
                print c
                ee = c / p
                end = time.time()
                string = "MT[H:" + str(self.macros) + ";S:2" + ";U:" +  str(self.users) + "]"
                string2 = str(i) + "," + str(c) + "," + str(p) + "," + str(ee) + "," + str(end-init) + "\n"
                print string2
                wait()

