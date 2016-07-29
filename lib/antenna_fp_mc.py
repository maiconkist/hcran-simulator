import math
import numpy
import util
import controller
import random
from antenna import *
from user import *
from util import *

DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)


class AntennaMc(Antenna):

    def __init__(self, id, type, pos, radius, grid, bw = 1.4):
        Antenna.__init__(self, id, type, pos, radius, grid, bw)

    def init_mc(self, antennas, nAntennas):
        if len(self.connected_ues) == 0:
            return
        
        self.HISTORICALRATE = 0.2
        self.RESETRATE    = 0.01
        self.NPARTICLES   = 10
        self.L_BETA       = 0.1
        self.L_LAMBDA     = 0.1
        self.L_UPSILON    = 0.1
        self.E_DEALTA     = 0.2
        self.mc_user_data_rate = np.zeros(shape=(self.NPARTICLES, len(self.connected_ues)))
        self.mc_data_rate = np.zeros(shape=(self.NPARTICLES))
        self.mc_power_consumption = np.zeros(shape=(self.NPARTICLES))
        self.mc_high_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_low_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_interference_reuse_constraint = np.zeros(shape=(self.NPARTICLES, self.TOTAL_RBS))
        self.mc_maximum_transmit_power_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_antenna_energy_efficient = np.zeros(shape=(self.NPARTICLES))
        self.mc_a = numpy.zeros(shape=(self.NPARTICLES,len(self.connected_ues), self.TOTAL_RBS))
        self.mc_roulette = numpy.zeros(shape=(self.NPARTICLES))
        #Re style variables
        self.user_data_rate = numpy.zeros(shape=(len(self.connected_ues)))
        self.i = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))
        self.a = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))
        self.p = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))


    def mc_clean_variables(self):
        self.NPARTICLES = int(self.NPARTICLES * self.RESETRATE)
        #debug_printf(self.NPARTICLES)
        if self.NPARTICLES < 2:
            self.NPARTICLES = 2
        self.mc_user_data_rate = np.zeros(shape=(self.NPARTICLES, len(self.connected_ues)))
        self.mc_data_rate = np.zeros(shape=(self.NPARTICLES))
        self.mc_power_consumption = np.zeros(shape=(self.NPARTICLES))
        self.mc_high_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_low_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_interference_reuse_constraint = np.zeros(shape=(self.NPARTICLES, self.TOTAL_RBS))
        self.mc_maximum_transmit_power_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_antenna_energy_efficient = np.zeros(shape=(self.NPARTICLES))
        self.mc_a = numpy.zeros(shape=(self.NPARTICLES,len(self.connected_ues), self.TOTAL_RBS))
        self.mc_roulette = numpy.zeros(shape=(self.NPARTICLES))


    def mc_ee_partial_calc(self,pt,ue,rb):
        k_data_rate = self.shannon((self.mc_a[pt,ue,rb] * Antenna.B0), self.sinr(self.p[ue][rb], self.i[ue][rb], self.noise()))
        self.mc_data_rate[pt] += k_data_rate
        self.mc_user_data_rate[pt][ue] += k_data_rate
        self.mc_power_consumption[pt] += (self.mc_a[pt,ue,rb] * self.dBm_to_watts(self.p[ue,rb]))
        #self.mc_interference_reuse_constraint[pt, rb] += self.mc_a[pt,ue,rb] * self.p[ue,rb] * Antenna.DR2M * Antenna.PMmax
        self.mc_maximum_transmit_power_constraint[pt] += self.mc_a[pt,ue,rb] * self.p[ue,rb]


    def mc_ee_final_calc(self,pt):
        interference_reuse_constraint = 0
        self.mc_power_consumption[pt] = Antenna.EFF * self.mc_power_consumption[pt] + Antenna.PRC + Antenna.PBH
        for ue in range(0, len(self.connected_ues)):
            if self.connected_ues[ue]._type == User.HIGH_RATE_USER:
                self.mc_high_rate_constraint[pt] += self.L_BETA * self.mc_user_data_rate[pt][ue] - Antenna.NR
            else:
                self.mc_low_rate_constraint[pt] += self.L_BETA *  self.mc_user_data_rate[pt][ue] - Antenna.NER
        #for rb in range(0,self.TOTAL_RBS): #RB
        #    interference_reuse_constraint += self.L_LAMBDA * (self.E_DEALTA - self.mc_interference_reuse_constraint[pt, k])
        #if self.type == self.BS_ID:
        #    self.mc_interference_reuse_constraint[pt] = Antenna.PMmax - self.mc_interference_reuse_constraint[pt]
        #else:        
        #    self.mc_interference_reuse_constraint[pt] = Antenna.PRmax - self.mc_interference_reuse_constraint[pt]


        
        if self.type == self.BS_ID:
            self.mc_maximum_transmit_power_constraint[pt] = self.L_UPSILON * (Antenna.PMmax - self.mc_maximum_transmit_power_constraint[pt])
        else:        
            self.mc_maximum_transmit_power_constraint[pt] = self.L_UPSILON * (Antenna.Pmax - self.mc_maximum_transmit_power_constraint[pt])
        
        #debug_printf('DataRate: ' + str(self.mc_data_rate[pt]))
        #debug_printf('PowerConsumption: ' + str(self.mc_power_consumption[pt]))
       
        #self.mc_antenna_energy_efficient[pt] = self.mc_data_rate[pt] - (self.energy_efficient * self.mc_power_consumption[pt]) + self.mc_high_rate_constraint[pt] + self.mc_low_rate_constraint[pt] + self.mc_interference_reuse_constraint[pt] + self.mc_maximum_transmit_power_constraint[pt]
        self.mc_antenna_energy_efficient[pt] = self.mc_data_rate[pt] - (self.energy_efficient * self.mc_power_consumption[pt]) + self.mc_high_rate_constraint[pt] + self.mc_low_rate_constraint[pt] + self.mc_maximum_transmit_power_constraint[pt]
        #debug_printf('EnergyEfficient: ' + str(self.mc_antenna_energy_efficient[pt]))



    def mc_initial_particles(self):
        numpy.set_printoptions(precision=2)
        nUes = len(self.connected_ues)
        for pt in range(0,self.NPARTICLES):
            debug_printf("\n----- PARTICULA " + str(pt+1) + " -----")
            for rb in range(0,self.TOTAL_RBS): #RB
                #Usuario
                ue = self.mc_random_by_noise_p(rb, None)
                if ue > -1:
                    self.mc_a[pt,ue,rb] = 1
                    self.mc_ee_partial_calc(pt,ue,rb)
            self.mc_ee_final_calc(pt) 
            
            debug_printf("Alloc = \n" + str(numpy.matrix(self.mc_a[pt])))
            debug_printf("Power = \n" + str(numpy.matrix(self.p)))
            debug_printf("Noise = \n" + str(numpy.matrix(self.i)))


    def mc_new_particles_generation(self):
        nUes = len(self.connected_ues)
        hist = self.NPARTICLES * self.HISTORICALRATE
        if (hist < 1):
            hist = 1 
        for pt in range(0,self.NPARTICLES):
            if pt < hist:
                #debug_printf("Mantem historico")
                index = numpy.argmax(self.mc_hist_ee)
                self.mc_hist_ee[index] = -1  
                selected_particle = self.mc_ant_a[index]
                for rb in range(0,self.TOTAL_RBS):
                    ue = numpy.argmax(selected_particle[:,rb])
                    #debug_printf("UE:", ue)
                    if ue > -1:
                        self.mc_a[pt,ue,rb] = 1
                        self.mc_ee_partial_calc(pt,ue,rb)
                debug_printf("Alloc = \n" + str(numpy.matrix(self.mc_a[pt])))
                debug_printf("AllocAnt = \n" + str(selected_particle))
            else:
                selected_particle = self.mc_ant_a[self.mc_roulette[pt]]
                for rb in range(0,self.TOTAL_RBS):
                    ue = self.mc_random_by_noise_p(rb, selected_particle)
                    if ue > -1:
                        debug_printf("\nSet 1\n")
                        self.mc_a[pt,ue,rb] = 1
                        self.mc_ee_partial_calc(pt,ue,rb)
            self.mc_ee_final_calc(pt) 


    def mc_random_by_noise_p(self, rb, particle):
        debug_printf("\nRandon for K = : " + str(rb))
        roleta_ues = numpy.zeros(shape=(len(self.connected_ues))) 
        ant = 0       
        mean = 0
        for ue in range(0, len(self.connected_ues)):
            ri = 1
            if (numpy.max(self.i)!=0):
                if self.i[ue,rb] !=0:
                    ri = (self.i[ue,rb]/numpy.max(self.i))
                else:
                    ri = (self.noise()/numpy.max(self.i))
            if (ri==0):
                ri = 1
            roleta_ues[ue] = (self.p[ue,rb]/numpy.max(self.p))/ri
            debug_printf("RValue("+str(roleta_ues[ue])+") =  p("+str(self.p[ue,rb])+")/maxp("+str(numpy.max(self.p))+")/ri("+str(ri)+")")
            if particle != None:
                debug_printf("Ganho da particula base: " + str(particle[ue,rb]+1))
                roleta_ues[ue] = roleta_ues[ue] * (particle[ue,rb]+1)
            mean = mean + roleta_ues[ue]
            roleta_ues[ue] = roleta_ues[ue] + ant
            ant = roleta_ues[ue]

        debug_printf("Sum: " + str(mean))
        mean = mean/len(self.connected_ues)
        tzero = -mean
        debug_printf("Mean: " + str(mean))
        debug_printf("Tzero: " + str(tzero))
        debug_printf("Max: " + str(max(roleta_ues)))

        
        rd = random.uniform(tzero, max(roleta_ues))
        debug_printf("Random: " + str(rd))
        debug_printf("Roulet: " + str(roleta_ues))
        if rd > 0:
            for t in range(0, len(self.connected_ues)):
                debug_printf("IF " + str(rd) +"<="+ str(roleta_ues[t]))
                if rd <= roleta_ues[t]:
                    debug_printf("Return " + str(t))
                    return t
        debug_printf("Return -1")
        return -1

    def mc_backup_particles(self):
        self.mc_ant_a = self.mc_a
 

    def mc_select_current_solution(self):
        self.mc_hist_ee = list(self.mc_antenna_energy_efficient)
        index = numpy.argmax(self.mc_antenna_energy_efficient)        
        self.energy_efficient = self.mc_antenna_energy_efficient[index]        
        debug_printf("Max value element : index"+ str(index) + str(self.energy_efficient))
        self.a = self.mc_a[index]


    def mc_spinning_roulette(self):
        area = np.zeros(shape=(self.NPARTICLES))
        result = np.zeros(shape=(self.NPARTICLES))
        total = sum(self.mc_antenna_energy_efficient)
        ant = 0;
        for q in range(0, self.NPARTICLES):
            area[q] = ant + self.mc_antenna_energy_efficient[q]
            ant = area[q]

        #TODO: transformar em uma distribuicao gaussian

        for q in range(0, self.NPARTICLES):
            rd = random.uniform(0.0, total)
            for t in range(0, self.NPARTICLES):
                if rd < area[t]:
                    result[q] = t
                    break

        self.mc_roulette = result


    def mc_raises_temperature(self):
        self.L_BETA = self.L_BETA * 2
        self.L_LAMBDA = self.L_LAMBDA * 2
        self.L_UPSILON = self.L_UPSILON * 2
        self.E_DEALTA = self.E_DEALTA * 2


