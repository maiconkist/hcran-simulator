import math
import numpy
import util
import controller
import random
from antenna import *
from user import *
from util import *

DEBUG = False

def debug_printf(string):
    if DEBUG:
        print(string)


class AntennaMc(Antenna):

    def __init__(self, id, type, pos, radius, grid, bw = 1.4):
        Antenna.__init__(self, id, type, pos, radius, grid, bw)

    def init_mc(self, antennas, nAntennas):
        if len(self.connected_ues) == 0:
            return
        debug_printf("\n##########################\n## STARTING MONTE CARLO ##\n##########################\n")
        self.NPARTICLES = 1000
        self.L_BETA       = 0.1
        self.L_LAMBDA     = 0.1
        self.L_UPSILON    = 0.1
        self.E_DEALTA     = 0.2
        self.mc_data_rate = np.zeros(shape=(self.NPARTICLES))
        self.mc_power_consumption = np.zeros(shape=(self.NPARTICLES))
        self.mc_high_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_low_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_interference_reuse_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_maximum_transmit_power_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_antenna_energy_efficient = np.zeros(shape=(self.NPARTICLES))
        self.mc_a = numpy.zeros(shape=(self.NPARTICLES,len(self.connected_ues), self.TOTAL_RBS))
        self.mc_roulette = numpy.zeros(shape=(self.NPARTICLES))
        #Re style variables
        self.snir = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))
        self.noise_plus_interference = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))
        self.a = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))
        self.p = numpy.zeros(shape=(len(self.connected_ues), self.TOTAL_RBS))


    def mc_clean_variables(self):
        #del self.mc_data_rate 
        #del self.mc_power_consumption 
        #del self.mc_high_rate_constraint 
        #del self.mc_low_rate_constraint 
        #del self.mc_interference_reuse_constraint 
        #del self.mc_maximum_transmit_power_constraint 
        #del self.mc_antenna_energy_efficient
        #del self.mc_a 
        #del self.mc_roulette 
        self.mc_data_rate = np.zeros(shape=(self.NPARTICLES))
        self.mc_power_consumption = np.zeros(shape=(self.NPARTICLES))
        self.mc_high_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_low_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_interference_reuse_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_maximum_transmit_power_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_antenna_energy_efficient = np.zeros(shape=(self.NPARTICLES))
        self.mc_a = numpy.zeros(shape=(self.NPARTICLES,len(self.connected_ues), self.TOTAL_RBS))
        self.mc_roulette = numpy.zeros(shape=(self.NPARTICLES))


    def mc_ee_partial_calc(self,pt,ue,rb):
        self.mc_data_rate[pt] += (self.mc_a[pt,ue,rb] * Antenna.B0 * math.log(1+(self.noise_plus_interference[ue,rb] * self.p[ue,rb])))
        self.mc_power_consumption[pt] += (self.mc_a[pt,ue,rb] * self.p[ue,rb])
        if self.connected_ues[ue]._type == User.HIGH_RATE_USER:
            self.mc_high_rate_constraint[pt] += self.L_BETA * self.shannon((self.mc_a[pt,ue,rb] * Antenna.B0), self.p[ue,rb], self.noise_plus_interference[ue,rb]) - Antenna.NR
        else:
            self.mc_low_rate_constraint[pt] += self.L_BETA *  self.shannon((self.mc_a[pt,ue,rb] * Antenna.B0), self.p[ue,rb], self.noise_plus_interference[ue,rb]) - Antenna.NER
        self.mc_interference_reuse_constraint[pt] += self.L_LAMBDA * (self.E_DEALTA - (self.mc_a[pt,ue,rb] * self.p[ue,rb] * Antenna.DR2M * Antenna.PMmax ))
        self.mc_maximum_transmit_power_constraint[pt] += self.mc_a[pt,ue,rb] * self.p[ue,rb]


    def mc_ee_final_calc(self,pt):
        self.mc_power_consumption[pt] = Antenna.EFF * self.mc_power_consumption[pt] + Antenna.PRC + Antenna.PBH
        self.mc_interference_reuse_constraint[pt] = self.E_DEALTA - self.mc_interference_reuse_constraint[pt]
        self.mc_maximum_transmit_power_constraint[pt] = self.L_UPSILON * self.mc_maximum_transmit_power_constraint[pt]
        if self.type == self.BS_ID:
            self.mc_interference_reuse_constraint[pt] = Antenna.PMmax - self.mc_interference_reuse_constraint[pt]
        else:        
            self.mc_interference_reuse_constraint[pt] = Antenna.PRmax - self.mc_interference_reuse_constraint[pt]
        
        #debug_printf('DataRate: ' + str(self.mc_data_rate[pt]))
        #debug_printf('PowerConsumption: ' + str(self.mc_power_consumption[pt]))
       
        self.mc_antenna_energy_efficient[pt] = self.mc_data_rate[pt] - (self.energy_efficient * self.mc_power_consumption[pt]) + self.mc_high_rate_constraint[pt] + self.mc_low_rate_constraint[pt] + self.mc_interference_reuse_constraint[pt] + self.mc_maximum_transmit_power_constraint[pt]
        #debug_printf('EnergyEfficient: ' + str(self.mc_antenna_energy_efficient[pt]))



    def mc_initial_particles(self):
        nUes = len(self.connected_ues)
        for pt in range(0,self.NPARTICLES):
            for rb in range(0,self.TOTAL_RBS): #RB
                #Usuario
                ue = self.mc_random_by_noise_p(rb, None)
                if ue > 0:
                    self.mc_a[pt,ue,rb] = 1
                    self.mc_ee_partial_calc(pt,ue,rb)
            self.mc_ee_final_calc(pt) 
        debug_printf("----- PARTICULA " + str(pt+1) + " -----")
        debug_printf("Alloc = \n" + str(numpy.matrix(self.mc_a[pt])))
        debug_printf("Power = \n" + str(numpy.matrix(self.p)))
        debug_printf("Noise = \n" + str(numpy.matrix(self.noise_plus_interference)))


    def mc_new_particles_generation(self):
        nUes = len(self.connected_ues)
        for pt in range(0,self.NPARTICLES):
            selected_particle = self.mc_ant_a[self.mc_roulette[pt]]
            for rb in range(0,self.TOTAL_RBS):
                ue = self.mc_random_by_noise_p(rb, selected_particle)
                if ue > 0:
                    self.mc_a[pt,ue,rb] = 1
                    self.mc_ee_partial_calc(pt,ue,rb)
            self.mc_ee_final_calc(pt) 


    def mc_random_by_noise_p(self, rb, particle):
        roleta_ues = numpy.zeros(shape=(len(self.connected_ues))) 
        ant = 0       
        mean = 0
        for ue in range(0, len(self.connected_ues)):
            rsnr = 1
            if (max(self.noise_plus_interference[:,rb])!=0):
                rsnr = (self.noise_plus_interference[ue,rb]/max(self.noise_plus_interference[:,rb]))
            if (rsnr==0):
                rsnr = 1
            roleta_ues[ue] = (self.p[ue,rb]/max(self.p[:,rb]))/rsnr
            if particle != None:
                roleta_ues[ue] = roleta_ues[ue] * (particle[ue,rb]+1)
            mean = mean + roleta_ues[ue]
            roleta_ues[ue] = roleta_ues[ue] + ant
            ant = roleta_ues[ue]

        #print "Sum: " + str(mean)
        mean = mean/len(self.connected_ues)
        tzero = -mean
        #print "Mean: " + str(mean)
        #print "Tzero: " + str(tzero)
        #print "Max: " + str(max(roleta_ues))

        
        rd = random.uniform(tzero, max(roleta_ues))
        #print "Random: " + str(rd)
        if rd > 0:
            for t in range(0, len(self.connected_ues)):
                if rd < roleta_ues[t]:
                    return t
        return -1

    def mc_backup_particles(self):
        self.mc_ant_a = self.mc_a
 

    def mc_select_current_solution(self):
        index = numpy.argmax(self.mc_antenna_energy_efficient)        
        self.energy_efficient = self.mc_antenna_energy_efficient[index]        
        debug_printf("Max value element : " + str(self.energy_efficient))
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
        self.L_BETA += 0.1
        self.L_LAMBDA += 0.1
        self.L_UPSILON += 0.1
        self.E_DEALTA += 0.2


