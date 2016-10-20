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

#TODO:
#Desalocar quando Objetivo estabilizado - OK
#100 stepzinhos estaveis - OK
#Atualizar numero de particulas antes de rodar - OK
# Verificar random mc (crrgir as mesmas coisas e verificar se nao esta sorteandocoisas invalidas e possibilitar a desalocacao tambem)
# Atualizar valores do link pelo peng

NPARTICLES   = 10
STABLE_STEPS_LENGTH = 10
HISTORY_LENGTH = 2
#RESETRATE    = 0.01
L_BETA       = 2  #EE
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
            antenna.user_consumption         = numpy.zeros(shape=(NPARTICLES,len(antenna.connected_ues)))
            antenna.fairness                 = numpy.zeros(shape=(NPARTICLES))
            antenna.meet_users               = numpy.zeros(shape=(NPARTICLES))
            antenna.backup_i                 = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_a                 = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_p                 = numpy.zeros(shape=(NPARTICLES, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.backup_energy_efficient  = numpy.zeros(shape=(NPARTICLES)) 
            antenna.backup_consumition       = numpy.zeros(shape=(NPARTICLES)) 
            antenna.backup_datarate          = numpy.zeros(shape=(NPARTICLES))
            antenna.backup_user_datarate     = numpy.zeros(shape=(NPARTICLES,len(antenna.connected_ues)))
            antenna.backup_user_consumption  = numpy.zeros(shape=(NPARTICLES,len(antenna.connected_ues)))
            antenna.backup_fairness          = numpy.zeros(shape=(NPARTICLES))
            antenna.backup_meet_users        = numpy.zeros(shape=(NPARTICLES))
            antenna.history_i                = numpy.zeros(shape=(HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_a                = numpy.zeros(shape=(HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_p                = numpy.zeros(shape=(HISTORY_LENGTH, len(antenna.connected_ues), threeGPP.TOTAL_RBS))
            antenna.history_energy_efficient = numpy.zeros(shape=(HISTORY_LENGTH)) 
            antenna.history_consumition      = numpy.zeros(shape=(HISTORY_LENGTH)) 
            antenna.history_datarate         = numpy.zeros(shape=(HISTORY_LENGTH))
            antenna.history_user_datarate    = numpy.zeros(shape=(HISTORY_LENGTH,len(antenna.connected_ues)))
            antenna.history_user_consumption = numpy.zeros(shape=(HISTORY_LENGTH,len(antenna.connected_ues)))
            antenna.history_fairness         = numpy.zeros(shape=(HISTORY_LENGTH))
            antenna.history_meet_users       = numpy.zeros(shape=(HISTORY_LENGTH))
 
        # Loop maximo de itaracoes
        #while stabilized_particles < self.NPARTICLES and step < self.MC_STEPS:
        for step in range (0, self.MC_STEPS):
            #print "REP: ", self.REPETICAO, " I:", step
            init = time.time()
            gc.collect() #Liberar memoria
            #if(step == -1):
                # Loop sobre as particulas
                # for p in range(0, NPARTICLES):
                #     calc.griddatarate(grid, p)
                #     calc.gridconsumption(grid, p)
                #     for stepezinho in range(0, threeGPP.TOTAL_RBS*len(grid.antennas)):# Loop de K * M para preencher A
                #         ant = self.rand_antenna(p, grid)
                #         #print "Antenna", ant
                #         antenna = grid.antennas[ant]
                #         if len(antenna.connected_ues) > 0:
                #             #print "Tem user"
                #             rest = antenna.rest_power(p)
                #             print "antenna", ant 
                #             if rest!= None and math.isnan(rest) == False:
                #                 #print "Tem energia"
                #                 ue = self.rand_user(p, antenna)
                #                 print "User", ue
                #                 rb = self.rand_rb(p, antenna, ue, grid)
                #                 print "RB", rb
                #                 mue = numpy.argmax(antenna.a[p, :, rb])
                #                 print "MUE", antenna.a[p, mue, rb]
                #                 if(antenna.a[p, mue, rb] == 0 and ue >= 0):
                #                     #print "Nao alocado ainda"
                #                     antenna.i[p][ue][rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                #                     antenna.p[p][ue][rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p][ue][rb], util.noise(), threeGPP.TARGET_SINR, p)
                #                     if math.isnan(antenna.p[p][ue][rb]):
                #                         #print "Nan"
                #                         antenna.i[p][ue][rb] = None
                #                         antenna.p[p][ue][rb] = None
                #                     else:   
                #                         #print "RB Alocado" 
                #                         antenna.a[p][ue][rb] = 1
                #                         calc.datarate(antenna, grid,p)
                #                         calc.consumption(antenna, p)



                # calc.griddatarate(grid, p)
                # calc.gridconsumption(grid, p)
                # calc.gridefficiency(grid, p)
                # calc.gridfairness(grid, p)
                # self.steps_datarate_constraint[p] = util.list_append(self.steps_datarate_constraint[p], calc.datarate_constraint(grid, p))
                # self.steps_fairness_constraint[p] = util.list_append(self.steps_fairness_constraint[p], calc.fairness_constraint(grid, p))
                # self.steps_energy_efficient[p]    = util.list_append(self.steps_energy_efficient[p], grid.energy_efficient[p])
                # self.steps_weighted_efficient[p]  = util.list_append(self.steps_weighted_efficient[p], calc.weighted_efficient(L_BETA, grid.energy_efficient[p], L_LAMBDA, self.steps_datarate_constraint[p,0], L_UPSILON, self.steps_fairness_constraint[p,0]))

            #else:
            best_weighted_efficient = max(self.steps_weighted_efficient[:,0])
            grid.backup_best_particles(self.steps_weighted_efficient[:,0].copy(), HISTORY_LENGTH)
            for p in range(0, NPARTICLES):
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
                for stepezinho in range(0, threeGPP.TOTAL_RBS*len(grid.antennas)):#*len(grid.antennas)
                    #print "Stepezinho", stepezinho
                    grid_ue = self.rand_ue_ant(p, grid)
                    user = grid._user[grid_ue]
                    antenna = user._connected_antenna
                    ue = 0
                    for ue in range(0, len(antenna.connected_ues)):
                        if antenna.connected_ues[ue]._id == user._id:
                            break
                    #print "Antenna UE", ue
                    antenna.backup_state(p)
                    
                    rb = self.rand_rb(p, ue, antenna, grid)
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
                        grid.backup_best_particles(self.steps_weighted_efficient[:,0].copy(), HISTORY_LENGTH)

                    if stepezinho % STABLE_STEPS_LENGTH == 0:
                        self.raises_temperature(p)

                    #print "System wiegted EE", self.steps_weighted_efficient[p, 0]
                    #util.wait()
                grid.restore_best_particles(self.steps_weighted_efficient[:,0].copy(), HISTORY_LENGTH)
            

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



    def rand_ue_ant(self, particle, grid):
        #print "Rand UE ANT"
        roulette = numpy.zeros(shape=(len(grid._user))) 
        user_weighted_ee = numpy.zeros(shape=(len(grid._user)))
        mean_datarate = grid.datarate[particle]/len(grid._user)
        for grid_ue in range(0, len(grid._user)):
            user = grid._user[grid_ue]
            antenna = user._connected_antenna
            rest_power = antenna.rest_power(particle) 
            ue = 0
            for ue in range(0, len(antenna.connected_ues)):
                if antenna.connected_ues[ue]._id == user._id:
                    break
            datarate_constraint = 0
            if user._type == User.HIGH_RATE_USER:
                datarate_constraint = antenna.user_datarate[particle, ue] - threeGPP.NR
            else:
                datarate_constraint = antenna.user_datarate[particle, ue] - threeGPP.NER
            if datarate_constraint >= 0:
                datarate_constraint = 0

            if rest_power == None or math.isnan(rest_power) or rest_power < 1:
                user_ee = (antenna.user_datarate[particle, ue]*2000/1048576)/(util.mw_to_watts(antenna.user_consumption[particle, ue]))
            else:
                user_ee = (antenna.user_datarate[particle, ue]*2000/1048576)/(util.mw_to_watts(antenna.user_consumption[particle, ue])) * rest_power
            if math.isnan(user_ee):
                user_ee = 0
            #print user_ee, antenna.user_datarate[particle, ue], mean_datarate
            fairness_constraint = (-1)*abs(antenna.user_datarate[particle, ue]-mean_datarate)


            #print fairness_constraint
            #print calc.weighted_efficient(L_BETA, user_ee, L_LAMBDA, datarate_constraint, L_UPSILON, fairness_constraint)

            #user_weighted_ee[grid_ue] = calc.weighted_efficient(L_BETA, user_ee, L_LAMBDA, datarate_constraint, L_UPSILON, fairness_constraint)
            user_weighted_ee[grid_ue] = calc.weighted_efficient(self.beta_particles[particle], user_ee, self.lambda_particles[particle], datarate_constraint, self.upsilon_particles[particle], fairness_constraint)
            
            #print "Grid UE", grid_ue, user_weighted_ee[grid_ue]


        accumulated = 0
        max_user_weighted_ee = numpy.min(user_weighted_ee)
        for ue in range(0, len(grid._user)):
            accumulated += abs(user_weighted_ee[ue]/max_user_weighted_ee)
            roulette[ue] = accumulated   

        #print "Users EE", user_weighted_ee
        #print "Ranto to", roulette 
        playmove = random.uniform(0.00, accumulated)
        #print "Movimento", playmove
        for ue in range(0, len(grid._user)):
            if playmove < roulette[ue]:
                #print "UE Grid", ue
                return ue
        #print "UE Grid2", ue
        return ue


    def rand_rb(self, p, ue, antenna, grid):
        #print "Rand RB"
        roulette = numpy.zeros(shape=(threeGPP.TOTAL_RBS)) 
        rb_weighted_ee = numpy.zeros(shape=(threeGPP.TOTAL_RBS))
        for antenna_aux in grid.antennas:
            if len(antenna_aux.connected_ues) > 0:
                antenna_aux.backup_state(p)

        for rb in range(0, threeGPP.TOTAL_RBS):
            prob = 0
            current_ue = numpy.argmax(antenna.a[p,:,rb])
            rest = antenna.rest_power(p)
            if antenna.a[p, current_ue, rb] != 0 or rest == None or math.isnan(rest) or numpy.sum(antenna.a[p]) == threeGPP.TOTAL_RBS:
                antenna.a[p][current_ue][rb] = 0
                antenna.p[p][current_ue][rb] = None
                antenna.i[p][current_ue][rb] = None
                #print "RB", rb, "ja alocado ou antena sem energia"
            else:
                antenna.i[p, ue, rb] = calc.power_interference(ue, rb, antenna, grid, p) #dBm
                antenna.p[p, ue, rb] = calc.transmission_power(antenna, antenna.connected_ues[ue], antenna.i[p,ue,rb], util.noise(), threeGPP.TARGET_SINR, p)
                if math.isnan(antenna.p[p][ue][rb]):
                    antenna.i[p][ue][rb] = None
                    antenna.p[p][ue][rb] = None
                    prob = -1
                else:    
                    antenna.a[p][ue][rb] = 1

            for antenna_aux in grid.antennas:
                if len(antenna_aux.connected_ues) > 0:
                    current_ue = numpy.argmax(antenna_aux.a[p,:,rb])
                    if antenna_aux.a[p, current_ue, rb] > 0:
                        antenna_aux.i[p, current_ue, rb] = calc.power_interference(current_ue, rb, antenna_aux, grid, p) #dBm
                        antenna_aux.p[p, current_ue, rb] = calc.transmission_power(antenna_aux, antenna_aux.connected_ues[current_ue], antenna_aux.i[p,current_ue,rb], util.noise(), threeGPP.TARGET_SINR, p)

            
            calc.griddatarate(grid, p)
            calc.gridconsumption(grid, p)
            calc.gridefficiency(grid, p)
            calc.gridfairness(grid, p)
            datarate_constraint = calc.datarate_constraint(grid, p)
            fairness_constraint = calc.fairness_constraint(grid, p)
            rb_weighted_ee[rb] = calc.weighted_efficient(L_BETA, grid.energy_efficient[p], L_LAMBDA, datarate_constraint, L_UPSILON, fairness_constraint)


            for antenna_aux in grid.antennas:
                if len(antenna_aux.connected_ues) > 0:
                    antenna_aux.restore_state(p)

        accumulated = 0
        max_rb_weighted_ee = max(rb_weighted_ee)
        for rb in range(0, threeGPP.TOTAL_RBS):
            accumulated += (max_rb_weighted_ee/rb_weighted_ee[rb])
            roulette[rb] = accumulated   

        #print "RB EE", rb_weighted_ee 
        #print "Ranto to", roulette 
        playmove = random.uniform(0.00, accumulated)
        #print "Movimento", playmove
        for rb in range(0, threeGPP.TOTAL_RBS):
            if playmove < roulette[rb]:
                return rb

        return rb



    # def rand_antenna(self, particle, grid):
    #     roulette = numpy.zeros(shape=(len(grid.antennas))) 
    #     accumulated = 0
    #     probMinimum = 1
    #     for ant in range(0, len(grid.antennas)):
    #         antenna = grid.antennas[ant]
    #         if len(antenna.connected_ues) > 0:  
    #             if (self.is_stable(self.steps_weighted_efficient[particle]) == False):
    #                 rest = antenna.rest_power(particle)
    #                 if rest != None and math.isnan(rest) == False:
    #                     if (abs(antenna.datarate_constraint[particle]) > 0):
    #                         accumulated = accumulated + abs(antenna.datarate_constraint[particle])
    #                     else:
    #                         #TODO: Selecionar antenna de pior EE
    #                         accumulated = accumulated + probMinimum
    #                 else:
    #                     accumulated = accumulated + 0 #antenas sem energia nao participam do sorteio
    #             else:
    #                 if (antenna.type == antenna.BS_ID):
    #                     accumulated = accumulated + threeGPP.POWER_BS * antenna.consumition[particle]
    #                 else:
    #                     accumulated = accumulated + threeGPP.POWER_RRH * antenna.consumition[particle]
    #         else:
    #              accumulated = accumulated + 0 #antenas sem usuarios nao participam do sorteio

    #         roulette[ant] = accumulated   

    #     print "Ranto to", roulette 
    #     playmove = random.randint(0, int(accumulated))
    #     print "Movimento", playmove
    #     for ant in range(0, len(grid.antennas)):

    #         if playmove < roulette[ant]:
    #             #print "Selecionada", ant
    #             return ant

    #     #print "Selecionada", ant

    #     return ant

    # #TODO: Dar probabilidade para desalocar rbs de usuarios que ja tem sua demanda atendica
    # def rand_user(self, particle, antenna):
    #     roulette = numpy.zeros(shape=(len(antenna.connected_ues))) 
    #     accumulated = 0
    #     probMinimum = 1
    #     rest = antenna.rest_power(particle)
    #     if rest != None and math.isnan(rest) == False and self.is_stable(self.steps_weighted_efficient[particle]) == False:
    #         max_user_datarate = numpy.max(antenna.user_datarate[particle,:])
    #         for ue in range(0, len(antenna.connected_ues)):
    #             #TODO: pensar em uma forma quando a demanda for dinamica 
    #             dif = max_user_datarate - antenna.user_datarate[particle, ue]
    #             if dif > probMinimum:
    #                 accumulated = accumulated + dif
    #             else:
    #                 accumulated = accumulated + probMinimum
    #             roulette[ue] = accumulated
    #     else:
    #         for ue in range(0, len(antenna.connected_ues)):
    #             user = antenna.connected_ues[ue]
    #             dif = 0
    #             if user._type == User.HIGH_RATE_USER:
    #                 dif = antenna.user_datarate[particle, ue] - threeGPP.NR
    #             else:
    #                 dif = antenna.user_datarate[particle, ue] - threeGPP.NER
    #             if dif > probMinimum:
    #                 accumulated = accumulated + dif
    #             else:
    #                 accumulated = accumulated + probMinimum
    #             roulette[ue] = accumulated

    #     playmove = random.randint(0, int(accumulated))
    #     for ue in range(0, len(antenna.connected_ues)):
    #        if playmove < roulette[ue]:
    #             return ue

    #     return ue

    # #TODO: Dar maior probabilidade para desalocar rb com pior eficiencia
    # def rand_rb(self, particle, antenna, ue, grid):
    #     roulette = numpy.zeros(shape=(threeGPP.TOTAL_RBS)) 
    #     accumulated = 0
    #     probMinimum = 10
    #     rest = antenna.rest_power(particle)
    #     if rest != None and math.isnan(rest) == False and self.is_stable(self.steps_weighted_efficient[particle]) == False:
    #         print "if"
    #         for rb in range(0, threeGPP.TOTAL_RBS):
    #             #print "loop", rb
    #             mue = numpy.argmax(antenna.a[particle, :, rb])
    #             #print "MUE", antenna.a[p, mue, rb]
    #             if(antenna.a[particle, mue, rb] == 0 and antenna.a[particle, ue, rb] == 0):
    #                 i = calc.power_interference(ue, rb, antenna, grid, particle)
    #                 power = calc.transmission_power(antenna, antenna.connected_ues[ue], i, util.noise(), threeGPP.TARGET_SINR, particle)
    #                 #print "Power", power 
    #                 if power != None and math.isnan(power) == False:    
    #                     data = (util.shannon(threeGPP.B0, calc.gaussian_sinr(power, util.path_loss(antenna.connected_ues[ue],antenna), i, util.noise())))
    #                     #print "power", transmission_power                  
    #                     prob = (data/2000)/util.dbm_to_mw(power)
    #                     #print "EE prob", prob
    #                     if prob > probMinimum:
    #                         accumulated = accumulated + prob
    #                     else:
    #                         accumulated = accumulated + probMinimum
    #                 else:
    #                     prob = 0
    #                     accumulated = accumulated + prob
    #             else:
    #                 prob = 0
    #                 accumulated = accumulated + prob
    #             roulette[rb] = accumulated
    #     else:
    #         #print "else"
    #         for rb in range(0, threeGPP.TOTAL_RBS):
    #             mue = numpy.argmax(antenna.a[particle, :, rb])
    #             if(antenna.a[particle, mue, rb] > 0):
    #                 i = calc.power_interference(ue, rb, antenna, grid, particle)
    #                 power = calc.transmission_power(antenna, antenna.connected_ues[ue], i, util.noise(), threeGPP.TARGET_SINR, particle)
    #                 if power != None and math.isnan(power) == False:
    #                     #print "Power prob", power
    #                     if power > probMinimum:
    #                         accumulated = accumulated + power
    #                     else:
    #                         accumulated = accumulated + probMinimum
    #             else:
    #                 prob = 0
    #                 accumulated = accumulated + prob
    #             roulette[rb] = accumulated

    #     #print "Roulette", roulette

    #     playmove = random.randint(0, int(accumulated))
    #     for rb in range(0, threeGPP.TOTAL_RBS):
    #        if playmove < roulette[rb]:
    #             return rb

    #     return rb

############################################
####          end-refactor   
############################################