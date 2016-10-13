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

NPARTICLES   = 100
STABLE_STEPS_LENGTH = 5
HISTORY_LENGTH = 2
#RESETRATE    = 0.01
L_BETA       = 1  #EE
L_LAMBDA     = 20 #DATARATE
L_UPSILON    = 1  #FAIRNESS
TX_FLUTUATION = 0.001

class NewMc(object): 
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
        for step in range (0, self.MC_STEPS):
            print "REP: ", self.REPETICAO, " I:", step
            init = time.time()
            gc.collect() #Liberar memoria
            if(step == 0):
                # Loop sobre as particulas
                for p in range(0, NPARTICLES):
                    for stepezinho in range(0, threeGPP.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para preencher A
                        ant = self.rand_antenna(p, grid)
                        antenna = grid.antennas[ant]
                        if len(antenna.connected_ues) > 0:
                            ue = self.rand_user(p, antenna)
                            rb = self.rand_rb(p, antenna, ue, grid)
                            mue = numpy.argmax(antenna.a[p, :, rb])
                            if(antenna.a[p, mue, rb] == 0 and ue >= 0):
                                antenna.i[p][ue][rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                                antenna.p[p][ue][rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p][ue][rb])
                                antenna.a[p][ue][rb] = 1
                                calc.datarate(antenna, p)



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
                    for stepezinho in range(0, threeGPP.TOTAL_RBS*len(grid.antennas)):
                        ant = self.rand_antenna(p, grid)
                        antenna = grid.antennas[ant]
                        while len(antenna.connected_ues) == 0:
                            ant = self.rand_antenna(p, grid)
                            antenna = grid.antennas[ant]
                        
                        antenna.backup_state(p)
                        
                        ue = self.rand_user(p, antenna)
                        rb = self.rand_rb(p, antenna, ue, grid)
                        mue = numpy.argmax(antenna.a[p, :, rb])
                        if(antenna.a[p, mue, rb] > 0):
                            antenna.i[p][mue][rb] = 0
                            antenna.p[p][mue][rb] = 0
                            antenna.a[p][mue][rb] = 0

                        if ue >= 0: # Se usuario nao for zero
                            antenna.i[p][ue][rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                            antenna.p[p][ue][rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p][ue][rb])
                            antenna.a[p][ue][rb] = 1
                        
                        calc.datarate(antenna, p)

                        for antenna_aux in grid.antennas:
                            if len(antenna_aux.connected_ues) > 0:
                                if antenna_aux._id != antenna._id:
                                    antenna_aux.backup_state(p)
                                current_ue = numpy.argmax(antenna_aux.a[p,:,rb])
                                if antenna_aux.a[p, current_ue, rb] > 0:
                                    antenna_aux.i[p, current_ue, rb] = calc.power_interference(current_ue, rb, antenna_aux, grid, p) #dBm
                                    antenna_aux.p[p, current_ue, rb] = calc.transmission_power(antenna_aux, antenna_aux.connected_ues[current_ue], antenna_aux.i[p,current_ue,rb])


                        calc.griddatarate(grid, p)
                        calc.gridconsumption(grid, p)
                        calc.gridefficiency(grid, p)
                        calc.gridfairness(grid, p)
                        current_datarate_constraint = calc.datarate_constraint(grid, p)
                        current_fairness_constraint = calc.fairness_constraint(grid, p)
                        current_weighted_efficient = calc.weighted_efficient(L_BETA, grid.energy_efficient[p], L_LAMBDA, current_datarate_constraint, L_UPSILON, current_fairness_constraint)

                        prob = self.acceptance_probability(p, grid.energy_efficient[p], self.steps_energy_efficient[p,0], current_datarate_constraint, self.steps_datarate_constraint[p,0], current_fairness_constraint, self.steps_fairness_constraint[p,0])
                        rand = random.uniform(0.0, 1.0)
                        if rand <= prob:
                            if(first_in):
                                self.steps_datarate_constraint[p] = util.list_append(self.steps_datarate_constraint[p], current_datarate_constraint)
                                self.steps_fairness_constraint[p] = util.list_append(self.steps_fairness_constraint[p], current_fairness_constraint)
                                self.steps_energy_efficient[p]  = util.list_append(self.steps_energy_efficient[p], grid.energy_efficient[p])
                                self.steps_weighted_efficient[p]  = util.list_append(self.steps_weighted_efficient[p], current_weighted_efficient)
                                first_in = False
                            else:
                                self.steps_datarate_constraint[p,0] = current_datarate_constraint
                                self.steps_fairness_constraint[p,0] = current_fairness_constraint
                                self.steps_energy_efficient[p,0]    = grid.energy_efficient[p]
                                self.steps_weighted_efficient[p,0]  = current_weighted_efficient
                        else:
                            for antenna_aux in grid.antennas:
                                antenna_aux.restore_state(p)

                grid.restore_best_particles(self.steps_weighted_efficient[:,0].copy(), HISTORY_LENGTH)
                self.raises_temperature()

            best_particle = numpy.argmax(self.steps_weighted_efficient[:,0])
            grid.write_to_resume('Adaptative Monte Carlo', self.REPETICAO, step, init, best_particle)


    def raises_temperature(self):          

        mean_particles_ee = numpy.mean(self.steps_energy_efficient[:,0])
        mean_particles_datarate = numpy.mean(self.steps_datarate_constraint[:,0])
        mean_particles_fairness = numpy.mean(self.steps_fairness_constraint[:,0])

        for p in range(0, NPARTICLES):

            particle_std_datarate = numpy.std(self.steps_datarate_constraint[p,:])
            particle_std_fairness = numpy.std(self.steps_fairness_constraint[p,:])
            particle_std_ee       = numpy.std(self.steps_energy_efficient[p,:])

            #print particle_std_ee, self.steps_energy_efficient[p,0]

            if self.steps_energy_efficient[p,0] < mean_particles_ee and (particle_std_ee/self.steps_energy_efficient[p,0]) < TX_FLUTUATION:
                self.beta_particles[p] = self.beta_particles[p] * 0.5
            elif self.steps_energy_efficient[p,0] < mean_particles_ee and (particle_std_ee/self.steps_energy_efficient[p,0]) > TX_FLUTUATION:
                self.beta_particles[p] = self.beta_particles[p] * 1.5
            elif self.steps_energy_efficient[p,0] > mean_particles_ee and (particle_std_ee/self.steps_energy_efficient[p,0]) > TX_FLUTUATION:
                self.beta_particles[p] = self.beta_particles[p] * 2

            if self.steps_datarate_constraint[p][0] < mean_particles_datarate and (particle_std_datarate/self.steps_datarate_constraint[p, 0]) < TX_FLUTUATION:
                self.lambda_particles[p] = self.lambda_particles[p] * 0.9
            elif self.steps_datarate_constraint[p][0] < mean_particles_datarate and (particle_std_datarate/self.steps_datarate_constraint[p, 0]) > TX_FLUTUATION:
                self.lambda_particles[p] = self.lambda_particles[p] * 10
            elif self.steps_datarate_constraint[p][0] > mean_particles_datarate and (particle_std_datarate/self.steps_datarate_constraint[p, 0]) > TX_FLUTUATION:
                self.lambda_particles[p] = self.lambda_particles[p] * 20

            if self.steps_fairness_constraint[p][0] < mean_particles_fairness and (particle_std_fairness/self.steps_fairness_constraint[p, 0]) < TX_FLUTUATION:
                self.upsilon_particles[p] = self.upsilon_particles[p] * 0.5
            elif self.steps_fairness_constraint[p][0] < mean_particles_fairness and (particle_std_fairness/self.steps_fairness_constraint[p, 0]) > TX_FLUTUATION:
                self.upsilon_particles[p] = self.upsilon_particles[p] * 1.5
            elif self.steps_fairness_constraint[p][0] > mean_particles_fairness and (particle_std_fairness/self.steps_fairness_constraint[p, 0]) > TX_FLUTUATION:
                self.upsilon_particles[p] = self.upsilon_particles[p] * 2


    def acceptance_probability(self, particle, new_ee, old_ee, new_datarate, old_datarate, new_fairness, old_fairness):
        prob1 = 1
        prob2 = 1
        prob3 = 1
        if new_ee >= old_ee:
            prob1 = 1
        else:
            delta_ee = new_ee-old_ee
            prob1 = math.exp(self.beta_particles[particle]*delta_ee)

        if new_datarate >= old_datarate:
            prob2 = 1
        else:
            delta_datarate = new_datarate-old_datarate
            prob2 = math.exp((self.lambda_particles[particle])*delta_datarate)

        if new_fairness >= old_fairness:
            prob3 = 1
        else:
            delta_fairness = new_fairness-old_fairness
            prob3 = math.exp((self.upsilon_particles[particle])*delta_fairness)

        prob = prob1 * prob2 * prob3
        return prob

    def rand_antenna(self, particle, grid):
        roulette = numpy.zeros(shape=(len(grid.antennas))) 
        accumulated = 0
        probMinimum = 1
        for ant in range(0, len(grid.antennas)):
            antenna = grid.antennas[ant]    
            if abs(antenna.datarate_constraint[particle]) > probMinimum:
                accumulated = accumulated + abs(antenna.datarate_constraint[particle])
            else:
                accumulated = accumulated + probMinimum
            roulette[ant] = accumulated   

        playmove = random.randint(0, int(accumulated))

        for ant in range(0, len(grid.antennas)):

            if playmove < roulette[ant]:
                return ant

        return ant

    def rand_user(self, particle, antenna):
        max_user_datarate = numpy.max(antenna.user_datarate[particle,:])
        roulette = numpy.zeros(shape=(len(antenna.connected_ues))) 
        accumulated = 0
        probMinimum = 1
        for ue in range(0, len(antenna.connected_ues)):
            #TODO: pensar em uma forma quando a demanda for dinamica 
            dif = max_user_datarate - antenna.user_datarate[particle, ue]
            if dif > probMinimum:
                accumulated = accumulated + dif
            else:
                accumulated = accumulated + probMinimum
            roulette[ue] = accumulated

        playmove = random.randint(0, int(accumulated))
        for ue in range(0, len(antenna.connected_ues)):
           if playmove < roulette[ue]:
                return ue

        return ue

    def rand_rb(self, particle, antenna, ue, grid):
        roulette = numpy.zeros(shape=(threeGPP.TOTAL_RBS)) 
        accumulated = 0
        probMinimum = 1
        for rb in range(0, threeGPP.TOTAL_RBS-1):
            i = calc.power_interference(ue, rb, antenna, grid, particle)
            power = calc.transmission_power(antenna, antenna.connected_ues[ue], i)
            data = (util.shannon(threeGPP.B0, util.sinr(power, i, util.noise())))
            #print "power", power
            prob = (data/1048576)/util.dBm_to_watts(power)
            #print prob
            if prob > probMinimum:
                accumulated = accumulated + prob
            else:
                accumulated = accumulated + probMinimum
            roulette[rb] = accumulated

        playmove = random.randint(0, int(accumulated))
        for rb in range(0, threeGPP.TOTAL_RBS-1):
           if playmove < roulette[rb]:
                return rb

        return rb

############################################
####          end-refactor   
############################################