#########################################################
# @file     energy_efficient_n_bs.py
# @author   Gustavo de Araujo
# @date     11 Abr 2016
#########################################################

from antenna_mc import AntennaMc
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
import gc

DEBUG = True
IMAX = 3

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

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

 

class Mc(object): 
    def __init__(self, m, s, u, r):
        self.antennas = []
        self.small = s
        self.macros = m
        self.users = u * m
        self.repeticao = r

    def run(self, grid):
        antennas = grid._antennas    
        ues = grid._user

        associate_user_in_antennas(ues, antennas)
                
        # Loop maximo de itaracoes
        for i in range(0, IMAX):
            init = time.time()
            # Para todas as antenas
            #Liberar memoria
            gc.collect()
            debug_printf("Memoria liberada")
            for nAntennas in range(0, len(antennas)):
                if len(antennas[nAntennas].connected_ues) > 0:   
                    if(i == 0):
                        debug_printf("\n##########################\n## STARTING MONTE CARLO ##\n##########################\n")
                        antennas[nAntennas].init_mc(antennas, nAntennas)
                        antennas[nAntennas].obtain_interference_and_power(grid)
                        # Generating the first particles
                        antennas[nAntennas].mc_initial_particles()
                    else:
                        antennas[nAntennas].obtain_interference_and_power(grid)
                        antennas[nAntennas].mc_spinning_roulette()
                        antennas[nAntennas].mc_backup_particles()
                        antennas[nAntennas].mc_clean_variables()
                        antennas[nAntennas].mc_raises_temperature()
                        antennas[nAntennas].mc_new_particles_generation()
                    wait()
                        
                    antennas[nAntennas].mc_select_current_solution()
                    antennas[nAntennas].obtain_energy_efficient()
                    antennas[nAntennas].toString()
                    wait()
            grid.write_to_resume('MC', self.repeticao, i+1, time.time()-init)


                # values.index(min(values))
                #p = antennas[nAnt].mt_power_consumition(antennas[nAnt].best_a, antennas[nAnt].best_p)
                #c = antennas[nAnt].mt_data_rate(antennas[nAnt].best_a, antennas[nAnt].best_i,antennas[nAnt].best_p)
                #print p
                #print c
                #ee = c / p
                #end = time.time()
                #string = "MT[H:" + str(self.macros) + ";S:2" + ";U:" +  str(self.users) + "]"
                #string2 = str(i) + "," + str(c) + "," + str(p) + "," + str(ee) + "," + str(end-init) + "\n"
                #print string2
                #wait()

