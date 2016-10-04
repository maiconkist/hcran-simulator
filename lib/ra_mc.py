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
from copy import copy, deepcopy
import math
import csv
import numpy
import os
import time
import random
import gc
import util

DEBUG = False

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

def associate_user_in_antennas(grid):
    #######################
    # Associa usuario na 
    # antena mais proxima
    ########################
    ues = grid.users
    antennas = grid.antennas
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
    grid.remove_users()
    for antenna in antennas:
        for ue in antenna.connected_ues:
            grid.add_user(ue)

    return grid


class Mc(object): 
    def __init__(self, r, delta1, delta2):
        self.delta1 = delta1
        self.delta2 = delta2
        self.repeticao = r
        self.MC_STEPS = 200
        self.STABLE_STEPS_LENGTH = 10
        self.NPARTICLES   = 100
        self.HISTORY_LENGTH = 0.02
        self.RESETRATE    = 0.01
        self.L_BETA       = 2
        self.L_LAMBDA     = 20
        #self.L_UPSILON    = 0.1
        #self.E_DEALTA     = 0.2
        self.TX_FLUTUATION = 0.2
        self.lambda_particles = None
        self.beta_particles = None 
        self.i_particles = None
        self.a_particles = None
        self.p_particles = None
        self.ee_particles = None
        self.stable_particles = None
        self.meet_user_particles = None
        self.datarate_user_particles = None
        self.datarate_particles = None
        self.consumption_antenna_particles = None
        self.consumption_particles = None
        self.datarate_constraint_particles = None
        self.history_i_particles = None
        self.history_a_particles = None
        self.history_p_particles = None
        self.history_ee_particles = None
        self.history_datarate_particles  = None
        self.history_consumption_particles  = None
        self.history_datarate_constraint_particles = None
        self.history_datarate_user_particles = None
        self.history_lambda_particles = None
        self.history_beta_particles = None
        

    def select_best_particle(self, grid):
        #self.L_BETA = numpy.max(self.beta_particles[:])
        #self.L_LAMBDA = numpy.max(self.lambda_particles[:])
        best_particle = -1
        for p in range(0, self.NPARTICLES):
            if best_particle == -1:
                best_particle = p
                best_ee = self.L_BETA * ((self.datarate_particles[p][0]*2000/1048576) / self.consumption_particles[p][0]) + (self.L_LAMBDA) * (self.datarate_constraint_particles[p][0]*2000/1048576)
            else:
                ee = self.L_BETA * ((self.datarate_particles[p][0]*2000/1048576) / self.consumption_particles[p][0]) + (self.L_LAMBDA) * (self.datarate_constraint_particles[p][0]*2000/1048576)
                if ee > best_ee:
                    best_ee = ee
                    best_particle = p


        #for ue in range (0, len(grid.users)):
            #print "UE:", ue, "RBs:", sum(self.a_particles[best_particle, ue, :])

        return best_particle


    def raises_temperature(self):
        ee_list = numpy.zeros(shape=(self.NPARTICLES, 10))
        for p in range(0, self.NPARTICLES):
            for t in range(0, 10):
                if(self.datarate_particles[p][t] > 0 and self.consumption_particles[p][t]> 0):
                    ee_list[p][t] = (self.datarate_particles[p][t]*2000/1048576) / self.consumption_particles[p][t]

        ee_sum = 0
        ee_std_particle = numpy.zeros(shape=(self.NPARTICLES))
        constrait_sum = 0
        constrait_std_particle = numpy.zeros(shape=(self.NPARTICLES))
        for p in range(0, self.NPARTICLES):
            ee_sum += ee_list[p][0]
            constrait_sum += self.datarate_constraint_particles[p][0]
            constrait_std_particle[p] = numpy.std(self.datarate_constraint_particles[p])
            ee_std_particle[p] = numpy.std(ee_list[p])

        mean_ee = ee_sum/self.NPARTICLES
        mean_constrait = constrait_sum/self.NPARTICLES

        for p in range(0, self.NPARTICLES):
            self.beta_particles[p] = math.pow(10, 3*(ee_list[p][0]-mean_ee + (ee_std_particle[p]/ee_list[p][0]) - 0.001))
            self.lambda_particles[p] = math.pow(1.0005, (self.datarate_constraint_particles[p][0]-mean_constrait + (constrait_std_particle[p]/self.datarate_constraint_particles[p][0]) - 0.001))

            # print "EE = ", ee_list[p][0]-mean_ee
            # if ee_list[p][0] < mean_ee and (ee_std_particle[p]/ee_list[p][0]) < 0.001:
            #     self.beta_particles[p] = self.beta_particles[p] * 0.5
            #     #print "Relaxa"
            # elif ee_list[p][0] < mean_ee and (ee_std_particle[p]/ee_list[p][0]) > 0.001:
            #     self.beta_particles[p] = self.beta_particles[p] * 1.5
            #     #print "Prende 1"
            # elif ee_list[p][0] > mean_ee and (ee_std_particle[p]/ee_list[p][0]) > 0.001:
            #     self.beta_particles[p] = self.beta_particles[p] * 2
            #     #print "Prende 2"
 
            # print "Data = ", self.datarate_constraint_particles[p][0]-mean_constrait
            # if self.datarate_constraint_particles[p][0] < mean_constrait and (constrait_std_particle[p]/self.datarate_constraint_particles[p][0]) < 0.001:
            #     self.lambda_particles[p] = self.lambda_particles[p] * 0.9
            #     #print "Relaxa"
            # elif self.datarate_constraint_particles[p][0] < mean_constrait and (constrait_std_particle[p]/self.datarate_constraint_particles[p][0]) > 0.001:
            #     self.lambda_particles[p] = self.lambda_particles[p] * 10
            #     #print "Prende 1"
            # elif self.datarate_constraint_particles[p][0] > mean_constrait and (constrait_std_particle[p]/self.datarate_constraint_particles[p][0]) > 0.001:
            #     self.lambda_particles[p] = self.lambda_particles[p] * 20
            #     #print "Prende 2"

        #TODO: Fazer os ifs

        #self.L_BETA = self.L_BETA * 1.2
        #self.L_BETA = self.L_BETA + 0.1
        #self.L_LAMBDA = self.L_LAMBDA * 1.5
        #self.L_UPSILON = self.L_UPSILON * 2
        #self.E_DEALTA = self.E_DEALTA * 2 


    def interference_calc(self, arb, user, particle ,grid):
        antenna_index = int(arb/Antenna.TOTAL_RBS)
        antenna = grid.antennas[antenna_index]
        rb = arb%Antenna.TOTAL_RBS
        ue = grid.users[user]
        interference = 0
        ant_index = -1
        for ant in grid.antennas:
            ant_index += 1
            if (antenna._id != ant._id):
                arb_index = (ant_index*Antenna.TOTAL_RBS)+rb

                index = numpy.argmax(self.a_particles[particle, :, arb_index])
                if self.a_particles[particle, index, arb_index] > 0 and ue._id != grid.users[index]:
                    R  =  util.dist(ue, ant)
                    interference += abs(util.friis(self.p_particles[particle, index, arb_index], Antenna.T_GAIN, Antenna.R_GAIN, R, Antenna.WAVELENTH))#dBm
                    #print ue._id, ant._id, R, interference, self.p_particles[particle, index, arb_index]

        #print interference
        return interference

    def power_calc(self, arb, user, particle, grid):
        antenna_index = int(arb/Antenna.TOTAL_RBS)
        antenna = grid.antennas[antenna_index]
        ue = grid.users[user]
        R = util.dist(ue, antenna)
        p = util.p_friis(antenna,self.i_particles[particle, user, arb], util.noise(), Antenna.T_GAIN, Antenna.R_GAIN, R, Antenna.WAVELENTH) #dBm
        return p

    def data_rate_and_power_consumption_calc(self, particle, grid):
        self.datarate_user_particles[particle] = numpy.zeros(shape=(len(grid.users)))
        self.consumption_antenna_particles[particle] = numpy.zeros(shape=(len(grid.antennas)))
        datarate_particle = 0
        consumption_particle = 0

        previous_antennas = 0
        previous_consumption = 0
        for arb in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para preencher A
            antenna_index = int(arb/Antenna.TOTAL_RBS)
            antenna = grid.antennas[antenna_index]# Identifica antena 
            user = numpy.argmax(self.a_particles[particle, :, arb])
            if self.a_particles[particle, user, arb] > 0:
                #DATA RATE
                data_bits = (util.shannon((self.a_particles[particle, user, arb] * Antenna.B0), util.sinr(self.p_particles[particle, user, arb], self.i_particles[particle, user, arb], util.noise())))/2000#Qnt de bits em 0,5 ms
                self.datarate_user_particles[particle, user] += data_bits
                #print "Data User: ", str(numpy.matrix(self.datarate_user_particles[particle]))
                datarate_particle += data_bits

                previous_consumption += util.dBm_to_watts(self.a_particles[particle, user, arb] * self.p_particles[particle, user, arb]) 

            #POWER CONSUMPTION
            next_arb_antenna = int((arb+1)/Antenna.TOTAL_RBS)
            if next_arb_antenna > antenna_index or arb == (Antenna.TOTAL_RBS*len(grid.antennas))-1: 
                if (antenna.type == Antenna.BS_ID):
                    self.consumption_antenna_particles[particle, antenna_index]  = (Antenna.MEFF * previous_consumption) + Antenna.PMC + Antenna.PMBH
                else:
                    self.consumption_antenna_particles[particle, antenna_index] = (Antenna.EFF * previous_consumption) + Antenna.PMC + Antenna.PMBH

                consumption_particle += self.consumption_antenna_particles[particle, antenna_index] 
                previous_consumption = 0
        self.datarate_particles[particle] = self.list_append(self.datarate_particles[particle], datarate_particle)
        self.consumption_particles[particle] = self.list_append(self.consumption_particles[particle], consumption_particle)
                
    #def ee_draft_calc(self, a, i, p, grid):


    def fairness_calc(self, p, grid):
        x1 = 0
        x2 = 0
        n = len(grid.users)
        for ue in range(0, len(grid.users)):
            x1 += self.datarate_user_particles[p, ue]
            x2 += math.pow(self.datarate_user_particles[p, ue], 2)
        x1 = math.pow(x1, 2)
        if (x2 == 0):
            return 1

        r = x1/(x2*n)
        return r

    def ee_calc(self, particle, grid):
        self.data_rate_and_power_consumption_calc(particle, grid)
        self.meet_user_particles[particle] = 0
        datarate_constraint_particle = 0
        for ue in range(0, len(grid.users)):
            #print "Datarates : ", self.datarate_constraint_particles[particle], self.datarate_user_particles[particle, ue]
            if grid.users[ue]._type == User.HIGH_RATE_USER: 
                if(self.datarate_user_particles[particle, ue] < Antenna.NR):
                    datarate_constraint_particle += (self.datarate_user_particles[particle, ue] - Antenna.NR)
                else:
                    self.meet_user_particles[particle] += 1
            else:
                if(self.datarate_user_particles[particle, ue] < Antenna.NER):
                    datarate_constraint_particle += (self.datarate_user_particles[particle, ue] - Antenna.NER)
                else:
                    self.meet_user_particles[particle] += 1

        self.datarate_constraint_particles[particle] = self.list_append(self.datarate_constraint_particles[particle], datarate_constraint_particle)            
        #print "EE = ", (self.datarate_particles[particle]*2000/1048576), "/", self.consumption_particles[particle], "+", (self.datarate_constraint_particles[particle]*2000/1048576)
        particle_ee = self.L_BETA * ((self.datarate_particles[particle][0]*2000/1048576) / self.consumption_particles[particle][0]) + (self.L_LAMBDA) * (self.datarate_constraint_particles[particle][0]*2000/1048576)

        #print "EE = ", particle_ee
        return particle_ee


    def covered_users_calc(self, antennas, antenna_index): #ue _anteriores = -1, for ate index: ue anteriores += antennas[x].conected_ues
        ue_anteriores = -1
        for ant in range(0, antenna_index):
            #print "Antenna ", ant
            ue_anteriores += len(antennas[ant].connected_ues)

        #print ue_anteriores
        return ue_anteriores

    def append_ee(self, particle, ee):
        #print particle, ee
        #del lst[-1]
        #lst = ee + lst
        ee_particle = np.delete(self.ee_particles[particle], -1)
        self.ee_particles[particle] = np.append(ee, ee_particle)
        #print self.ee_particles[particle]

    def list_append(self, lista, value):
        lista = np.delete(lista, -1)
        lista = np.append(value, lista)
        return lista


    def define_best_particles(self, grid):
        for i in range(0, int(self.NPARTICLES*self.HISTORY_LENGTH)):
            self.history_datarate_constraint_particles[i][0] = 0
            for ue in range(0, len(grid.users)):
                if grid.users[ue]._type == User.HIGH_RATE_USER: 
                    if(self.history_datarate_user_particles[i, ue]  < Antenna.NR):
                        self.history_datarate_constraint_particles[i][0] += (self.history_datarate_user_particles[i, ue] - Antenna.NR)
                else:
                    if(self.history_datarate_user_particles[i, ue]  < Antenna.NER):
                        self.history_datarate_constraint_particles[i][0] += (self.history_datarate_user_particles[i, ue] - Antenna.NER)
            self.history_ee_particles[i,0] = self.L_BETA * ((self.history_datarate_particles[i][0]*2000/1048576) / self.history_consumption_particles[i][0]) + (self.L_LAMBDA) *(self.history_datarate_constraint_particles[i][0]*2000/1048576)#RECALCULAR A EE BASEADO NO NOVO BETA
        
        for i in range(0, int(self.NPARTICLES*self.HISTORY_LENGTH)):
            index = numpy.argmin(self.ee_particles[:,0])
            if self.history_ee_particles[i,0] > self.ee_particles[index,0]:
                #print "Remove", self.ee_particles[index, 0], "and Restore ", self.history_ee_particles[i,0]
                self.i_particles[index] = self.history_i_particles[i].copy()
                self.a_particles[index] = self.history_a_particles[i].copy()
                self.p_particles[index] = self.history_p_particles[i].copy()
                self.ee_particles[index] = self.history_ee_particles[i].copy()
                self.datarate_particles[index]  = self.history_datarate_particles[i].copy()
                self.consumption_particles[index]  = self.history_consumption_particles[i].copy()
                self.datarate_constraint_particles[index] = self.history_datarate_constraint_particles[i].copy()
                self.datarate_user_particles[index] = self.history_datarate_user_particles[i].copy()
                self.lambda_particles[index] = self.history_lambda_particles[i].copy()
                self.beta_particles[index] = self.history_beta_particles[i].copy()



    def make_history(self):
        ee = self.ee_particles[:,0].copy()
        for i in range(0, int(self.NPARTICLES*self.HISTORY_LENGTH)):
            part = numpy.argmax(ee)
            #print "Dump", ee[part]
            ee[part] = -9999999999999999
            self.history_i_particles[i] = self.i_particles[part].copy()
            self.history_a_particles[i] = self.a_particles[part].copy()
            self.history_p_particles[i] = self.p_particles[part].copy()
            self.history_ee_particles[i] = self.ee_particles[part].copy()
            self.history_datarate_particles[i]  = self.datarate_particles[part].copy()
            self.history_consumption_particles[i]  = self.consumption_particles[part].copy()
            self.history_datarate_constraint_particles[i] = self.datarate_constraint_particles[part].copy()
            self.history_datarate_user_particles[i] = self.datarate_user_particles[part].copy()
            self.history_lambda_particles[i] = self.lambda_particles[part].copy()
            self.history_beta_particles[i] = self.beta_particles[part].copy()


    def is_stable(self, lst):
