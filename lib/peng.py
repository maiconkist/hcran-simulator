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
    raw_input("press enter to continue.")

class Peng(object):

    I = 10

    TOTAL_RBS = 5

    def __init__(self, m, u, c):
        self.antennas = []
        self.active_antennas = []
        self.macros = m
        self.users = u
        self.cenario = c

    def run(self, grid):
        antennas = grid._antennas
        ues = grid._user
        ees = [] 
        ######################
        # Associa usuario na 
        # antena mais proxima
        ######################
        for ue in ues:
            distance = 10000
            users_no_met = 0
            near = antennas[0]
            for antenna in antennas:
                #print "Nova Antenna"
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
            near.connected_ues.append(ue)        

        ######################
        # Peng Process 
        ######################
        for ant in antennas:
            ant.init_peng(Peng.TOTAL_RBS, antennas)

        tolerancia = 0.01
        for i in range(0, Peng.I):
            init = time.time()
            for antenna in antennas:
                dif = 1000
                if antenna.N > 0:
                    while dif > tolerancia:
                       # print ("dif: " + str(dif) + " - tol: " + str(tolerancia))
                       # wait()
                        antenna.obtain_sinr(grid)
                        antenna.obtain_matrix()
                        antenna.update_lagrange()
                        dif = antenna.max_dif()
                        antenna.swap_l()
                     
                    antenna.peng_obtain_energy_efficient()
#                print numpy.matrix(antenna.p)
#                raw_input("press enter to continue.")

            end = time.time()
            max_ee = 0
            sum_data_rate = 0
            sum_power_consumition = 0
            sum_ee = 0
            for antenna in antennas:
                if len(antenna.p_energy_efficient) == 0:
                    continue
                sum_data_rate += antenna.data_rate
                sum_power_consumition += antenna.power_consumition
                sum_ee += antenna.p_energy_efficient[len(antenna.p_energy_efficient)-1]

            data = str(self.macros) + "," + str(len(antennas)) + "," \
                + str(self.users) + "," + str(i) + "," + str(sum_data_rate/len(antennas)) \
                + "," + str(sum_power_consumition/len(antennas)) + "," \
                + str(sum_ee) + "," + str(end-init)  

            print data

