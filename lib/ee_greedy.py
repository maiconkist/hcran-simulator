#########################################################
# @file     ee_greedy.py
# @author   Gustavo de Araujo
# @date     03 Abr 2016
#########################################################

from antenna import Antenna
from grid import Grid
from util import *
import math
import csv

class Greedy(object):
    
    def __init__( self ):
        self.antenna_list = []
        self.user_list = []
        self.active_antennas = []
    
    def run( self, grid ):
        rrhs = grid._antennas
        ues = grid._user
        rrhs_used = []
        
        for ue in ues:
            distance = 10000
            users_no_met = 0
            near = rrhs[0]
            for rrh in rrhs:
                # pega a antena mais proxima que tenha RBs disponiveis
                d = dist( ue, rrh ) 
                if rrh.type == Antenna.BS_ID:
                    if (d < distance) and ((grid.TOTAL_RBS -1 - len(
                        rrh.resources)) >= calculate_necessary_rbs(ue,rrh)) and (d<Antenna.BS_RADIUS):
                        distance = d
                        near = rrh

                elif rrh.type == Antenna.RRH_ID:
                    if (d < distance) and ((grid.TOTAL_RBS -1
                        - len(rrh.resources)) >= calculate_necessary_rbs(ue,
                            rrh)) and (d<Antenna.RRH_RADIUS):
                        distance = d
                        near = rrh

            if near.type == Antenna.BS_ID:
                
                #inicio da proxima faixa de RBs
                from_rb = len( near.resources ) 

                from_rb += grid.TOTAL_RBS_RRH        
                to_rb = from_rb + calculate_necessary_rbs(ue, rrh) - 1
                if (to_rb<grid.TOTAL_RBS):
                    ue.from_rb = from_rb
                    ue.to_rb = to_rb
                    ue._connected_antenna = near
                    ue.power_connected_antenna = friis( ue, near )

                    #aloca RBs
                    for rb in range( from_rb, to_rb + 1):  
                        near.resources.append(rb)
                        grid.matrix_resources[near._id][rb] = ue._id

            elif near.type == Antenna.RRH_ID:
                #inicio da proxima faixa de RBs
                from_rb = len( near.resources ) 
                to_rb = from_rb + calculate_necessary_rbs(ue, rrh) - 1
                if (to_rb<grid.TOTAL_RBS_RRH):
                    ue.from_rb = from_rb
                    ue.to_rb = to_rb
                    ue._connected_antenna = near
                    ue.power_connected_antenna = friis(ue, near)
                    
                    # aloca RBs
                    for rb in range( from_rb, to_rb + 1):  
                        near.resources.append(rb)
                        grid.matrix_resources[near._id][rb] = ue._id

        for ue in reversed(ues):
            if ue._connected_antenna != None and ue._connected_antenna.type == Antenna.BS_ID and len(ue._connected_antenna.resources)<grid.TOTAL_RBS:
                ue.to_rb = grid.TOTAL_RBS - 1

                # aloca RBs
                for rb in range( ue.from_rb, ue.to_rb + 1):  
                    ue._connected_antenna.resources.append(rb)
                    grid.matrix_resources[ue._connected_antenna._id][rb] = ue._id

            elif ue._connected_antenna != None and ue._connected_antenna.type == Antenna.RRH_ID and len(ue._connected_antenna.resources)<grid.TOTAL_RBS_RRH:
                ue.to_rb = grid.TOTAL_RBS_RRH - 1

                # aloca RBs
                for rb in range( ue.from_rb, ue.to_rb + 1):  
                    ue._connected_antenna.resources.append( rb )
                    grid.matrix_resources[ ue._connected_antenna._id ][ rb ] = ue._id

        rbs_reutilized = []
        rbs_interf = []
        power_consume = 0
        sh_capacity = 0
        vazao_total = 0

        for ue in ues:
            if ue._connected_antenna != None:
                sinr_ue = 0
                from_rb = ue.from_rb
                to_rb = ue.to_rb
                id_antenna = ue._connected_antenna._id
                vazao_ue = 0
            
                if ue._connected_antenna not in rrhs_used:
                    rrhs_used.append(ue._connected_antenna)
            
                power_consume += ue.power_connected_antenna

                for j in range(from_rb, to_rb + 1):            
                    sinr = snr(ue, ue._connected_antenna, power_interfering(ue, j, grid))

                    #84RE com 2 RBs por ms para 1 segundo (1000 ms)
                    ue._tx_rate += snr_to_bit(sinr) *12*7*2*1000             

                sh_ue = math.floor(math.log((1 + sinr_ue), 2 ) * 180000)
                sh_capacity += sh_ue 
            
                vazao_total += ue._tx_rate
            
                if vazao_ue < ue.demand:
                    users_no_met += 1
            
            else:
                users_no_met += 1

        se = vazao_total/(grid._bandwidth*1000000)
        print 'SE:', se
        ee_with_off = calculate_energy_efficient(rrhs_used,vazao_total)
        print 'EE:', ee_with_off
'''        
        f = open('user_per_mhz.csv','a')   # Trying to create a new file or open one
        f.write(str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid._user))+','+str(len(rrhs_used))+','+str(users_no_met)+','+str(ee_with_off)+','+str(se)+','+str(grid._bandwidth)+','+str(vazao_total)+'\n')
        f.close()

        plot_grid( grid )
'''        