#        if lst[-1] != 0:
#            mean = numpy.mean(lst)
            #amax = numpy.amax(lst)
            #amin = numpy.amin(lst)
#            std = numpy.std(lst)
#            if std < (mean*self.TX_FLUTUATION):
#                print 'Stable!!'
#                return True

        return False

    def rand_user(self, particle, antenna_index, antenna, covered_users, prob_zero, grid):
        prob_zero = 0
        totalUes = len(antenna.connected_ues)
        for ue in range (covered_users+1, totalUes):
             self.datarate_user_particles[particle, ue] = 0

        for rb in range(0, Antenna.TOTAL_RBS):# Loop de K * M para preencher A
            arb = (antenna_index*Antenna.TOTAL_RBS-1)+rb
            user = numpy.argmax(self.a_particles[particle, :, arb])
            if self.a_particles[particle, user, arb] > 0:
                data_bits = (util.shannon((self.a_particles[particle, user, arb] * Antenna.B0), util.sinr(self.p_particles[particle, user, arb], self.i_particles[particle, user, arb], util.noise())))/2000#Qnt de bits em 0,5 ms
                self.datarate_user_particles[particle, user] += data_bits

        
        probPerUser = numpy.ones(shape=(len(antenna.connected_ues)))
        sum_prob = 0
        #print "Covered_users", covered_users, 
        for ue in range (0, totalUes):
            if grid.users[ue]._type == User.HIGH_RATE_USER: 
                if(self.datarate_user_particles[particle, ue] < Antenna.NR):
                    probPerUser[ue] = sum_prob + (Antenna.NR - self.datarate_user_particles[particle, ue])
            else:
                if(self.datarate_user_particles[particle, ue] < Antenna.NER):
                    probPerUser[ue] = sum_prob + (Antenna.NER - self.datarate_user_particles[particle, ue])
            sum_prob += probPerUser[ue]

        rand = random.randint(int(covered_users-prob_zero), int(covered_users+sum_prob))
        if rand > covered_users:
            for ue in range (0, totalUes):
                if rand <= probPerUser[ue]:
                    #print "return", ue
                    return covered_users + 1 + ue
        else:
            #print "return", rand
            return rand



    def calc_prob_zero(self, particle, antenna_index, antenna, covered_users, grid):
        #print "Prob Zero"
        totalUes = len(antenna.connected_ues)
        meet_users = 0
        for ue in range (covered_users+1, covered_users+totalUes):
            if grid.users[ue]._type == User.HIGH_RATE_USER: 
                if(self.datarate_user_particles[particle, ue] >= Antenna.NR):
                    meet_users += 1
            else:
                if(self.datarate_user_particles[particle, ue] >= Antenna.NER):
                    meet_users += 1

        if (meet_users < totalUes/2):
            return int(totalUes)
        elif (meet_users < totalUes):
            return int(totalUes*2)
        elif (meet_users == totalUes):
            return 1
        else:
            return int(totalUes)
        #return 0


    def exp_ee_calc(self, particle, new_ee, old_ee, new_constraint, old_constraint):
        #prob = math.exp(self.L_BETA*(new_ee-old_ee))
        prob1 = 1
        prob2 = 1
        #if new_constraint > old_constraint:
        if new_ee >= old_ee:
            prob1 = 1
        else:
            delta_ee = new_ee-old_ee
            prob1 = math.exp(self.beta_particles[particle]*delta_ee)
                #prob1 = math.exp(self.L_BETA*delta_ee)

        if new_constraint >= old_constraint:
            prob2 = 1
        else:
            delta_constraint = new_constraint-old_constraint
            prob2 = math.exp((self.lambda_particles[particle])*delta_constraint)
            #prob2 = math.exp((self.L_BETA)*delta_constraint)

        prob = prob1 * prob2
        #print prob, prob1, prob2
        return prob

    def run(self, grid):
        acceppt = 0
        not_acceppt = 0
        self.history_a_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.history_p_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.history_i_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.history_ee_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH), self.STABLE_STEPS_LENGTH))
        self.history_datarate_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),10))
        self.history_consumption_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),10))
        self.history_datarate_constraint_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),10))
        self.history_datarate_user_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH), len(grid.users)))
        self.lambda_particles = numpy.ones(shape=(self.NPARTICLES))
        self.beta_particles = numpy.ones(shape=(self.NPARTICLES))
        self.history_lambda_particles = numpy.ones(shape=(self.NPARTICLES))
        self.history_beta_particles = numpy.ones(shape=(self.NPARTICLES))
        self.i_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.a_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.p_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.ee_particles = numpy.zeros(shape=(self.NPARTICLES, self.STABLE_STEPS_LENGTH))
        self.stable_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.meet_user_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.datarate_user_particles = numpy.zeros(shape=(self.NPARTICLES, len(grid.users)))
        self.consumption_antenna_particles = numpy.zeros(shape=(self.NPARTICLES, len(grid.antennas)))
        
        self.datarate_particles = numpy.zeros(shape=(self.NPARTICLES,10))
        self.consumption_particles = numpy.zeros(shape=(self.NPARTICLES,10))
        self.datarate_constraint_particles = numpy.zeros(shape=(self.NPARTICLES,10))
 
        grid = associate_user_in_antennas(grid)

        # print "Users GRID"

        # for gridUe in grid.users:
        #     print gridUe._id
            
        # print "Users ANTENNAS"
        # for antenna in grid.antennas:
        #     for ueAnt in antenna.connected_ues:  
        #         print ueAnt._id

        # print "Users FIM"          

        # Loop maximo de itaracoes
        #while stabilized_particles < self.NPARTICLES and step < self.MC_STEPS:
        for step in range (0, self.MC_STEPS):
            print "REP: ", self.repeticao, " I:", step
            acceppt = 0
            not_acceppt = 0
            init = time.time()
            gc.collect() #Liberar memoria
            if(step == 0):
                # Loop sobre as particulas
                for p in range(0, self.NPARTICLES):
                    for stepezinho in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para preencher A
                        arb = random.randint(0, Antenna.TOTAL_RBS*len(grid.antennas)-1)
                        u = numpy.argmax(self.a_particles[p, :, arb])
                        if(self.a_particles[p, u, arb] == 0):
                            antenna_index = int(arb/Antenna.TOTAL_RBS)
                            antenna = grid.antennas[antenna_index]# Identifica antena 
                            if len(antenna.connected_ues) > 0:
                                covered_users = self.covered_users_calc(grid.antennas, antenna_index)
                                probZero = self.calc_prob_zero(p, antenna_index, antenna, covered_users, grid)
                                #user = random.randint(covered_users-probZero, covered_users+len(antenna.connected_ues)) #Seleciona de forma aletoria um usuario valido para a antenna
                                user = self.rand_user(p, antenna_index, antenna, covered_users, probZero, grid)
                                if user > covered_users: # Se usuario nao for zero
                                    self.a_particles[p, user, arb] = 1 # Seleta 1 para o estado 
                                    self.i_particles[p, user, arb] = self.interference_calc(arb, user, p, grid)
                                    self.p_particles[p, user, arb] = self.power_calc(arb, user, p, grid)

                    # for arb in range(0, Antenna.TOTAL_RBS*len(grid.antennas)-1):# Loop de K * M para calcular I e P
                    #     user = numpy.argmax(self.a_particles[p, :, arb])
                    #     if self.a_particles[p, user, arb] > 0:
                    #         self.i_particles[p, user, arb] = self.interference_calc(arb, user, p, grid)
                    #         isum += self.i_particles[p, user, arb]
                    #         self.p_particles[p, user, arb] = self.power_calc(arb, user, p, grid)                    

                    ee_particle = self.ee_calc(p, grid)
                    self.append_ee(p, ee_particle)
                self.make_history()
            else:
                for p in range(0, self.NPARTICLES):

                    current_ee_particle = self.ee_particles[p,0]
                    current_datarate_constraint = self.datarate_constraint_particles[p][0]
                    for stepezinho in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):
                        random_arb = random.randint(0, Antenna.TOTAL_RBS*len(grid.antennas)-1)
                        antenna_index = int(random_arb/Antenna.TOTAL_RBS)
                        antenna = grid.antennas[antenna_index]# Identifica antena 
                        
                        while len(antenna.connected_ues) == 0:
                            random_arb = random.randint(0, Antenna.TOTAL_RBS*len(grid.antennas)-1)
                            antenna_index = int(random_arb/Antenna.TOTAL_RBS)
                            antenna = grid.antennas[antenna_index]

                        covered_users = self.covered_users_calc(grid.antennas, antenna_index) #ue _anteriores = -1, for ate index: ue anteriores += antennas[x].conected_ues
                        probZero = self.calc_prob_zero(p, antenna_index, antenna, covered_users, grid)
                        #print probZero, covered_users-probZero, covered_users+len(antenna.connected_ues)
                        #user = random.randint(covered_users-probZero, covered_users+len(antenna.connected_ues)) #Seleciona de forma aletoria um usuario valido para a antenna
                        user = user = self.rand_user(p, antenna_index, antenna, covered_users, probZero, grid)
                        previous_user = numpy.argmax(self.a_particles[p,:,random_arb])
                       
                        if(self.a_particles[p, previous_user, random_arb] > 0):
                            self.a_particles[p, previous_user, random_arb] = 0
                            self.i_particles[p, previous_user, random_arb] = 0
                            self.p_particles[p, previous_user, random_arb] = 0
                        else:
                            previous_user = -1

                        if user > covered_users: # Se usuario nao for zero e for diferente do anterior
                            self.a_particles[p, user, random_arb] = 1 # Seleta 1 para o estado 
                            self.i_particles[p, user, random_arb] = self.interference_calc(random_arb, user, p, grid)
                            self.p_particles[p, user, random_arb] = self.power_calc(random_arb, user, p, grid) 

                        for arb in range((random_arb%Antenna.TOTAL_RBS), Antenna.TOTAL_RBS*len(grid.antennas), Antenna.TOTAL_RBS):# Loop de K * M para calcular I e P
                            current_user = numpy.argmax(self.a_particles[p,:, arb])
                            if self.a_particles[p, current_user, arb] > 0:
                                self.i_particles[p, current_user, arb] = self.interference_calc(arb, current_user, p, grid)
                                self.p_particles[p, current_user, arb] = self.power_calc(arb, current_user, p, grid) 

                        
                        new_ee_particle = self.ee_calc(p, grid)
                        new_datarate_constraint = self.datarate_constraint_particles[p][0]
                        prob = self.exp_ee_calc(p, new_ee_particle, current_ee_particle, new_datarate_constraint, current_datarate_constraint)
                        rand = random.uniform(0.0, 1.0)
                        if rand <= prob:
                            current_ee_particle = new_ee_particle
                            #print "Accept"
                        else:
                            #print "Not Accept"
                            if user > covered_users:
                                if(self.a_particles[p, user, random_arb] > 0):
                                    self.a_particles[p, user, random_arb] = 0
                                    self.i_particles[p, user, random_arb] = 0
                                    self.p_particles[p, user, random_arb] = 0
                            if previous_user > 0:
                                self.a_particles[p, previous_user, random_arb] = 1 # Seleta 1 para o estado 
                                self.i_particles[p, previous_user, random_arb] = self.interference_calc(random_arb, previous_user, p, grid)
                                self.p_particles[p, previous_user, random_arb] = self.power_calc(random_arb, previous_user, p, grid) 

                            for arb in range((random_arb%Antenna.TOTAL_RBS), Antenna.TOTAL_RBS*len(grid.antennas), Antenna.TOTAL_RBS):# Loop de K * M para calcular I e P
                                current_user = numpy.argmax(self.a_particles[p,:, arb])
                                if self.a_particles[p, current_user, arb] > 0:
                                    self.i_particles[p, current_user, arb] = self.interference_calc(arb, current_user, p, grid)
                                    self.p_particles[p, current_user, arb] = self.power_calc(arb, current_user, p, grid)

                            self.ee_particles[p,0] = self.ee_calc(p, grid)

                    ee_particle = self.ee_calc(p, grid)
                    self.append_ee(p, ee_particle)

                        #if current_ee_particle != self.ee_particles[p,0]:
                        #    self.append_ee(p, new_ee_particle)

                        #if self.is_stable(self.ee_particles[p]):
                        #    self.stable_particles[p] = 1
                        #    stabilized_particles += 1
                        #else:
                        #    if self.stable_particles[p] == 1:
                        #        self.stable_particles[p] = 0
                        #       stabilized_particles -= 1

                        #print "Particula", p,"total aceitos = ", acceppt, " contra", not_acceppt, "nao aceitos."
                        #if self.meet_user_particles[p] < 15:
                        #    self.MC_STEPS += 1
                        #else:
                        #    step = self.MC_STEPS
                    
                self.define_best_particles(grid)
                self.make_history()
                      
            if step % 2 == 0:
                self.raises_temperature()
            best_particle = self.select_best_particle(grid)
            fairness = self.fairness_calc(best_particle, grid)
            isum = 0
            used_rbs = 0
            for arb in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):
                for ue in range(0, len(grid.users)):
                    antenna_index = int(arb/Antenna.TOTAL_RBS)
                    antenna = grid.antennas[antenna_index]# Identifica antena 
                    if (self.a_particles[best_particle, ue, arb] != 0):
                        self.i_particles[best_particle, ue, arb] = self.interference_calc(arb, ue, best_particle, grid)
                        isum += self.a_particles[best_particle, ue, arb]*self.i_particles[best_particle, ue, arb]
                        used_rbs += self.a_particles[best_particle, ue, arb]


            #print isum, "/", used_rbs
            #print 'TotalRbs:', str(Antenna.TOTAL_RBS*len(grid.antennas)), "UsedRbs:", str(used_rbs), "Imean", str(isum/used_rbs), "EE:", str(self.ee_particles[best_particle,0]), "MU:", str(self.meet_user_particles[best_particle]), "C:", str(self.datarate_particles[best_particle,0]), "P:", str(self.consumption_particles[best_particle,0])

            f = open('resumo.csv','a')
            f.write('MC(B:'+str(self.delta1)+'L:'+str(self.delta2)+'),MC['+str(len(grid.bs_list))+'-'+str(len(grid.rrh_list))+'-'+str(len(grid.users))+'],'+str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid.users))+','+str(self.repeticao)+','+str(step)+','+str(self.datarate_particles[best_particle,0])+','+str(self.consumption_particles[best_particle,0])+','+str(self.ee_particles[best_particle,0])+','+str(self.meet_user_particles[best_particle])+','+str(fairness)+','+str(time.time()-init)+'\n')
            f.close()

            debug_printf("----- GRID step "+str(step+1)+" -----")
            debug_printf("Alloc = \n" + str(numpy.matrix(self.a_particles[best_particle])))
            debug_printf("Power = \n" + str(numpy.matrix(self.p_particles[best_particle])))
            debug_printf("Noise = \n" + str(numpy.matrix(self.i_particles[best_particle])))
            #step = step + 1


















