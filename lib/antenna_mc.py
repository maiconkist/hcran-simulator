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
        if len(self._ues) == 0:
            return

        debug_printf("\n##########################\n## STARTING MONTE CARLO ##\n##########################\n")
        self._others_ant = []
        self.list_antennas_in_antennas(antennas, nAntennas)
        self.NPARTICLES = 10
        self.E_BETA       = 0.1
        self.E_LAMBDA     = 0.1
        self.E_UPSILON    = 0.1
        self.E_DEALTA     = 0.2
        self.TOTAL_RBS   = 5
        self._antenna_energy_efficient = 0
        self.mc_data_rate = np.zeros(shape=(self.NPARTICLES))
        self.mc_power_consumption = np.zeros(shape=(self.NPARTICLES))
        self.mc_high_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_low_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_interference_reuse_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_maximum_transmit_power_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_antenna_energy_efficient = np.zeros(shape=(self.NPARTICLES))
        #self.mc_cnir = numpy.zeros(shape=(self.NPARTICLES, len(self._ues), self.TOTAL_RBS))
        self.mc_a = numpy.zeros(shape=(self.NPARTICLES,len(self._ues), self.TOTAL_RBS))
        #self.mc_p = numpy.zeros(shape=(self.NPARTICLES,len(self._ues), self.TOTAL_RBS))
        self._cnir = numpy.zeros(shape=(len(self._ues), self.TOTAL_RBS))
        self._a = numpy.zeros(shape=(len(self._ues), self.TOTAL_RBS))
        self._p = numpy.zeros(shape=(len(self._ues), self.TOTAL_RBS))
        self._w = numpy.zeros(shape=(len(self._ues), self.TOTAL_RBS))
        self.mc_roulette = numpy.zeros(shape=(self.NPARTICLES))


    def clean_mc_variables(self):
        self.mc_data_rate = np.zeros(shape=(self.NPARTICLES))
        self.mc_power_consumption = np.zeros(shape=(self.NPARTICLES))
        self.mc_high_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_low_rate_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_interference_reuse_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_maximum_transmit_power_constraint = np.zeros(shape=(self.NPARTICLES))
        self.mc_antenna_energy_efficient = np.zeros(shape=(self.NPARTICLES))
        #self.mc_cnir = numpy.zeros(shape=(self.NPARTICLES, len(self._ues), self.TOTAL_RBS))
        self.mc_a = numpy.zeros(shape=(self.NPARTICLES,len(self._ues), self.TOTAL_RBS))
        #self.mc_p = numpy.zeros(shape=(self.NPARTICLES,len(self._ues), self.TOTAL_RBS))
        self.mc_roulette = numpy.zeros(shape=(self.NPARTICLES))


    def list_antennas_in_antennas(self, antennas, nAnt):
        for ant in antennas:
            if ant._id != antennas[nAnt]._id:
                antennas[nAnt]._others_ant.append(antennas[nAnt])

            #ant.init_ee(grid.TOTAL_RBS, antennas[nAnt]._others_ant, i)  

    def ee_partial_calc(self,pt,ue,rb):
        self.mc_data_rate[pt] += (self.mc_a[pt,ue,rb] * Antenna.B0 * math.log(1+(self._cnir[ue,rb] * self._p[ue,rb])))
        self.mc_power_consumption[pt] += (self.mc_a[pt,ue,rb] * self._p[ue,rb])
        if self._ues[ue]._type == User.HIGH_RATE_USER:
            self.mc_high_rate_constraint[pt] += self.E_BETA * ((self.mc_a[pt,ue,rb] * Antenna.B0 * math.log(1+(self._cnir[ue,rb] * self._p[ue,rb])) - Antenna.NR))
        else:
            self.mc_low_rate_constraint[pt] += self.E_BETA * ((self.mc_a[pt,ue,rb] * Antenna.B0 * math.log(1+(self._cnir[ue,rb] * self._p[ue,rb])) - Antenna.NER))
        self.mc_interference_reuse_constraint[pt] += self.E_LAMBDA * (self.E_DEALTA - (self.mc_a[pt,ue,rb] * self._p[ue,rb] * Antenna.DR2M * Antenna.PMmax ))
        self.mc_maximum_transmit_power_constraint[pt] += self.mc_a[pt,ue,rb] * self._p[ue,rb]


    def ee_final_calc(self,pt):
        self.mc_power_consumption[pt] = Antenna.EFF * self.mc_power_consumption[pt] + Antenna.PRC + Antenna.PBH
        self.mc_interference_reuse_constraint[pt] = self.E_DEALTA - self.mc_interference_reuse_constraint[pt]
        self.mc_maximum_transmit_power_constraint[pt] = self.E_UPSILON * self.mc_maximum_transmit_power_constraint[pt]
        if self.type == self.BS_ID:
            self.mc_interference_reuse_constraint[pt] = Antenna.PMmax - self.mc_interference_reuse_constraint[pt]
        else:        
            self.mc_interference_reuse_constraint[pt] = Antenna.PRmax - self.mc_interference_reuse_constraint[pt]
        
        debug_printf('DataRate: ' + str(self.mc_data_rate[pt]))
        debug_printf('PowerConsumption: ' + str(self.mc_power_consumption[pt]))
       
        self.mc_antenna_energy_efficient[pt] = self.mc_data_rate[pt] - (self._antenna_energy_efficient * self.mc_power_consumption[pt]) + self.mc_high_rate_constraint[pt] + self.mc_low_rate_constraint[pt] + self.mc_interference_reuse_constraint[pt] + self.mc_maximum_transmit_power_constraint[pt]
        debug_printf('EnergyEfficient: ' + str(self.mc_antenna_energy_efficient[pt]))

    def interference_calc(self, grid):
        for ue in range (0, len(self._ues)):
            for rb in range (0, self.TOTAL_RBS):
                self._cnir[ue][rb] = peng_power_interfering(self._ues[ue], rb, grid._antennas)
                self._p[ue][rb] = self.calculate_p(ue, rb)
                self._w[ue][rb]= self.waterfilling_optimal(ue, rb)

    def waterfilling_optimal(self, n, k):
        #TODO: corrigir isso        
        #p1 = (Antenna.B0 * (1 + self.E_BETA)) 
        #p2 = math.log(self._antenna_energy_efficient * Antenna.EFF + self.E_LAMBDA * Antenna.DR2M * Antenna.HR2M + self.E_UPSILON)
        #return p1 / p2
        return 1


    def calculate_p(self, n, k):
        #Obtain P                                                                                
        p = self.waterfilling_optimal(n,k) - (1 / self._cnir[n][k])                                               
        return p

    def initial_particles(self):
        nUes = len(self._ues)
        for pt in range(0,self.NPARTICLES):
            for rb in range(0,self.TOTAL_RBS): #RB
                #ue = random.randint(-(nUes/3),nUes)-1 #Usuario
                ue = self.random_by_cnir_p(rb, None)
                if ue > 0:
                    self.mc_a[pt,ue,rb] = 1
                    #self.mc_cnir[pt,ue,rb] = self._cnir[ue][rb]
                    #self.mc_p[pt,ue,rb] = self.calculate_p(ue, rb) # aqui tu calcula p
                    self.ee_partial_calc(pt,ue,rb)
            self.ee_final_calc(pt) 
        debug_printf("----- PARTICULA " + str(pt+1) + " -----")
        debug_printf("A = \n" + str(numpy.matrix(self.mc_a[pt])))
        debug_printf("P = \n" + str(numpy.matrix(self._p)))
        debug_printf("CNIR = \n" + str(numpy.matrix(self._cnir)))


    def new_particles_generation(self):
        nUes = len(self._ues)
        for pt in range(0,self.NPARTICLES):
            selected_particle = self.mc_ant_a[self.mc_roulette[pt]]
            for rb in range(0,self.TOTAL_RBS):
                # como gerar a matript a baseada na mSel?????
                #if random.choice([True, False, False]): #30% de chance de trocar
                #    ue = random.randint(-(nUes/3),nUes)-1 #Usuario
                #    if ue > 0:        
                #        self.mc_a[pt,ue,rb] = 1
                #        #self.mc_cnir[pt,ue,rb] =  self._cnir[ue][rb]                        
                #        #self._p[ue,rb] =  self.calculate_p(ue, rb)
                #        self.ee_partial_calc(pt,ue,rb)
                #else:
                #    ue = numpy.argmax(self.mc_ant_a[pt,:,rb])
                #    self.mc_a[pt,ue,rb] = 1
                #    #self.mc_cnir[pt,ue,rb] = self._cnir[ue][rb]
                #    #self._p[pt,ue,rb] = self.calculate_p(ue, rb)                     
                #    self.ee_partial_calc(pt,ue,rb)
                ue = self.random_by_cnir_p(rb, selected_particle)
                if ue > 0:
                    self.mc_a[pt,ue,rb] = 1
                    self.ee_partial_calc(pt,ue,rb)
            self.ee_final_calc(pt) 
            #TODO: atualizar multiplicadores de lagrange
            #self.mt_update_l(pt)

    def random_by_cnir_p(self, rb, particle):
        roleta_ues = numpy.zeros(shape=(len(self._ues))) 
        ant = 0       
        mean = 0
        for ue in range(0, len(self._ues)):
            roleta_ues[ue] = (self._p[ue,rb]/max(self._p[rb]))/(self._cnir[ue,rb]/max(self._cnir[rb]))
            if particle != None:
                roleta_ues[ue] = roleta_ues[ue] * (particle[ue,rb]+1)
            mean = mean + roleta_ues[ue]
            roleta_ues[ue] = roleta_ues[ue] + ant
            ant = roleta_ues[ue]

        mean = mean/len(self._ues)
        tzero = -mean
        rd = random.uniform(tzero, max(roleta_ues))
        if rd > 0:
            for t in range(0, len(self._ues)):
                if rd < roleta_ues[t]:
                    return t
        return -1

    def backup_particles(self):
        self.mc_ant_a = self.mc_a
 

    def select_current_solution(self):
        index = numpy.argmax(self.mc_antenna_energy_efficient)        
        self._antenna_energy_efficient = self.mc_antenna_energy_efficient[index]        
        debug_printf("Max value element : " + str(self._antenna_energy_efficient))
        self._a = self.mc_a[index]
        #self._p = self.mc_p[index]
        #self._cnir = self.mc_cnir[index]
 

    def spinning_roulette(self):
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
