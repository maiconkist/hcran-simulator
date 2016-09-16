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
    def __init__(self, r, delta1, delta2):
        self.delta1 = delta1
        self.delta2 = delta2
        self.repeticao = r
        self.MC_STEPS = 25
        self.STABLE_STEPS_LENGTH = 10
        self.NPARTICLES   = 100
        self.HISTORY_LENGTH = 0.05
        self.RESETRATE    = 0.01
        self.L_BETA       = delta1
        self.L_LAMBDA     = delta2
        #self.L_UPSILON    = 0.1
        #self.E_DEALTA     = 0.2
        self.TX_FLUTUATION = 0.2
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
        

    def raises_temperature(self):
        self.L_BETA = self.L_BETA * 2
        #self.L_BETA = self.L_BETA + 0.1
        self.L_LAMBDA = self.L_LAMBDA * 2
        #self.L_UPSILON = self.L_UPSILON * 2
        #self.E_DEALTA = self.E_DEALTA * 2 


    def interference_calc(self, arb, user, particle ,grid):
            antenna_index = int(arb/Antenna.TOTAL_RBS)
            antenna = grid.antennas[antenna_index]
            ue = grid.users[user]
            interference = 0
            for rb in range((arb%Antenna.TOTAL_RBS), Antenna.TOTAL_RBS*len(grid.antennas), Antenna.TOTAL_RBS):
                if rb != arb:
                    ant_index = int(rb/Antenna.TOTAL_RBS)
                    ant = grid.antennas[ant_index]
                    current_user = numpy.argmax(self.a_particles[particle, :, rb])
                    if self.a_particles[particle, current_user, rb] > 0:
                        R  =  util.dist(ue, ant)
                        interference += abs(util.friis(self.p_particles[particle, current_user, rb], Antenna.T_GAIN, Antenna.R_GAIN, R, Antenna.WAVELENTH))#dBm
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
        #print "Data User (zero): ", str(numpy.matrix(self.datarate_user_particles[particle]))
        self.datarate_particles[particle] = 0
        
        self.consumption_antenna_particles[particle] = numpy.zeros(shape=(len(grid.antennas)))
        self.consumption_particles[particle] = 0

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
                self.datarate_particles[particle] += data_bits

                previous_consumption += util.dBm_to_watts(self.a_particles[particle, user, arb] * self.p_particles[particle, user, arb]) 

            #POWER CONSUMPTION
            next_arb_antenna = int((arb+1)/Antenna.TOTAL_RBS)
            if next_arb_antenna > antenna_index or arb == (Antenna.TOTAL_RBS*len(grid.antennas))-1: 
                if (antenna.type == Antenna.BS_ID):
                    self.consumption_antenna_particles[particle, antenna_index]  = (Antenna.MEFF * previous_consumption) + Antenna.PMC + Antenna.PMBH
                else:
                    self.consumption_antenna_particles[particle, antenna_index] = (Antenna.EFF * previous_consumption) + Antenna.PMC + Antenna.PMBH

                self.consumption_particles[particle] += self.consumption_antenna_particles[particle, antenna_index] 
                previous_consumption = 0

                
    #def ee_draft_calc(self, a, i, p, grid):


    def fairness_calc(self, p, grid):
        x1 = 0
        x2 = 0
        n = len(grid.users)
        for ue in range(0, len(grid.users)):
            x1 +=  self.datarate_user_particles[p, ue]
            x2 += math.pow(self.datarate_user_particles[p, ue], 2)
        x1 = math.pow(x1, 2)
        r = x1/(x2*n)
        return r

    def ee_calc(self, particle, grid):
        self.data_rate_and_power_consumption_calc(particle, grid)
        self.meet_user_particles[particle] = 0
        self.datarate_constraint_particles[particle] = 0
        for ue in range(0, len(grid.users)):
            #print "Datarates : ", self.datarate_constraint_particles[particle], self.datarate_user_particles[particle, ue]
            if grid.users[ue]._type == User.HIGH_RATE_USER: 
                if(self.datarate_user_particles[particle, ue] < Antenna.NR):
                    self.datarate_constraint_particles[particle] += (self.L_LAMBDA) * (self.datarate_user_particles[particle, ue] - Antenna.NR)
                else:
                    self.meet_user_particles[particle] += 1
            else:
                if(self.datarate_user_particles[particle, ue] < Antenna.NER):
                    self.datarate_constraint_particles[particle] += (self.L_LAMBDA) * (self.datarate_user_particles[particle, ue] - Antenna.NER)
                else:
                    self.meet_user_particles[particle] += 1


        #print "EE = ", (self.datarate_particles[particle]*2000/1048576), "/", self.consumption_particles[particle], "+", (self.datarate_constraint_particles[particle]*2000/1048576)
        particle_ee = self.L_BETA * ((self.datarate_particles[particle]*2000/1048576) / self.consumption_particles[particle]) + (self.datarate_constraint_particles[particle]*2000/1048576)

        #print "EE = ", particle_ee
        return particle_ee


    def covered_users_calc(self, antennas, antenna_index): #ue _anteriores = -1, for ate index: ue anteriores += antennas[x].conected_ues
        ue_anteriores = -1
        for ant in range(0, antenna_index):
            ue_anteriores += len(antennas[ant].connected_ues)

        return ue_anteriores

    def append_ee(self, particle, ee):
        #print particle, ee
        #del lst[-1]
        #lst = ee + lst
        ee_particle = np.delete(self.ee_particles[particle], -1)
        self.ee_particles[particle] = np.append(ee, ee_particle)
        #print self.ee_particles[particle]


    def define_best_particles(self, grid):
        for i in range(0, int(self.NPARTICLES*self.HISTORY_LENGTH)):
            for ue in range(0, len(grid.users)):
                if grid.users[ue]._type == User.HIGH_RATE_USER: 
                    self.history_datarate_constraint_particles[i] += (self.L_LAMBDA) * (self.history_datarate_user_particles[i, ue] - Antenna.NR)
                else:
                    self.history_datarate_constraint_particles[i] += (self.L_LAMBDA) * (self.history_datarate_user_particles[i, ue] - Antenna.NER)
            self.history_ee_particles[i,0] = self.L_BETA * ((self.history_datarate_particles[i]*2000/1048576) / self.history_consumption_particles[i]) + (self.history_datarate_constraint_particles[i]*2000/1048576)#RECALCULAR A EE BASEADO NO NOVO BETA
        
        for i in range(0, int(self.NPARTICLES*self.HISTORY_LENGTH)):
            index = numpy.argmin(self.ee_particles[:,0])
            if self.history_ee_particles[i,0] > self.ee_particles[index,0]:
                self.i_particles[index] = self.history_i_particles[i].copy()
                self.a_particles[index] = self.history_a_particles[i].copy()
                self.p_particles[index] = self.history_p_particles[i].copy()
                self.ee_particles[index] = self.history_ee_particles[i].copy()
                self.datarate_particles[index]  = self.history_datarate_particles[i].copy()
                self.consumption_particles[index]  = self.history_consumption_particles[i].copy()
                self.datarate_constraint_particles[index] = self.history_datarate_constraint_particles[i].copy()
                self.datarate_user_particles[index] = self.history_datarate_user_particles[i].copy()



    def make_history(self):
        ee = self.ee_particles[:,0].copy()
        for i in range(0, int(self.NPARTICLES*self.HISTORY_LENGTH)):
            part = numpy.argmax(ee)
            ee[part] = -99999999
            self.history_i_particles[i] = self.i_particles[part].copy()
            self.history_a_particles[i] = self.a_particles[part].copy()
            self.history_p_particles[i] = self.p_particles[part].copy()
            self.history_ee_particles[i] = self.ee_particles[part].copy()
            self.history_datarate_particles[i]  = self.datarate_particles[part].copy()
            self.history_consumption_particles[i]  = self.consumption_particles[part].copy()
            self.history_datarate_constraint_particles[i] = self.datarate_constraint_particles[part].copy()
            self.history_datarate_user_particles[i] = self.datarate_user_particles[part].copy()


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

    def exp_ee_calc(self, new_ee, old_ee, new_constraint, old_constraint):
        #prob = math.exp(self.L_BETA*(new_ee-old_ee))
        prob1 = 0
        prob2 = 0
        if new_ee > old_ee:
            prob1 = 1
        else:
            delta_ee = new_ee-old_ee
            prob1 = math.exp(self.L_BETA*delta_ee)

        if new_constraint > old_constraint:
            prob2 = 1
        else:
            delta_constraint = new_constraint-old_constraint
            prob2 = math.exp((self.L_LAMBDA)*delta_constraint)

        prob = prob1 * prob2
        return prob

    def run(self, grid):
        acceppt = 0
        not_acceppt = 0
        self.history_a_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.history_p_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.history_i_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH),len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.history_ee_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH), self.STABLE_STEPS_LENGTH))
        self.history_datarate_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH)))
        self.history_consumption_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH)))
        self.history_datarate_constraint_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH)))
        self.history_datarate_user_particles = numpy.zeros(shape=(int(self.NPARTICLES*self.HISTORY_LENGTH), len(grid.users)))
        self.datarate_constraint_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.i_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.a_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.p_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.ee_particles = numpy.zeros(shape=(self.NPARTICLES, self.STABLE_STEPS_LENGTH))
        self.stable_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.meet_user_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.datarate_user_particles = numpy.zeros(shape=(self.NPARTICLES, len(grid.users)))
        self.datarate_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.consumption_antenna_particles = numpy.zeros(shape=(self.NPARTICLES, len(grid.antennas)))
        self.consumption_particles = numpy.zeros(shape=(self.NPARTICLES))

        associate_user_in_antennas(grid.users, grid.antennas)



        step = 0
        stabilized_particles = 0
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
                    covered_users = -1
                    previous_antennas = 0
                    for arb in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para preencher A
                        antenna_index = int(arb/Antenna.TOTAL_RBS)
                        antenna = grid.antennas[antenna_index]# Identifica antena 
                        if antenna_index > previous_antennas:
                            #print "Nova antenna"
                            previous_antennas += 1
                            antenna_ant = grid.antennas[antenna_index-1]#
                            #print covered_users, len(antenna_ant.connected_ues)
                            covered_users += len(antenna_ant.connected_ues)
                            #print covered_users
                        if len(antenna.connected_ues) > 0:
                            user = random.randint(covered_users, covered_users+len(antenna.connected_ues)) #Seleciona de forma aletoria um usuario valido para a antenna
                            #print user, "= randon", covered_users, covered_users+len(antenna.connected_ues)
                            if user > covered_users: # Se usuario nao for zero
                                #print "Setando 1"
                                self.a_particles[p, user, arb] = 1 # Seleta 1 para o estado 
                                self.i_particles[p, user, arb] = self.interference_calc(arb, user, p, grid)
                                self.p_particles[p, user, arb] = self.power_calc(arb, user, p, grid)

                    for arb in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para calcular I e P
                        user = numpy.argmax(self.a_particles[p, :, arb])
                        if self.a_particles[p, user, arb] > 0:
                            self.i_particles[p, user, arb] = self.interference_calc(arb, user, p, grid)
                            self.p_particles[p, user, arb] = self.power_calc(arb, user, p, grid)                    

                    ee_particle = self.ee_calc(p, grid)
                    self.append_ee(p, ee_particle)
                self.make_history()
            else:
                for p in range(0, self.NPARTICLES):
                    if (step-1) % 2 == 0:
                        new_ee_particle = self.ee_calc(p, grid)
                        self.append_ee(p, new_ee_particle)

                    if self.stable_particles[p] < 1:
                        #self.append_ee(p, self.ee_particles[p,0])
                        current_ee_particle = self.ee_particles[p,0]
                        current_datarate_constraint = self.datarate_constraint_particles[p]
                        for stepezinho in range(0, Antenna.TOTAL_RBS*len(grid.antennas)):
                            random_arb = random.randint(0, Antenna.TOTAL_RBS*len(grid.antennas)-1)
                            #print "random_arb = ", random_arb, 0, Antenna.TOTAL_RBS*len(grid.antennas)-1
                            antenna_index = int(random_arb/Antenna.TOTAL_RBS)
                            #print "antenna_index = ", antenna_index
                            antenna = grid.antennas[antenna_index]# Identifica antena 
                            
                            while len(antenna.connected_ues) == 0:
                                random_arb = random.randint(0, Antenna.TOTAL_RBS*len(grid.antennas)-1)
                                antenna_index = int(random_arb/Antenna.TOTAL_RBS)
                                antenna = grid.antennas[antenna_index]
                                #print "antenna_index = ", antenna_index

                            covered_users = self.covered_users_calc(grid.antennas, antenna_index) #ue _anteriores = -1, for ate index: ue anteriores += antennas[x].conected_ues
                            #print "Covered users", covered_users
                            user = random.randint(covered_users, covered_users+len(antenna.connected_ues)) #Seleciona de forma aletoria um usuario valido para a antenna
                            #old_a_particle = deepcopy(self.a_particles[p])
                            #old_i_particle = deepcopy(self.i_particles[p])
                            #old_p_particle = deepcopy(self.p_particles[p])
                            previous_user = numpy.argmax(self.a_particles[p,:,random_arb])
                            #print "Usuario anterior", previous_user
                            self.a_particles[p, previous_user, random_arb] = 0
                            self.i_particles[p, previous_user, random_arb] = 0
                            self.p_particles[p, previous_user, random_arb] = 0
                            if user > covered_users: # Se usuario nao for zero e for diferente do anterior
                                    #print "Seleta 1 para o estado", user, random_arb
                                    self.a_particles[p, user, random_arb] = 1 # Seleta 1 para o estado 
                                    self.i_particles[p, user, random_arb] = self.interference_calc(random_arb, user, p, grid)
                                    self.p_particles[p, user, random_arb] = self.power_calc(random_arb, user, p, grid) 

                            for arb in range((random_arb%Antenna.TOTAL_RBS), Antenna.TOTAL_RBS*len(grid.antennas), Antenna.TOTAL_RBS):# Loop de K * M para calcular I e P
                                current_user = numpy.argmax(self.a_particles[p,:, arb])
                                if self.a_particles[p, current_user, arb] > 0:
                                    self.i_particles[p, current_user, arb] = self.interference_calc(arb, current_user, p, grid)
                                    self.p_particles[p, current_user, arb] = self.power_calc(arb, current_user, p, grid) 

                            
                            new_ee_particle = self.ee_calc(p, grid)
                            new_datarate_constraint = self.datarate_constraint_particles[p]
                            prob = self.exp_ee_calc(new_ee_particle, current_ee_particle, new_datarate_constraint, current_datarate_constraint)
                            rand = random.uniform(0.0, 1.0)
                            #print "Rand = ", rand
                            #print "Prob = ", prob
                            if rand <= prob:
                                #print "Acceppt"
                                #print "\nMELHOROU!!!\n"
                                acceppt += 1
                                #self.append_ee(p, new_ee_particle)
                                current_ee_particle = new_ee_particle
                            else:
                                #print "Not Acceppt"
                                not_acceppt += 1
                                self.a_particles[p, user, random_arb] = 0
                                self.i_particles[p, user, random_arb] = 0
                                self.p_particles[p, user, random_arb] = 0
                                self.a_particles[p, previous_user, random_arb] = 1 # Seleta 1 para o estado 
                                self.i_particles[p, previous_user, random_arb] = self.interference_calc(random_arb, previous_user, p, grid)
                                self.p_particles[p, previous_user, random_arb] = self.power_calc(random_arb, previous_user, p, grid) 

                                for arb in range((random_arb%Antenna.TOTAL_RBS), Antenna.TOTAL_RBS*len(grid.antennas), Antenna.TOTAL_RBS):# Loop de K * M para calcular I e P
                                    current_user = numpy.argmax(self.a_particles[p,:, arb])
                                    if self.a_particles[p, current_user, arb] > 0:
                                        self.i_particles[p, current_user, arb] = self.interference_calc(arb, current_user, p, grid)
                                        self.p_particles[p, current_user, arb] = self.power_calc(arb, current_user, p, grid)

                                self.ee_calc(p, grid)

                        if current_ee_particle != self.ee_particles[p,0]:
                            self.append_ee(p, new_ee_particle)

                        if self.is_stable(self.ee_particles[p]):
                            self.stable_particles[p] = 1
                            stabilized_particles += 1
                        else:
                            if self.stable_particles[p] == 1:
                                self.stable_particles[p] = 0
                                stabilized_particles -= 1

                        #print "Particula", p,"total aceitos = ", acceppt, " contra", not_acceppt, "nao aceitos."
                        #if self.meet_user_particles[p] < 15:
                        #    self.MC_STEPS += 1
                        #else:
                        #    step = self.MC_STEPS
                self.define_best_particles(grid)
                self.make_history()
            if step % 2 == 0:
                self.raises_temperature()

            best_particle = numpy.argmax(self.ee_particles[:,0])
            debug_printf("----- GRID step "+str(step+1)+" -----")
            debug_printf("Alloc = \n" + str(numpy.matrix(self.a_particles[best_particle])))
            debug_printf("Power = \n" + str(numpy.matrix(self.p_particles[best_particle])))
            debug_printf("Noise = \n" + str(numpy.matrix(self.i_particles[best_particle])))
            #f.write('ALG,CASE,M,S,U,R,I,C,P,EE,MU,T\n')
            fairness = self.fairness_calc(best_particle, grid)


            f = open('resumo.csv','a')
            f.write('MC(B:'+str(self.delta1)+'L:'+str(self.delta2)+'),MC['+str(len(grid.bs_list))+'-'+str(len(grid.rrh_list))+'-'+str(len(grid.users))+'],'+str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid.users))+','+str(self.repeticao)+','+str(step)+','+str(self.datarate_particles[best_particle])+','+str(self.consumption_particles[best_particle])+','+str(self.ee_particles[best_particle,0])+','+str(self.meet_user_particles[best_particle])+','+str(fairness)+','+str(time.time()-init)+'\n')
            f.close()
            #step = step + 1























#            for nAntennas in range(0, len(antennas)):
#                if len(antennas[nAntennas].connected_ues) > 0:   
#                    if(i == 0):
#                        debug_printf("\n##########################\n## STARTING MONTE CARLO ##\n##########################\n")
#                        antennas[nAntennas].init_mc(antennas, nAntennas)
#                        antennas[nAntennas].obtain_interference_and_power(grid)
#                        # Generating the first particles
#                        antennas[nAntennas].mc_initial_particles()
#                    else:
#                        antennas[nAntennas].obtain_interference_and_power(grid)
#                        antennas[nAntennas].mc_spinning_roulette()
#                        antennas[nAntennas].mc_backup_particles()
#                        antennas[nAntennas].mc_clean_variables()
#                        antennas[nAntennas].mc_raises_temperature()
#                        antennas[nAntennas].mc_new_particles_generation()
#                    wait()
#                        
#                    antennas[nAntennas].mc_select_current_solution()
#                    antennas[nAntennas].obtain_energy_efficient()
#                    antennas[nAntennas].toString()
#                    wait()
#            grid.write_to_resume('MC', self.repeticao, i+1, time.time()-init)


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

