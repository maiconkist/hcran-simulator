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

class Peng(object):

    I = 10

    TOTAL_RBS = 150

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
                    print "dif: " + str(dif)
                    print "tolerancia: " + str(tolerancia)
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

