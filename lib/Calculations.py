import math
import scipy.spatial
import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import antenna as Antenna
import util 
import threeGPP
from user import *

############################################
####          begin-refactor   
############################################
def power_interference(ue, rb, antenna, grid, particle = 0):
    user = antenna.connected_ues[ue]
    interference = 0
    for ant in grid.antennas:
        if (antenna._id != ant._id and ant.a != None and len(ant.connected_ues) > 0):
            index = numpy.argmax(ant.a[particle, :, rb])
            if ant.a[particle, index, rb] > 0:
                R  =  util.dist(antenna.connected_ues[ue], ant)
                if (ant.type == ant.BS_ID):
                    interference += abs(util.friis(ant.p[particle, index, rb], threeGPP.HPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH))
                else:
                    interference += abs(util.friis(ant.p[particle, index, rb], threeGPP.LPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH))
                #print ue._id, ant._id, R, interference, self.p_particles[particle, index, arb_index]

    #print interference
    return interference


def transmission_power(antenna, user, interferece):
    R = util.dist(user, antenna)
    if (antenna.type == antenna.BS_ID):
        p = p_friis(antenna, interferece, util.noise(), threeGPP.HPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH) #dBm
    else:
        p = p_friis(antenna, interferece, util.noise(), threeGPP.LPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH) #dBm
    return p

def p_friis(antenna, I, N, Gt, Gr, R, Wl):
    Pt = threeGPP.TARGET_SINR + (abs(I)+N) - Gt - Gr - (20 * math.log(Wl/(4*math.pi*R), 10))
    if (antenna.type == antenna.BS_ID):
        if Pt > threeGPP.POWER_BS:
            Pt = threeGPP.POWER_BS
    else:
        if Pt > threeGPP.POWER_RRH:
            Pt = threeGPP.POWER_RRH
    return Pt

def demand_in_rbs(ue):
    demanda_bits = 0
    if ue._type == User.HIGH_RATE_USER:
        demanda_bits = threeGPP.NR
    else:
        demanda_bits = threeGPP.NER
    demanda_bits = demanda_bits - ue.tx_rate

    if demanda_bits < 0:
        demanda_bits = 1
    r = int(math.ceil(demanda_bits/threeGPP.RB_BIT_CAPACITY))
    if r < 1:
        r = 1
    return r

def datarate(antenna, particle = 0):
    antenna.datarate[particle] = 0
    antenna.meet_users[particle] = 0
    antenna.datarate_constraint[particle] = 0
    if antenna.connected_ues != None:
        antenna.user_datarate[particle] = numpy.zeros(shape=(len(antenna.connected_ues)))
        for n in range(0, len(antenna.connected_ues)):
            for k in range (0, threeGPP.TOTAL_RBS):
                data_bits = (util.shannon((antenna.a[particle][n][k] * threeGPP.B0), util.sinr(antenna.p[particle][n][k], antenna.i[particle][n][k], util.noise())))/2000#Qnt de bits em 0,5 ms
                antenna.datarate[particle] += data_bits
                antenna.user_datarate[particle][n] += data_bits
            if antenna.connected_ues[n]._type == antenna.connected_ues[n].HIGH_RATE_USER:
                if(antenna.user_datarate[particle, n] < threeGPP.NER):
                    antenna.datarate_constraint[particle] += (antenna.user_datarate[particle, n] - threeGPP.NR)
                else:
                    antenna.meet_users[particle] += 1
            else:
                if(antenna.user_datarate[particle, n] < threeGPP.NER):
                    antenna.datarate_constraint[particle] += (antenna.user_datarate[particle, n] - threeGPP.NER)
                else:
                    antenna.meet_users[particle] += 1
                    

def consumption(antenna, particle = 0):
    antenna.consumition[particle] = 0
    result = 0
    for n in range(0, len(antenna.connected_ues)):
        for k in range(0, threeGPP.TOTAL_RBS):
            result += util.dBm_to_watts(antenna.a[particle][n][k] * antenna.p[particle][n][k])   
    if (antenna.type == antenna.BS_ID):
        antenna.consumition[particle] = (threeGPP.MEFF * result) + threeGPP.PMC + threeGPP.PMBH
    else:
        antenna.consumition[particle] = (threeGPP.EFF * result) + threeGPP.PMC + threeGPP.PMBH

def efficiency(antenna, particle = 0):
    antenna.energy_efficient[particle] = antenna.datarate[particle]/threeGPP.CHANNEL/antenna.consumition[particle]

def fairness(antenna, particle = 0):
    x1 = 0
    x2 = 0
    n = len(antenna.connected_ues)
    for ue in range(0, len(antenna.connected_ues)):
        x1 += antenna.user_datarate[particle, ue]
        x2 += math.pow(antenna.user_datarate[particle, ue], 2)
    x1 = math.pow(x1, 2)
    if (x2 == 0):
        return 1

    r = x1/(x2*n)
    antenna.fairness[particle] = r

def gridfairness(grid, particle = 0):
    x1 = 0
    x2 = 0
    n = len(grid.users)
    for antenna in grid.antennas:
        for ue in range(0, len(antenna.connected_ues)):
            x1 += antenna.user_datarate[particle, ue]
            x2 += math.pow(antenna.user_datarate[particle, ue], 2)
    x1 = math.pow(x1, 2)
    if (x2 == 0):
        return 1
    r = x1/(x2*n)
    grid.fairness[particle] = r

