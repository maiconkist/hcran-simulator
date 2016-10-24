import math
import scipy.spatial
import numpy
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
    #print "\n\n"
    for ant in grid.antennas:
        if (antenna._id != ant._id and ant.a != None and len(ant.connected_ues) > 0):
            index = numpy.argmax(ant.a[particle, :, rb])
            if ant.a[particle, index, rb] > 0 and math.isnan(ant.p[particle, index, rb]) == False:
                intef = util.friis_loss(ant.p[particle, index, rb], antenna.connected_ues[ue], ant)
                if intef != None:
                    interference += util.dbm_to_mw(intef)

    if interference > 0:
        i = util.mw_to_dbm(interference)
        return i
    else:
        return None
    
def gaussian_sinr(power, path_loss, interference, noise):
    #print power, path_loss, interference, noise
    if interference != None and math.isnan(interference) == False:
        sinr = util.dbm_to_mw(power) - util.dbm_to_mw(path_loss)/(util.dbm_to_mw(noise)+ util.dbm_to_mw(interference))
    else:
        sinr = util.dbm_to_mw(power) - util.dbm_to_mw(path_loss)/(util.dbm_to_mw(noise))
    #print "SINR", sinr
    #sinr = util.mw_to_dbm(sinr)
    return sinr
        

def transmission_power(antenna, user, interference, noise, Tsinr, particle = 0):
    path_loss = util.path_loss(user, antenna)
    #if antenna.type == antenna.BS_ID:
    ##    print "BS Power"
    #else:
    #    print "RRH Power"
    #(Pt - util.dbm_to_mw(path_loss))/(util.dbm_to_mw(interferece) + util.dbm_to_mw(noise)) = util.dbm_to_mw(Tsinr) 
    #print interference, noise, Tsinr, particle, math.isnan(interference)
    if interference != None and math.isnan(interference) == False:
        Pt = (util.dbm_to_mw(interference) + util.dbm_to_mw(noise)) * Tsinr + util.dbm_to_mw(path_loss)
    else:
        Pt = (util.dbm_to_mw(noise)) * Tsinr + util.dbm_to_mw(path_loss)
    
    #print "Power"
    rest = antenna.rest_power(particle)
    if rest != None:
        rest = util.dbm_to_mw(rest)
        if (Pt > rest):
            Pt = rest
        Pt = util.mw_to_dbm(Pt)
        #print Pt
        return Pt
    else:
        #print None
        return None

def demand_in_rbs(antenna, ue, particle = 0):
    user = antenna.connected_ues[ue]
    demanda_bits = 0
    if user._type == User.HIGH_RATE_USER:
        demanda_bits = threeGPP.NR
    else:
        demanda_bits = threeGPP.NER
    #print "User datarate", antenna.user_datarate[particle, ue]
    demanda_bits = demanda_bits - antenna.user_datarate[particle, ue]

    if demanda_bits < 0:
        demanda_bits = 1
    r = int(math.ceil(demanda_bits/(util.shannon(threeGPP.B0, threeGPP.TARGET_SINR)/2000)))
    if r < 1:
        r = 1
    return r

def datarate(antenna, grid, particle = 0):
    if particle < 0:
        antenna.datarate[0] = 0
        antenna.meet_users[0] = 0
        antenna.datarate_constraint[0] = 0
        if antenna.connected_ues > 0:
            antenna.user_datarate[0] = numpy.zeros(shape=(len(antenna.connected_ues)))
            for n in range(0, len(antenna.connected_ues)):
                for k in range (0, threeGPP.TOTAL_RBS):
                    if antenna.a[0][n][k] > 0 and math.isnan(antenna.p[0][n][k]) == False:
                        #print "Power", antenna.p[0][n][k]

                        antenna.i[0][n][k] = None
                        data_bits = (util.shannon((antenna.a[0][n][k] * threeGPP.B0), gaussian_sinr(antenna.p[0][n][k], util.path_loss(antenna.connected_ues[n], antenna),antenna.i[0][n][k], util.noise())))/2000#Qnt de bits em 0,5 ms
                        antenna.datarate[0] += data_bits
                        antenna.user_datarate[0][n] += data_bits
                        #print "Ant data", antenna.user_datarate[0][0]
                if antenna.connected_ues[n]._type == antenna.connected_ues[n].HIGH_RATE_USER:
                    if(antenna.user_datarate[0, n] < threeGPP.NER):
                        antenna.datarate_constraint[0] += (antenna.user_datarate[0, n] - threeGPP.NR)
                    else:
                        antenna.meet_users[0] += 1
                else:
                    if(antenna.user_datarate[0, n] < threeGPP.NER):
                        antenna.datarate_constraint[0] += (antenna.user_datarate[0, n] - threeGPP.NER)
                    else:
                        antenna.meet_users[0] += 1
    else:
        antenna.datarate[particle] = 0
        antenna.meet_users[particle] = 0
        antenna.datarate_constraint[particle] = 0
        if antenna.connected_ues > 0:
            antenna.user_datarate[particle] = numpy.zeros(shape=(len(antenna.connected_ues)))
            for n in range(0, len(antenna.connected_ues)):
                for k in range (0, threeGPP.TOTAL_RBS):
                    if antenna.a[particle][n][k] > 0 and math.isnan(antenna.p[particle][n][k]) == False:
                        #print "Power", antenna.p[particle][n][k]
                        #antenna.i[particle][n][k] = power_interference(n, k, antenna, grid, particle)
                        data_bits = (util.shannon((antenna.a[particle][n][k] * threeGPP.B0), gaussian_sinr(antenna.p[particle][n][k], util.path_loss(antenna.connected_ues[n], antenna),antenna.i[particle][n][k], util.noise())))/2000#Qnt de bits em 0,5 ms
                        antenna.datarate[particle] += data_bits
                        antenna.user_datarate[particle][n] += data_bits
                        #print "Ant data", antenna.user_datarate[0][0]
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

        #print "Ant data contraint", antenna.datarate_constraint[particle]
                    

