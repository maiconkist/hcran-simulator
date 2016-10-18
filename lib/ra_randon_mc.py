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
import threeGPP
import Calculations as calc

NPARTICLES   = 20
STABLE_STEPS_LENGTH = 10
HISTORY_LENGTH = 10
#RESETRATE    = 0.01
L_BETA       = 1  #EE
L_LAMBDA     = 20 #DATARATE
L_UPSILON    = 2  #FAIRNESS
TX_FLUTUATION = 0.001

class RandonMc(object): 
    def __init__(self, r, imax):
        self.REPETICAO = r
        self.MC_STEPS = imax
    
        self.lambda_particles = None
        self.beta_particles = None 
        self.upsilon_particles = None
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
        if math.isnan(dif) == False and abs(dif) > TX_FLUTUATION:
            #print "Not Stable"
            return False
        #print "Stable"    
        return True

    def run(self, grid):
        grid.energy_efficient           = numpy.zeros(shape=(NPARTICLES)) 
        grid.consumition                = numpy.zeros(shape=(NPARTICLES))
        grid.datarate                   = numpy.zeros(shape=(NPARTICLES))
        grid.fairness                   = numpy.zeros(shape=(NPARTICLES))
        grid.meet_users                 = numpy.zeros(shape=(NPARTICLES))
        grid.history_weighted_efficient = numpy.zeros(shape=(HISTORY_LENGTH))

        self.lambda_particles           = numpy.ones(shape=(NPARTICLES))
        self.upsilon_particles          = numpy.ones(shape=(NPARTICLES))
        self.beta_particles             = numpy.ones(shape=(NPARTICLES))
        self.steps_energy_efficient     = numpy.zeros(shape=(NPARTICLES,STABLE_STEPS_LENGTH))
        self.steps_weighted_efficient   = numpy.zeros(shape=(NPARTICLES,STABLE_STEPS_LENGTH))
        self.steps_datarate_constraint  = numpy.zeros(shape=(NPARTICLES,STABLE_STEPS_LENGTH))
        self.steps_fairness_constraint  = numpy.zeros(shape=(NPARTICLES,STABLE_STEPS_LENGTH))

        for antenna in grid.antennas:
            antenna.i                        = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.a                        = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.p                        = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.energy_efficient         = numpy.zeros(shape=(NPARTICLES)) 
            antenna.consumition              = numpy.zeros(shape=(NPARTICLES)) 
            antenna.datarate                 = numpy.zeros(shape=(NPARTICLES))
            antenna.datarate_constraint      = numpy.zeros(shape=(NPARTICLES))
            antenna.user_datarate            = numpy.zeros(shape=(NPARTICLES,len(antenna.connected_ues)))
            antenna.fairness                 = numpy.zeros(shape=(NPARTICLES))
            antenna.meet_users               = numpy.zeros(shape=(NPARTICLES))
            antenna.backup_i                 = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_a                 = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_p                 = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_energy_efficient  = numpy.zeros(shape=(NPARTICLES)) 
            antenna.backup_consumition       = numpy.zeros(shape=(NPARTICLES)) 
            antenna.backup_datarate          = numpy.zeros(shape=(NPARTICLES))
            antenna.backup_user_datarate     = numpy.zeros(shape=(NPARTICLES,len(antenna.connected_ues)))
            antenna.backup_fairness          = numpy.zeros(shape=(NPARTICLES))
            antenna.backup_meet_users        = numpy.zeros(shape=(NPARTICLES))
            antenna.history_i                = numpy.zeros(shape=(HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_a                = numpy.zeros(shape=(HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_p                = numpy.zeros(shape=(HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_energy_efficient = numpy.zeros(shape=(HISTORY_LENGTH)) 
            antenna.history_consumition      = numpy.zeros(shape=(HISTORY_LENGTH)) 
            antenna.history_datarate         = numpy.zeros(shape=(HISTORY_LENGTH))
            antenna.history_user_datarate    = numpy.zeros(shape=(HISTORY_LENGTH,len(antenna.connected_ues)))
            antenna.history_fairness         = numpy.zeros(shape=(HISTORY_LENGTH))
            antenna.history_meet_users       = numpy.zeros(shape=(HISTORY_LENGTH))
 
        # Loop maximo de itaracoes
        #while stabilized_particles < self.NPARTICLES and step < self.MC_STEPS:
        for step in range (0, self.MC_STEPS*10 + 1):
            #print "REP: ", self.REPETICAO, " I:", step
            init = time.time()
            gc.collect() #Liberar memoria
            if(step == 0):
                # Loop sobre as particulas
                for p in range(0, NPARTICLES):
                    #calc.griddatarate(grid, p)
                    #calc.gridconsumption(grid, p)
                    for stepezinho in range(0, threeGPP.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para preencher A
                        ant = self.rand_antenna(p, grid)
                        #print "Antenna", ant
                        antenna = grid.antennas[ant]
                        if len(antenna.connected_ues) > 0:
                            #print "Tem user"
                            rest = antenna.rest_power(p)
                            if rest!= None and math.isnan(rest) == False:
                                #print "Tem energia"
                                ue = self.rand_user(p, antenna)
                                #print "User", ue
                                rb = self.rand_rb(p, antenna, ue, grid)
                                #print "RB", rb
                                mue = numpy.argmax(antenna.a[p, :, rb])
                                #print "MUE", antenna.a[p, mue, rb]
                                if(antenna.a[p, mue, rb] == 0 and ue >= 0):
                                    #print "Nao alocado ainda"
                                    antenna.i[p][ue][rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                                    antenna.p[p][ue][rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p][ue][rb], util.noise(), threeGPP.TARGET_SINR, p)
                                    if math.isnan(antenna.p[p][ue][rb]):
                                        #print "Nan"
                                        antenna.i[p][ue][rb] = None
                                        antenna.p[p][ue][rb] = None
                                    else:   
                                        #print "RB Alocado" 
                                        antenna.a[p][ue][rb] = 1
       

                calc.griddatarate(grid, p)
                calc.gridconsumption(grid, p)
                calc.gridefficiency(grid, p)
                calc.gridfairness(grid, p)
                self.steps_datarate_constraint[p] = util.list_append(self.steps_datarate_constraint[p], calc.datarate_constraint(grid, p))
                self.steps_fairness_constraint[p] = util.list_append(self.steps_fairness_constraint[p], calc.fairness_constraint(grid, p))
                self.steps_energy_efficient[p]    = util.list_append(self.steps_energy_efficient[p], grid.energy_efficient[p])
                self.steps_weighted_efficient[p]  = util.list_append(self.steps_weighted_efficient[p], calc.weighted_efficient(L_BETA, grid.energy_efficient[p], L_LAMBDA, self.steps_datarate_constraint[p,0], L_UPSILON, self.steps_fairness_constraint[p,0]))

            else:
                grid.backup_best_particles(self.steps_weighted_efficient[:,0].copy(), HISTORY_LENGTH)
                for p in range(0, NPARTICLES):
                    first_in = True
                    for stepezinho in range(0, threeGPP.TOTAL_RBS*len(grid.antennas)):#*len(grid.antennas)
                        ant = self.rand_antenna(p, grid)
                        antenna = grid.antennas[ant]
                        #if len(antenna.connected_ues) == 0 and math.isnan(antenna.rest_power(p)) == False:
                        #    continue
                        while len(antenna.connected_ues) == 0:
                            ant = self.rand_antenna(p, grid)
                            antenna = grid.antennas[ant]
                        
                        antenna.backup_state(p)
                        #print "Antenna", ant
                        ue = self.rand_user(p, antenna)
                        rb = self.rand_rb(p, antenna, ue, grid)
                        rest = antenna.rest_power(p)
                        if rest != None and math.isnan(rest) == False and antenna.a[p][ue][rb] == 0:
                            mue = numpy.argmax(antenna.a[p, :, rb])
                            if(antenna.a[p, mue, rb] > 0):
                                antenna.a[p][mue][rb] = 0
                                antenna.p[p][mue][rb] = None
                                antenna.i[p][mue][rb] = None

                            if ue >= 0: # Se usuario nao for zero
                                antenna.i[p][ue][rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                                antenna.p[p][ue][rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p][ue][rb], util.noise(), threeGPP.TARGET_SINR, p)
                                if math.isnan(antenna.p[p][ue][rb]):
                                    antenna.i[p][ue][rb] = None
                                    antenna.p[p][ue][rb] = None
                                else:    
                                    antenna.a[p][ue][rb] = 1
                        else:
                            #print "Desalocando"
                            antenna.a[p][ue][rb] = 0
                            antenna.p[p][ue][rb] = None
                            antenna.i[p][ue][rb] = None

                        for antenna_aux in grid.antennas:
                            if len(antenna_aux.connected_ues) > 0:
                                if antenna_aux._id != antenna._id:
                                    antenna_aux.backup_state(p)
                                current_ue = numpy.argmax(antenna_aux.a[p,:,rb])
                                if antenna_aux.a[p, current_ue, rb] > 0:
                                    antenna_aux.i[p, current_ue, rb] = calc.power_interference(current_ue, rb, antenna_aux, grid, p) #dBm
                                    antenna_aux.p[p, current_ue, rb] = calc.transmission_power(antenna_aux, antenna_aux.connected_ues[current_ue], antenna_aux.i[p,current_ue,rb], util.noise(), threeGPP.TARGET_SINR, p)


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
                            #print "Aceitou!!!"
                            #if(first_in):
                            self.steps_datarate_constraint[p] = util.list_append(self.steps_datarate_constraint[p], current_datarate_constraint)
                            self.steps_fairness_constraint[p] = util.list_append(self.steps_fairness_constraint[p], current_fairness_constraint)
                            self.steps_energy_efficient[p]  = util.list_append(self.steps_energy_efficient[p], grid.energy_efficient[p])
                            self.steps_weighted_efficient[p]  = util.list_append(self.steps_weighted_efficient[p], current_weighted_efficient)
                            #first_in = False
                            #else:
                            #    self.steps_datarate_constraint[p,0] = current_datarate_constraint
                            #    self.steps_fairness_constraint[p,0] = current_fairness_constraint
                            #    self.steps_energy_efficient[p,0]    = grid.energy_efficient[p]
                            #    self.steps_weighted_efficient[p,0]  = current_weighted_efficient
                        else:
                            #print "Nao aceitou..."
                            for antenna_aux in grid.antennas:
                                antenna_aux.restore_state(p)

                        if stepezinho % self.MC_STEPS == 0:
                            self.raises_temperature(p)

                grid.restore_best_particles(self.steps_weighted_efficient[:,0].copy(), HISTORY_LENGTH)


            if step % self.MC_STEPS == 0:
                best_particle = numpy.argmax(self.steps_weighted_efficient[:,0])
                grid.write_to_resume('Random Monte Carlo', self.REPETICAO, step/10, init, best_particle)


    def raises_temperature(self, p):          

        mean_particles_ee = numpy.mean(self.steps_energy_efficient[:,0])
        mean_particles_datarate = numpy.mean(self.steps_datarate_constraint[:,0])
        mean_particles_fairness = numpy.mean(1 + self.steps_fairness_constraint[:,0])

        #print "Mean EE", mean_particles_ee
        #print "Mean Data", mean_particles_datarate
        #print "Mean Fair", mean_particles_fairness

        #for p in range(0, NPARTICLES):

        if self.steps_energy_efficient[p,0] < mean_particles_ee and self.is_stable(self.steps_energy_efficient[p]):
            self.beta_particles[p] = self.beta_particles[p] * 0.5
            #print "relaxa ee"
        elif self.steps_energy_efficient[p,0] < mean_particles_ee and self.is_stable(self.steps_energy_efficient[p]) == False:
            self.beta_particles[p] = self.beta_particles[p] * 1.5
            #print "restringe ee"
        elif self.steps_energy_efficient[p,0] > mean_particles_ee and self.is_stable(self.steps_energy_efficient[p]) == False:
            #print "restringe muito ee"
            self.beta_particles[p] = self.beta_particles[p] * 2

        if self.steps_datarate_constraint[p][0] < mean_particles_datarate and self.is_stable(self.steps_datarate_constraint[p]):
            self.lambda_particles[p] = self.lambda_particles[p] * 0.9
            #print "relaxa data"
        elif self.steps_datarate_constraint[p][0] < mean_particles_datarate and self.is_stable(self.steps_datarate_constraint[p]) == False:
            self.lambda_particles[p] = self.lambda_particles[p] * 10
            #print "restringe data"
        elif self.steps_datarate_constraint[p][0] > mean_particles_datarate and self.is_stable(self.steps_datarate_constraint[p]) == False:
            #print "restringe muito data"
            self.lambda_particles[p] = self.lambda_particles[p] * 20

        if self.steps_fairness_constraint[p][0] < mean_particles_fairness and self.is_stable(self.steps_fairness_constraint[p]):
            self.upsilon_particles[p] = self.upsilon_particles[p] * 0.5
            #print "relaxa fair"
        elif self.steps_fairness_constraint[p][0] < mean_particles_fairness and self.is_stable(self.steps_fairness_constraint[p]) == False:
            self.upsilon_particles[p] = self.upsilon_particles[p] * 1.5
            #print "restringe fair"
        elif self.steps_fairness_constraint[p][0] > mean_particles_fairness and self.is_stable(self.steps_fairness_constraint[p]) == False:
            #print "restringe muito fair"
            self.upsilon_particles[p] = self.upsilon_particles[p] * 2


    def acceptance_probability(self, particle, new_ee, old_ee, new_datarate, old_datarate, new_fairness, old_fairness):
        prob1 = 1
        prob2 = 1
        prob3 = 1
        if new_ee >= old_ee:
            prob1 = 1
        else:
            #prob1 = 0.6
            delta_ee = new_ee-old_ee
            prob1 = math.exp(self.beta_particles[particle]*delta_ee)

        if new_datarate >= old_datarate or old_datarate == 0:
            prob2 = 1
        else:
            #prob2 = 0.3
            #print new_datarate-old_datarate
            delta_datarate = new_datarate-old_datarate
            prob2 = math.exp((self.lambda_particles[particle])*delta_datarate)

        if new_fairness >= old_fairness:
            prob3 = 1
        else:
            #prob3 = 0.6
            delta_fairness = new_fairness-old_fairness
            prob3 = math.exp((self.upsilon_particles[particle])*delta_fairness)


        #print prob1, prob2, prob3
        prob = prob1 * prob2 * prob3
        return prob
    #TODO: Dar probabilidade para quando esta usando maximo de energia desalocar
    # MAX power da antenna
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