def griddatarate(grid, particle = 0):
    grid.datarate[particle] = 0
    grid.meet_users[particle] = 0
    for ant in grid.antennas:
        datarate(ant, particle)
        grid.datarate[particle] += ant.datarate[particle]
        grid.meet_users[particle] += ant.meet_users[particle]

def gridconsumption(grid, particle = 0):
    grid.consumition[particle] = 0
    for ant in grid.antennas:
        consumption(ant, particle)
        grid.consumition[particle] += ant.consumition[particle]

def gridefficiency(grid, particle = 0):
    grid.energy_efficient[particle] = (grid.datarate[particle]*2000/1048576)/threeGPP.CHANNEL/grid.consumition[particle]


def datarate_constraint(grid, particle = 0):
    datarate_constraint = 0
    for antenna in grid.antennas:
        antenna.datarate_constraint[particle] = 0
        for ue in range(0, len(antenna.connected_ues)):
            user = antenna.connected_ues[ue]
            if user._type == User.HIGH_RATE_USER: 
                if(antenna.user_datarate[particle, ue] < threeGPP.NR):
                    datarate_constraint += (antenna.user_datarate[particle, ue] - threeGPP.NR)
                    antenna.datarate_constraint[particle] += (antenna.user_datarate[particle, ue] - threeGPP.NR)
            else:
                if(antenna.user_datarate[particle, ue] < threeGPP.NER):
                    datarate_constraint += (antenna.user_datarate[particle, ue] - threeGPP.NER)
                    antenna.datarate_constraint[particle] += (antenna.user_datarate[particle, ue] - threeGPP.NER)
            
    return datarate_constraint
    
def fairness_constraint(grid, particle = 0):
    return grid.fairness[particle] - 1

def weighted_efficient(efficient_weight, energy_efficient, datarate_weight, datarate_constraint, fairness_weight, fairness_constraint):
    return efficient_weight * energy_efficient + datarate_weight * datarate_constraint + fairness_weight * fairness_constraint








############################################
####          end-refactor   
############################################

# def power_interference(ue, rb, antenna, grid, particle = 0):
#     user = antenna.connected_ues[ue]
#     power_interfering = 0
#     for ant in grid._antennas:
#         if (user._connected_antenna._id != ant._id and ant.a != None and sum(ant.a[particle,:,rb])>0):
#             index = numpy.argmax(ant.a[particle,:,rb])            
#             power_interfering += util.dbm_to_mw(received_power(ant.connected_ues[index], ant))
    
#     if power_interfering > 0:
#         return util.mw_to_dbm(util.dbm_to_mw(power_interfering) + util.dbm_to_mw(util.path_loss(user, antenna)))
#     else:
#         return util.path_loss(user, antenna)

# def snr(ue, rb, antenna, particle=0):
#     power = received_power(ue, rb, antenna, particle)
#     power_interfering = antenna.i[particle, ue, rb]
#     if power_interfering != 0:
#         snr = util.dbm_to_mw(power) / (util.dbm_to_mw(util.noise()) + util.dbm_to_mw(power_interfering))
#     else:
#         snr = power / (util.dbm_to_mw(util.noise()))

#     return util.mw_to_dbm(snr)

# def received_power(ue, rb, antenna, particle=0):
#     user = antenna.connected_ues[ue]
#     R  =  util.dist(user, antenna)
#     if (antenna.type == antenna.BS_ID):
#         return util.friis(antenna.p[particle,ue,rb], threeGPP.HPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH)
#     else:
#         return util.friis(antenna.p[particle,ue,rb], threeGPP.LPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH)


#def interference(ue, rb, antennas):
#    interference = 0
#    for ant in antennas:
#        if (ue._connected_antenna._id != ant._id and ant.a != None and sum(ant.a[:,rb])>0):
#            index = numpy.argmax(ant.a[:,rb])
#            R  =  dist(ue, ant)
#            interference += abs(friis(ant.p[index,rb], ant.T_GAIN, ant.R_GAIN, R, ant.WAVELENTH))#dBm
#    return interference
                            
# def list_antennas_in_antennas(self, antennas, nAnt):
#     for ant in antennas:
#         if ant._id != antennas[nAnt]._id:
#             antennas[nAnt]._others_ant.append(antennas[nAnt])

# def obtain_interference_and_power(self, grid):
#     for ue in range (0, len(self.connected_ues)):
#         for rb in range (0, self.TOTAL_RBS):
#             self.i[ue][rb] = util.interference(self.connected_ues[ue], rb, grid._antennas) #dBm
#             R  =  util.dist(self.connected_ues[ue], self)
#             self.p[ue][rb] = self.p_friis(self.i[ue][rb], self.noise(), self.T_GAIN, self.R_GAIN, R, self.WAVELENTH) #dBm

#     #calculate bandwidth required to meet user
# def calculate_necessary_rbs( user, antenna ):
#     bits = snr_to_bit(snr( user, antenna ))
#     rbs = int( math.ceil( math.ceil( ( user.demand/1000 )/( 12*7*bits ) )/2.0 ) ) #demanda em ms
#     #print rbs
#     return rbs