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
import threeGPP
import Calculations as calc

#self.NPARTICLES   = 10000
#self.STABLE_STEPS_LENGTH = 50
#self.HISTORY_LENGTH = 1000
#RESETRATE    = 0.01
L_BETA       = 2  #EE
L_LAMBDA     = 20 #DATARATE
L_UPSILON    = 2  #FAIRNESS
TX_FLUTUATION = 0.001

class RandonMc(object): 
    def __init__(self, r, imax):
        self.REPETICAO = r
        self.MC_STEPS = imax
        self.NPARTICLES = 10000
        self.HISTORY_LENGTH = 1000
        self.STEPS_PER_PARTICLE = 500
        self.STABLE_STEPS_LENGTH = 50
        self.lambda_particles = None
        self.beta_particles = None 
        self.upsilon_particles = None
        self.steps_objective    = None
        self.steps_energy_efficient    = None
        self.steps_weighted_efficient  = None
        self.steps_datarate_constraint = None
        self.steps_fairness_constraint = None
        #self.history_datarate_particles  = None
        #self.history_consumption_particles  = None
        #self.history_datarate_constraint_particles = None
        #self.history_fairness_constraint_particles = None
        #self.history_datarate_user_particles = None
        #self.history_lambda_particles = None
        #self.history_beta_particles = None
        #self.history_upsilon_particles = None
        #self.history_ee_particles = None

    def is_stable(self, data_list):
        std_list = numpy.std(data_list)

        dif = std_list/data_list[0]
        #print dif 
        if (math.isnan(dif) == False and abs(dif) > TX_FLUTUATION) or data_list[-1] == 0:
            #print "Not Stable"
            return False
        #print "Stable"    
        return True


    def run(self, grid):
        self.NPARTICLES = threeGPP.TOTAL_RBS*len(grid.users)
        self.HISTORY_LENGTH = int(0.1 * self.NPARTICLES)
        self.STEPS_PER_PARTICLE = threeGPP.TOTAL_RBS*len(grid.antennas)
        self.STABLE_STEPS_LENGTH = int(0.1 * self.STEPS_PER_PARTICLE)

        grid.energy_efficient           = numpy.zeros(shape=(self.NPARTICLES)) 
        grid.consumition                = numpy.zeros(shape=(self.NPARTICLES))
        grid.datarate                   = numpy.zeros(shape=(self.NPARTICLES))
        grid.fairness                   = numpy.zeros(shape=(self.NPARTICLES))
        grid.meet_users                 = numpy.zeros(shape=(self.NPARTICLES))
        grid.history_weighted_efficient = numpy.zeros(shape=(self.HISTORY_LENGTH))

        self.lambda_particles           = numpy.ones(shape=(self.NPARTICLES))
        self.upsilon_particles          = numpy.ones(shape=(self.NPARTICLES))
        self.beta_particles             = numpy.ones(shape=(self.NPARTICLES))
        self.steps_energy_efficient     = numpy.zeros(shape=(self.NPARTICLES,self.STABLE_STEPS_LENGTH))
        self.steps_weighted_efficient   = numpy.zeros(shape=(self.NPARTICLES,self.STABLE_STEPS_LENGTH))
        self.steps_datarate_constraint  = numpy.zeros(shape=(self.NPARTICLES,self.STABLE_STEPS_LENGTH))
        self.steps_fairness_constraint  = numpy.zeros(shape=(self.NPARTICLES,self.STABLE_STEPS_LENGTH))

        for antenna in grid.antennas:
            antenna.i                        = numpy.zeros(shape=(self.NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.a                        = numpy.zeros(shape=(self.NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.p                        = numpy.zeros(shape=(self.NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.energy_efficient         = numpy.zeros(shape=(self.NPARTICLES)) 
            antenna.consumition              = numpy.zeros(shape=(self.NPARTICLES)) 
            antenna.datarate                 = numpy.zeros(shape=(self.NPARTICLES))
            antenna.datarate_constraint      = numpy.zeros(shape=(self.NPARTICLES))
            antenna.user_datarate            = numpy.zeros(shape=(self.NPARTICLES,len(antenna.connected_ues)))
            antenna.user_consumption         = numpy.zeros(shape=(self.NPARTICLES,len(antenna.connected_ues)))
            antenna.fairness                 = numpy.zeros(shape=(self.NPARTICLES))
            antenna.meet_users               = numpy.zeros(shape=(self.NPARTICLES))
            antenna.backup_i                 = numpy.zeros(shape=(self.NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_a                 = numpy.zeros(shape=(self.NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_p                 = numpy.zeros(shape=(self.NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_energy_efficient  = numpy.zeros(shape=(self.NPARTICLES)) 
            antenna.backup_consumition       = numpy.zeros(shape=(self.NPARTICLES)) 
            antenna.backup_datarate          = numpy.zeros(shape=(self.NPARTICLES))
            antenna.backup_user_datarate     = numpy.zeros(shape=(self.NPARTICLES,len(antenna.connected_ues)))
            antenna.backup_user_consumption  = numpy.zeros(shape=(self.NPARTICLES,len(antenna.connected_ues)))
            antenna.backup_fairness          = numpy.zeros(shape=(self.NPARTICLES))
            antenna.backup_meet_users        = numpy.zeros(shape=(self.NPARTICLES))
            antenna.history_i                = numpy.zeros(shape=(self.HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_a                = numpy.zeros(shape=(self.HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_p                = numpy.zeros(shape=(self.HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_energy_efficient = numpy.zeros(shape=(self.HISTORY_LENGTH)) 
            antenna.history_consumition      = numpy.zeros(shape=(self.HISTORY_LENGTH)) 
            antenna.history_datarate         = numpy.zeros(shape=(self.HISTORY_LENGTH))
            antenna.history_user_datarate    = numpy.zeros(shape=(self.HISTORY_LENGTH,len(antenna.connected_ues)))
            antenna.history_user_consumption = numpy.zeros(shape=(self.HISTORY_LENGTH,len(antenna.connected_ues)))
            antenna.history_fairness         = numpy.zeros(shape=(self.HISTORY_LENGTH))
            antenna.history_meet_users       = numpy.zeros(shape=(self.HISTORY_LENGTH))
 
        # Loop maximo de itaracoes
        #while stabilized_particles < self.self.NPARTICLES and step < self.MC_STEPS:
        for step in range (0, self.MC_STEPS):
            
            init = time.time()
            gc.collect() #Liberar memoria

            best_weighted_efficient = max(self.steps_weighted_efficient[:,0])
            grid.backup_best_particles(self.steps_weighted_efficient[:,0].copy(), self.HISTORY_LENGTH)
            for p in range(0, self.NPARTICLES):
                print "I:", step, "P:", p
                calc.griddatarate(grid, p)
                calc.gridconsumption(grid, p)
                calc.gridefficiency(grid, p)
                calc.gridfairness(grid, p)
                self.steps_datarate_constraint[p] = util.list_append(self.steps_datarate_constraint[p], calc.datarate_constraint(grid, p))
                self.steps_fairness_constraint[p] = util.list_append(self.steps_fairness_constraint[p], calc.fairness_constraint(grid, p))
                self.steps_energy_efficient[p]    = util.list_append(self.steps_energy_efficient[p], grid.energy_efficient[p])
                self.steps_weighted_efficient[p]  = util.list_append(self.steps_weighted_efficient[p], calc.weighted_efficient(L_BETA, grid.energy_efficient[p], L_LAMBDA, self.steps_datarate_constraint[p,0], L_UPSILON, self.steps_fairness_constraint[p,0]))

                #print  self.steps_datarate_constraint[p,0], self.steps_fairness_constraint[p,0], self.steps_energy_efficient[p,0], self.steps_weighted_efficient[p,0]

                first_in = True
                for stepezinho in range(0, self.STEPS_PER_PARTICLE):#*len(grid.antennas)
                    ant = self.rand_antenna(p, grid)
                    antenna = grid.antennas[ant]

                    while len(antenna.connected_ues) == 0:
                        ant = self.rand_antenna(p, grid)
                        antenna = grid.antennas[ant]
                    
                    antenna.backup_state(p)
                    #print "Antenna", ant
                    ue = self.rand_user(p, antenna)
                    user = antenna.connected_ues[ue]
                    rb = self.rand_rb(p, antenna, ue, grid)
                    antenna.backup_state(p)

                    #print "Antenna,ue,rb: ", antenna._id, user._id, rb
                    current_ue = numpy.argmax(antenna.a[p,:,rb])
                    rest = antenna.rest_power(p)
                    if antenna.a[p][ue][rb] == 0 and antenna.a[p, current_ue, rb] == 0 and rest != None and math.isnan(rest) == False and numpy.sum(antenna.a[p]) < threeGPP.TOTAL_RBS:
                        antenna.i[p][ue][rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                        antenna.p[p][ue][rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p][ue][rb], util.noise(), threeGPP.TARGET_SINR, p)
                        if math.isnan(antenna.p[p][ue][rb]):
                            antenna.i[p][ue][rb] = None
                            antenna.p[p][ue][rb] = None
                        else:    
                            antenna.a[p][ue][rb] = 1
                            #print "Alocando"
                    else:
                        #print "Desalocando"
                        antenna.a[p][current_ue][rb] = 0
                        antenna.p[p][current_ue][rb] = None
                        antenna.i[p][current_ue][rb] = None

                    calc.griddatarate(grid, p)
                    calc.gridconsumption(grid, p)
                    calc.gridefficiency(grid, p)
                    calc.gridfairness(grid, p)
                    current_datarate_constraint = calc.datarate_constraint(grid, p)
                    current_fairness_constraint = calc.fairness_constraint(grid, p)
                    current_weighted_efficient = calc.weighted_efficient(L_BETA, grid.energy_efficient[p], L_LAMBDA, current_datarate_constraint, L_UPSILON, current_fairness_constraint)
                    prob = self.acceptance_probability(p, grid.energy_efficient[p], self.steps_energy_efficient[p,0], current_datarate_constraint, self.steps_datarate_constraint[p,0], current_fairness_constraint, self.steps_fairness_constraint[p,0])
                    rand = random.uniform(0.000, 1.000)
                    #print rand, prob
                    if rand <= prob:
                        prob = 0 #Nao tem o porque, apenas para o if comilar
                        #print "Aceitou!!!"
                        #grid e suas avaliacaes ja estao prontas
                    else:
                        #print "Nao aceitou..."
                        for antenna_aux in grid.antennas:
                            antenna_aux.restore_state(p)
                        calc.griddatarate(grid, p)
                        calc.gridconsumption(grid, p)
                        calc.gridefficiency(grid, p)
                        calc.gridfairness(grid, p)


                    self.steps_datarate_constraint[p] = util.list_append(self.steps_datarate_constraint[p], current_datarate_constraint)
                    self.steps_fairness_constraint[p] = util.list_append(self.steps_fairness_constraint[p], current_fairness_constraint)
                    self.steps_energy_efficient[p]  = util.list_append(self.steps_energy_efficient[p], grid.energy_efficient[p])
                    self.steps_weighted_efficient[p]  = util.list_append(self.steps_weighted_efficient[p], current_weighted_efficient)
                    if self.steps_weighted_efficient[p,0] > best_weighted_efficient:
                        best_weighted_efficient = self.steps_weighted_efficient[p,0]
                        grid.backup_best_particles(self.steps_weighted_efficient[:,0].copy(), self.HISTORY_LENGTH)

                    if stepezinho % self.STABLE_STEPS_LENGTH == 0:
                        self.raises_temperature(p)

                    #print "System wiegted EE", self.steps_weighted_efficient[p, 0]
                    #util.wait()
                grid.restore_best_particles(self.steps_weighted_efficient[:,0].copy(), self.HISTORY_LENGTH)
            

            best_particle = numpy.argmax(self.steps_weighted_efficient[:,0])
            grid.write_to_resume('Adaptative Monte Carlo', self.REPETICAO, step, init, best_particle)


    def raises_temperature(self, p):          

        mean_particles_ee = numpy.mean(self.steps_energy_efficient[:,0])
        mean_particles_datarate = numpy.mean(self.steps_datarate_constraint[:,0])
        mean_particles_fairness = numpy.mean(1 + self.steps_fairness_constraint[:,0])

        #print "Mean EE", mean_particles_ee
        #print "Mean Data", mean_particles_datarate
        #print "Mean Fair", mean_particles_fairness

        if self.steps_energy_efficient[p,0] <= mean_particles_ee and self.is_stable(self.steps_energy_efficient[p]):
            self.beta_particles[p] = self.beta_particles[p] * 0.5
            #print "relaxa ee"
        elif self.steps_energy_efficient[p,0] < mean_particles_ee and self.is_stable(self.steps_energy_efficient[p]) == False:
            self.beta_particles[p] = self.beta_particles[p] * (L_BETA/2)
            #print "restringe ee"
        elif self.steps_energy_efficient[p,0] >= mean_particles_ee and self.is_stable(self.steps_energy_efficient[p]) == False:
            #print "restringe muito ee"
            self.beta_particles[p] = self.beta_particles[p] * L_BETA

        if self.steps_datarate_constraint[p][0] <= mean_particles_datarate and self.is_stable(self.steps_datarate_constraint[p]):
            self.lambda_particles[p] = self.lambda_particles[p] * 0.5
            #print "relaxa data"
        elif self.steps_datarate_constraint[p][0] < mean_particles_datarate and self.is_stable(self.steps_datarate_constraint[p]) == False:
            self.lambda_particles[p] = self.lambda_particles[p] * (L_LAMBDA/2)
            #print "restringe data"
        elif self.steps_datarate_constraint[p][0] >= mean_particles_datarate and self.is_stable(self.steps_datarate_constraint[p]) == False:
            #print "restringe muito data"
            self.lambda_particles[p] = self.lambda_particles[p] * L_LAMBDA

        if self.steps_fairness_constraint[p][0] <= mean_particles_fairness and self.is_stable(self.steps_fairness_constraint[p]):
            self.upsilon_particles[p] = self.upsilon_particles[p] * 0.5
            #print "relaxa fair"
        elif self.steps_fairness_constraint[p][0] < mean_particles_fairness and self.is_stable(self.steps_fairness_constraint[p]) == False:
            self.upsilon_particles[p] = self.upsilon_particles[p] * (L_UPSILON/2)
            #print "restringe fair"
        elif self.steps_fairness_constraint[p][0] >= mean_particles_fairness and self.is_stable(self.steps_fairness_constraint[p]) == False:
            #print "restringe muito fair"
            self.upsilon_particles[p] = self.upsilon_particles[p] * L_UPSILON


    def acceptance_probability(self, particle, new_ee, old_ee, new_datarate, old_datarate, new_fairness, old_fairness):
        prob1 = 1
        prob2 = 1
        prob3 = 1
        if new_ee > old_ee:
            prob1 = 1
            #print "EE 1"
        else:
            #prob1 = 0.6
            delta_ee = new_ee-old_ee
            #print "Delta ee", delta_ee
            #print self.beta_particles[particle]
            prob1 = math.exp(self.beta_particles[particle]*delta_ee)

        if new_datarate > old_datarate or new_datarate == 0:
            prob2 = 1
            #print "Data 1"
        else:
            #prob2 = 0.3
            #print new_datarate-old_datarate
            delta_datarate = new_datarate-old_datarate
            #print "Delta d", delta_datarate
            #print self.lambda_particles[particle]
            prob2 = math.exp((self.lambda_particles[particle])*delta_datarate)

        if new_fairness > old_fairness:
            #print "Fairness 1"
            prob3 = 1
        else:
            #prob3 = 0.6
            delta_fairness = new_fairness-old_fairness
            #print "Delta f", delta_fairness
            #print self.upsilon_particles[particle]
            prob3 = math.exp((self.upsilon_particles[particle])*delta_fairness)


        #print "Probabilidades", prob1, prob2, prob3
        prob = prob1 * prob2 * prob3
        #print "Prob", prob
        return prob

    def rand_antenna(self, particle, grid):
        ant = random.randint(0, len(grid.antennas)-1)
        return ant

    #TODO: Dar probabilidade para desalocar rbs de usuarios que ja tem sua demanda atendica
    def rand_user(self, particle, antenna):
        ue = random.randint(0, len(antenna.connected_ues)-1)
        return ue

    #TODO: Dar maior probabilidade para desalocar rb com pior eficiencia
    def rand_rb(self, particle, antenna, ue, grid):
        rb = random.randint(0, threeGPP.TOTAL_RBS-1)
        return rb

############################################
####          end-refactor   
############################################
