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

DEBUG = False

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("press enter to continue.")

def associate_user_in_antennas(ues, antennas):
    #######################
    # Associa usuario na 
    # antena mais proxima
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
        near.connected_ues.append(ue)  

class Peng(object):

    I = 10

    #TOTAL_RBS = 5

    def __init__(self, rep):
        self.repeticao = rep
        #self.antennas = []
        #self.active_antennas = []
        #self.macros = m
        #self.users = u
        #self.cenario = c

    def run(self, grid):

        associate_user_in_antennas(grid.users, grid.antennas)      

        antennas = grid._antennas
        ues = grid._user
        ees = []

        ######################
        # Peng Process 
        ######################
        for ant in antennas:
            ant.init_peng(antennas)

        tolerancia = 0.01
        for i in range(0, Peng.I): # Outer Loop
            init = time.time()
            for antenna in antennas:
                dif = 1000
                if antenna.N > 0:
                    while dif > tolerancia: #Inner Loop
                        #print ("dif: " + str(dif) + " - tol: " + str(tolerancia))
                        #wait()
                        antenna.obtain_snr() # a zuado
                        antenna.obtain_matrix() # matrix a e p
                        antenna.update_lagrange() 
                        dif = antenna.max_dif()
                        antenna.swap_l()
                     
                antenna.peng_obtain_energy_efficient()
#                print numpy.matrix(antenna.p)
#                raw_input("press enter to continue.")

            datarate = 0
            consumption = 0
            meet_user = 0
            for antenna in antennas:
                #if len(antenna.p_energy_efficient) == 0:
                #    continue
                datarate += antenna.data_rate
                consumption += antenna.power_consumition
                meet_user += antenna.users_meet

            f = open('resumo.csv','a')
            f.write('PENG,PENG['+str(len(grid.bs_list))+'-'+str(len(grid.rrh_list))+'-'+str(len(grid.users))+'],'+str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid.users))+','+str(self.repeticao)+','+str(i)+','+str(datarate)+','+str(consumption)+','+str(datarate/consumption)+','+str(meet_user)+','+str(time.time()-init)+'\n')
            f.close()