def consumption(antenna, particle = 0):
    antenna.consumition[particle] = 0
    result = 0
    for n in range(0, len(antenna.connected_ues)):
        result_ue = 0
        for k in range(0, threeGPP.TOTAL_RBS):
            if antenna.a[particle][n][k] > 0:
                #old_power = antenna.p[particle][n][k]
                #antenna.p[particle][n][k] = None
                #new_power = transmission_power(antenna, antenna.connected_ues[n], antenna.i[particle,n,k], util.noise(), threeGPP.TARGET_SINR, particle)
                #if new_power != None:
                #    antenna.p[particle][n][k] = new_power
                #else:
                #    antenna.p[particle][n][k] = old_power
                if math.isnan(antenna.p[particle][n][k]) == False:
                    result_ue += util.dbm_to_mw(antenna.p[particle][n][k]) 
        result += result_ue
        antenna.user_consumption[particle, n] = result_ue 
    if (antenna.type == antenna.BS_ID):
        antenna.consumition[particle] = (threeGPP.MEFF * result) + util.watts_to_mw(threeGPP.PMC) + util.watts_to_mw(threeGPP.PMBH)
    else:
        antenna.consumition[particle] = (threeGPP.EFF * result) + util.watts_to_mw(threeGPP.PMC) + util.watts_to_mw(threeGPP.PMBH)

def efficiency(antenna, particle = 0):
    antenna.energy_efficient[particle] = (antenna.datarate[particle]*2000/1048576)/(util.mw_to_watts(antenna.consumition[particle]))

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
    if particle < 0:
        grid.datarate[0] = 0
        grid.meet_users[0] = 0
        for ant in grid.antennas:
            if ant.connected_ues > 0:
                datarate(ant, grid, -1)
                #print "Ant data 3", ant.user_datarate[0][0]
                grid.datarate[0] += ant.datarate[0]
                grid.meet_users[0] += ant.meet_users[0]
    else:
        grid.datarate[particle] = 0
        grid.meet_users[particle] = 0
        for ant in grid.antennas:
            if ant.connected_ues > 0:
                datarate(ant, grid, particle)
                #print "Ant data 3", ant.user_datarate[0][0]
                grid.datarate[particle] += ant.datarate[particle]
                grid.meet_users[particle] += ant.meet_users[particle]

def gridconsumption(grid, particle = 0):
    grid.consumition[particle] = 0
    for ant in grid.antennas:
        consumption(ant, particle)
        grid.consumition[particle] += ant.consumition[particle]

def gridefficiency(grid, particle = 0):
    grid.energy_efficient[particle] = (grid.datarate[particle]*2000/1048576)/(util.mw_to_watts(grid.consumition[particle]))


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
# def transmission_power(antenna, user, interferece):
#     R = util.dist(user, antenna)
#     if (antenna.type == antenna.BS_ID):
#         p = p_friis(antenna, interferece, util.noise(), threeGPP.HPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH) #dBm
#     else:
#         p = p_friis(antenna, interferece, util.noise(), threeGPP.LPN_T_GAIN, threeGPP.UE_R_GAIN, R, threeGPP.WAVELENTH) #dBm
#     return p
# def p_friis(antenna, interferece, noise, Gt, Gr, R, Wl):
#     #Pt = threeGPP.TARGET_SINR * util.mw_to_dbm(util.dbm_to_mw(interferece) + util.dbm_to_mw(noise)) - Gt - Gr - (20 * math.log(Wl/(4*math.pi*R), 10))
#     #Pt = threeGPP.TARGET_SINR * (util.dbm_to_mw(interferece) + util.dbm_to_mw(noise))
#     #Pt = util.mw_to_dbm(Pt)

#     #sinr = util.mw_to_dbm(util.dbm_to_mw(power)/(util.dbm_to_mw(noise)+ util.dbm_to_mw(interference)))
#     #sinr = util.mw_to_dbm(sinr)

#     #Pt = threeGPP.TARGET_SINR * util.mw_to_dbm(util.dbm_to_mw(interferece) + util.dbm_to_mw(noise))
#     #sinrmw = /(util.dbm_to_mw(noise)+ util.dbm_to_mw(interference))
#     Pt = util.mw_to_dbm(util.dbm_to_mw(threeGPP.TARGET_SINR) * (util.dbm_to_mw(noise) + util.dbm_to_mw(interferece)))
    
#     if (antenna.type == antenna.BS_ID):
#         if Pt > threeGPP.POWER_BS:
#             Pt = threeGPP.POWER_BS
#     else:
#         if Pt > threeGPP.POWER_RRH:
#             Pt = threeGPP.POWER_RRH
#     return Pt

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