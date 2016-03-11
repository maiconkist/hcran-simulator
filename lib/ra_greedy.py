from antenna import Antenna
from grid import Grid
from util import *
import math
import csv

class Greedy( object ):
    
    def __init__( self ):
        self.antenna_list = []
        self.user_list = []
        self.active_antennas = []
    
    def run( self, grid ):
        rrhs = grid._antennas
        ues = grid._user
        rrhs_used = []

        

        for ue in ues:
        #print 'UE' + str(ue.id)
            distance = 10000
            users_no_met = 0
            near = rrhs[0]
            for rrh in rrhs:
                d = dist( ue, rrh ) # pega a antena mais proxima que tenha RBs disponiveis
                #print ue._id, rrh._id, d
                if rrh.type == Antenna.BS_ID:
                    if d < distance and ( grid.TOTAL_RBS -1 - len( rrh.resources ) ) >= calculate_necessary_rbs(ue, rrh) and d<Antenna.BS_RADIUS:
                        #print len( rrh.resources )                
                        #print rrh.resources
                        distance = d
                        near = rrh
                elif rrh.type == Antenna.RRH_ID:
                    if d < distance and ( grid.TOTAL_RBS -1 - len( rrh.resources ) ) >= calculate_necessary_rbs(ue, rrh) and d<Antenna.RRH_RADIUS:
                        distance = d
                        near = rrh

            if near.type == Antenna.BS_ID:
                from_rb = len( near.resources ) #inicio da proxima faixa de RBs

                #if from_rb < Grid.TOTAL_RBS_RRH:
                from_rb += grid.TOTAL_RBS_RRH        
                to_rb = from_rb + calculate_necessary_rbs(ue, rrh) - 1
                if (to_rb<grid.TOTAL_RBS):
                    ue.from_rb = from_rb
                    ue.to_rb = to_rb
                    ue._connected_antenna = near
                    ue.power_connected_antenna = friis( ue, near )

                    for rb in range( from_rb, to_rb + 1): # aloca RBs 
                        near.resources.append( rb )
                        grid.matrix_resources[ near._id ][ rb ] = ue._id


            elif near.type == Antenna.RRH_ID:
                from_rb = len( near.resources ) #inicio da proxima faixa de RBs                
                to_rb = from_rb + calculate_necessary_rbs(ue, rrh) - 1
                if (to_rb<grid.TOTAL_RBS_RRH):
                    ue.from_rb = from_rb
                    ue.to_rb = to_rb
                    ue._connected_antenna = near
                    ue.power_connected_antenna = friis( ue, near )

                    for rb in range( from_rb, to_rb + 1): # aloca RBs 
                        near.resources.append( rb )
                        grid.matrix_resources[ near._id ][ rb ] = ue._id


        rbs_reutilized = []
        rbs_interf = []
        power_consume = 0
        sh_capacity = 0
        vazao_total = 0

    #print '#### Associacao ####'

        for ue in ues:
            if ue._connected_antenna != None:
                sinr_ue = 0
                from_rb = ue.from_rb
                to_rb = ue.to_rb
                id_antenna = ue._connected_antenna._id
                vazao_ue = 0
            
                if ue._connected_antenna not in rrhs_used:
                    rrhs_used.append( ue._connected_antenna )
            
                power_consume += ue.power_connected_antenna

                for j in range( from_rb, to_rb + 1):            
                    #if j not in ue.rb_excluded:
                    sinr = snr(ue, ue._connected_antenna, power_interfering(ue, j, grid))
                    #print sinr_db
                    #UM USUARIO PODE RECEBER DOIS RBS COM MODULAcOES DIFERETES??
                   
                    ue._tx_rate += snr_to_bit( sinr ) *12*7*2*1000 #84RE com 2 RBs por ms para 1 segundo (1000 ms)
                    #print sinr, snr_to_bit( sinr ), ue._tx_rate
                    #vazao_ue += vazao  
            
                #SHANNON ----> PORQUE NAO ESTA SENDO UTILIZADO????        
                sh_ue = math.floor( math.log( ( 1 + sinr_ue ), 2 ) * 180000 )
                sh_capacity += sh_ue #CAPACIDADE EM BITS DISPONIVEL PARA TRANSMISSAO
            
                vazao_total += ue._tx_rate
            
                #vazao_necessaria = calculate_necessary_rbs(ue, rrh) * 1008 #1008? ALGO RELACIONADO AOS RBs EM 0,5 ms 
                    
                if vazao_ue < ue.demand:
                    users_no_met += 1

                #print 'U:', ue._id, 'A:', id_antenna, 'RB', from_rb, ',', to_rb, 'V:',ue.demand, '/', ue._tx_rate
            else:
                users_no_met += 1
                #print 'U:', ue._id, 'A:', '?', 'RB', '?', ',', '?', 'V:',ue.demand, '/', '0'

        se = vazao_total/20000000
        print 'SE:', se
        #ee_without_off = calculate_worst_energy_efficient(grid._antennas,vazao_total)
        ee_with_off = calculate_energy_efficient(rrhs_used,vazao_total)
        #print ee_without_off
        print 'EE:', ee_with_off
        
        f = open('resumo.csv','a')   # Trying to create a new file or open one
        f.write(str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid._user))+','+str(len(rrhs_used))+','+str(users_no_met)+','+str(ee_with_off)+','+str(se)+'\n')
        #f.write(str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid._user))+','+'EE_WITHOUT_OFF'+','+str(len(rrhs_used))+','+str(users_no_met)+','+str(ee_without_off)+'\n')
        #f.write(str(len(grid.bs_list))+','+str(len(grid.rrh_list))+','+str(len(grid._user))+','+'EE_WITH_OFF'+','+str(len(rrhs_used))+','+str(users_no_met)+','+str(ee_with_off)+'\n')
        f.close()

        #plot_grid( grid )
        #power_consume += ( len( rrhs_used ) * Antenna.ON ) + ( ( len( rrhs ) - len( rrhs_used ) ) * Antenna.OFF )
