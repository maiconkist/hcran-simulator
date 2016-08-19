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
    def __init__(self, r):
        self.repeticao = r
        self.MC_STEPS = 10
        self.DELTA_HISTORY = 10
        self.NPARTICLES   = 1000
        self.HISTORICALRATE = 0.2
        self.RESETRATE    = 0.01
        self.L_BETA       = 0.0
        self.L_LAMBDA     = 0.1
        self.L_UPSILON    = 0.1
        self.E_DEALTA     = 0.2
        self.TX_FLUTUATION = 0.2
        self.i_particles = None
        self.a_particles = None
        self.p_particles = None
        self.ee_particles = None
        self.stable_particles = None
        self.meet_user_particles = None
        self.data_rate_user_particles = None
        self.data_rate_particles = None
        self.consumption_antenna_particles = None
        self.consumption_particles = None

    def raises_temperature(self):
        self.L_BETA = self.L_BETA + 0.1
        #self.L_LAMBDA = self.L_LAMBDA * 2
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
        self.data_rate_user_particles[particle] = numpy.zeros(shape=(len(grid.users)))
        #print "Data User (zero): ", str(numpy.matrix(self.data_rate_user_particles[particle]))
        self.data_rate_particles[particle] = 0
        
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
                self.data_rate_user_particles[particle, user] += data_bits
                #print "Data User: ", str(numpy.matrix(self.data_rate_user_particles[particle]))
                self.data_rate_particles[particle] += data_bits

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


                


    def ee_calc(self, particle, grid):
        self.data_rate_and_power_consumption_calc(particle, grid)
        self.meet_user_particles[particle] = 0
        data_rate_constraint = 0
        for ue in range(0, len(grid.users)):
            #print "Datarates : ", data_rate_constraint, self.data_rate_user_particles[particle, ue]
            if grid.users[ue]._type == User.HIGH_RATE_USER: 
                #data_rate_constraint += self.L_BETA * (self.data_rate_user_particles[particle, ue] - Antenna.NR)
                #if(self.data_rate_user_particles[particle, ue] > Antenna.NR):
                #    self.meet_user_particles[particle] += 1
                
                if(self.data_rate_user_particles[particle, ue] < Antenna.NR):
                    data_rate_constraint += self.L_BETA * (self.data_rate_user_particles[particle, ue] - Antenna.NR)
                else:
                    self.meet_user_particles[particle] += 1
            else:
                #data_rate_constraint += self.L_BETA * (self.data_rate_user_particles[particle, ue] - Antenna.NER)
                #f(self.data_rate_user_particles[particle, ue] > Antenna.NER):
                #    self.meet_user_particles[particle] += 1
                if(self.data_rate_user_particles[particle, ue] < Antenna.NER):
                    data_rate_constraint += self.L_BETA * (self.data_rate_user_particles[particle, ue] - Antenna.NER)
                else:
                    self.meet_user_particles[particle] += 1


        #print "EE = ", (self.data_rate_particles[particle]*2000/1048576), "/", self.consumption_particles[particle], "+", (data_rate_constraint*2000/1048576)
        particle_ee = ((self.data_rate_particles[particle]*2000/1048576) / self.consumption_particles[particle]) + (data_rate_constraint*2000/1048576)

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

    def exp_ee_calc(self, new_ee, old_ee):
        #Y = (100 *self.L_BETA)^(old_e-new_ee* 10 * self.L_BETA)
        #print "Y = (100 *",self.L_BETA,")^(",old_e, "-", new_ee, "* 10 *", self.L_BETA,") = ", 
        #print new_ee, old_ee, self.L_BETA
        Y = 1-(abs(1-(new_ee/old_ee))*math.exp(2*self.L_BETA))
        #print "Y = 1-((1-(",new_ee,"/",old_ee,"))*",math.exp(2*self.L_BETA),") = ", Y
        return Y

    def run(self, grid):
        acceppt = 0
        not_acceppt = 0
        self.i_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.a_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.p_particles = numpy.zeros(shape=(self.NPARTICLES,len(grid.users), Antenna.TOTAL_RBS*len(grid.antennas)))
        self.ee_particles = numpy.zeros(shape=(self.NPARTICLES, self.DELTA_HISTORY))
        self.stable_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.meet_user_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.data_rate_user_particles = numpy.zeros(shape=(self.NPARTICLES, len(grid.users)))
        self.data_rate_particles = numpy.zeros(shape=(self.NPARTICLES))
        self.consumption_antenna_particles = numpy.zeros(shape=(self.NPARTICLES, len(grid.antennas)))
        self.consumption_particles = numpy.zeros(shape=(self.NPARTICLES))

        associate_user_in_antennas(grid.users, grid.antennas)



        step = 0
        stabilized_particles = 0
        # Loop maximo de itaracoes
        while stabilized_particles < self.NPARTICLES and step < self.MC_STEPS:
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
            else:
                for p in range(0, self.NPARTICLES):
                    if (step-1) % 10 == 0:
                        new_ee_particle = self.ee_calc(p, grid)
                        self.append_ee(p, new_ee_particle)

                    if self.stable_particles[p] < 1:
                        #self.append_ee(p, self.ee_particles[p,0])
                        current_ee_particle = self.ee_particles[p,0]
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
                            if new_ee_particle > current_ee_particle:
                                #print "\nMELHOROU!!!\n"
                                acceppt += 1
                                #self.append_ee(p, new_ee_particle)
                                current_ee_particle = new_ee_particle
                            else:
                                #print self.ee_particles[p]
                                exp = self.exp_ee_calc(new_ee_particle, current_ee_particle)
                                rand = random.uniform(0.0, 1.0)
                                #print "if ", rand, "<", exp
                                if rand < exp:
                                    #print "Acceppt"
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

                        if current_ee_particle != self.ee_particles[p,0]:
                            self.append_ee(p, new_ee_particle)

                        if self.is_stable(self.ee_particles[p]):
                            self.stable_particles[p] = 1
                            stabilized_particles += 1
                        else:
                            if self.stable_particles[p] == 1:
                                self.stable_particles[p] = 0
                                stabilized_particles -= 1

                        print "Particula", p,"total aceitos = ", acceppt, " contra", not_acceppt, "nao aceitos."
                        #if self.meet_user_particles[p] < 15:
                        #    self.MC_STEPS += 1
                        #else:
                        #    step = self.MC_STEPS

            if step % 10 == 0:
                self.raises_temperature()

            best_particle = numpy.argmax(self.ee_particles[:,0])
            debug_printf("----- GRID step "+str(step+1)+" -----")
            debug_printf("Alloc = \n" + str(numpy.matrix(self.a_particles[best_particle])))
            debug_printf("Power = \n" + str(numpy.matrix(self.p_particles[best_particle])))
            debug_printf("Noise = \n" + str(numpy.matrix(self.i_particles[best_particle])))
            #f.write('ALG,CASE,M,S,U,R,I,C,P,EE,MU,T\n')
            
            f = open('resumo.csv','a')
            f.write('MC,MC['+str(len(grid.bs_list))+'-'+str(len(grid.rrh_list))+'-'+str(len(grid.users))+'],'+str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid.users))+','+str(self.repeticao)+','+str(step)+','+str(self.data_rate_particles[best_particle])+','+str(self.consumption_particles[best_particle])+','+str(self.ee_particles[best_particle,0])+','+str(self.meet_user_particles[best_particle])+','+str(time.time()-init)+'\n')
            f.close()
            step = step + 1























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

