import math
import numpy
import util
import controller
from user import *


DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

class Antenna(object):
    BS_ID       = 1
    RRH_ID      = 2
    RRH_RADIUS  = 50
    BS_RADIUS   = 710
    
    #VARIABLE CONSTANTS
    POWER_BS    = 46
    POWER_RRH   = 23
    TARGET_SINR = 14.5 #[db]
    T_GAIN      = 0                       #transmission antenna gain
    R_GAIN      = 0                       #receptor antenna gain
    WAVELENTH   = (3/19.0)                #Comprimento de onda considerando uma frequencia de 1.9 GHz
    TOTAL_RBS   = 100
    CHANNEL     = 20000000 #Hz
    RB_BIT_CAPACITY = 406.499955591 #bits/0.5 ms with a SINR  18.8

    ################
    # Peng and MC constants
    B0           = 180000
    N0           = -17
    DRN          = 1         
    HRN          = 1         
    DMN          = 450
    HMN          = 1
    Pmax         = 23        
    PMmax        = 46
    PRmax        = 1
    PRC          = 6.8
    PBH          = 3.85
    PMC          = 10
    PMBH         = 3.85
    EFF          = 2
    MEFF         = 4
    DR2M         = 125       
    HR2M         = 1 
    NR           = 5242880/2000 #High Rate Constraint
    NER          = 5242880/2000 #Low Rate Constraint
    #NR           = 1000000/2000 #High Rate Constraint
    #NER          = 1000000/2000 #Low Rate Constraint
    E_BETA       = 0.1
    E_LAMBDA     = 0.1
    E_UPSILON    = 0.1
    D_0          = 1

    # 1.4  channel has 6  RBs in frequency domain
    # 3.0  channel has 15 RBs in frequency domain
    # 5.0  channel has 25 RBs in frequency domain
    # 10.0 channel has 50 RBs in frequency domain
    # 15.0 channel has 75 RBs in frequency domain
    # 20.0 channel has 100 RBs in frequency domain
    # * 2000 for time domain

    BW_RB_MAP = {1.4: 6  * 2000.0,
                 3  : 15 * 2000.0,
                 5  : 25 * 2000.0,
                 10 : 50 * 2000.0,
                 15 : 75 * 2000.0,
                 20 : 100* 2000.0
    }

    def __init__(self, id, type, pos, radius, grid, bw = 1.4):
        self._id = id
        self.type = type
        #BS or RRH
        if type == self.BS_ID:
            self.power = self.POWER_BS
            self._radius = self.BS_RADIUS
        else:
            self.power = self.POWER_RRH
            self._radius = self.RRH_RADIUS
        self.antenna_in_range = []
        self.user_in_range = []
        # List of connected UEs
        self.connected_ues = []

        self.resources = []
        # position tupe
        self._pos = pos
        # antenna coverage radius
        self._radius = radius
        # Grid object
        self._grid = grid
        # Channel bw (none in the start)
        self._cur_ch_bw =bw
        self._cur_rb_cap = Antenna.BW_RB_MAP[bw]
        # Channel BW required
        self._ch_bw_required = None
        
        self._rb_map = {}

        # Register to the closest BBU
        self._bbu = util.nearest(self, grid.bbus)
        self._bbu.register(self)
        
        #################################
        #Used by peng and monte carlo
        #################################
        self.i                          = None
        self.a                          = None
        self.p                          = None
        self.h                          = None
        self.energy_efficient           = 0 
        self.power_consumition          = 0 
        self.data_rate                  = 0
        self.user_data_rate             = None
        self.users_meet                 = 0
        self.p_energy_efficient        = []

    @property
    def x( self ):
        return self.pos[ 0 ]
    
    @property
    def y( self ):
        return self.pos[ 1 ]

    @property
    def pos(self):
        """
        """
        return self._pos

    @pos.setter
    def pos(self, pos):
        """
        """
        print("Cannot set pos for Antenna object")

    @property
    def radius(self):
        """
        """
        return self._radius

    @property
    def bbu(self):
        """
        """
        return self._bbu

    @property
    def demand(self):
        return self._ch_bw_required

    @property
    def ch_bw(self):
        return self._cur_ch_bw

    @property
    def ch_bw_demand(self):
	    return self._ch_bw_required

    @ch_bw.setter
    def ch_bw(self, new_bw):
        self._cur_ch_bw = new_bw
        self._cur_rb_cap = Antenna.BW_RB_MAP[new_bw]

    def connect(self, ue):
        """ Called by ue when user connects

        @param ue UE connecting
        """
        if ue not in self.connected_ues and util.dist(ue, self) < self.radius:
            self.connected_ues.append(ue)
            self._bbu.event(controller.UE_CONNECT, self, ue)
            return True

        elif ue in self.connected_ues:
            # already connected, nothing to do
            return True

        else:
            return False

    def disconnect(self, ue):
        """ Called by ue when disconnects

        @param ue UE disconnecting
        """
        if ue in self.connected_ues:
            self.connected_ues.remove(ue)
            self._bbu.event(controller.UE_DISCONNECT, self, ue)
            return True
        return False



    def _update_ue_rb(self):
        """ Check the total RBs required to satisfy UEs demands
        """

        self._rb_map = {}
        for ue in self.connected_ues:
            # calculate the total RBs for each UE
            # mult per 84 because: 84 ofdm symbons in a RB
            self._rb_map[ue] = ue.demand / (util.snr_to_bit(util.snr(ue, self, 0)) * 84.0)

    def rb_demand_to_ch_bw(self, rb_demand):
        """ Minimum channel BW based on RB demand

        @param rb_demand Total RB demand
        """

        # TODO: Inverse the BW_RB_MAP map instead of if..else block
        if rb_demand <= (6 * 2000):
            return 1.4
        elif rb_demand <= (15 * 2000):
            return 3.0
        elif rb_demand <= (25 * 2000):
            return 5.0
        elif rb_demand <= (50 * 2000):
            return 10.0
        elif rb_demand <= (75 * 2000):
            return 15.0
        elif rb_demand <= (100 * 2000):
            return 20.0
        else:
            self._grid.logger.log("op:antenna_impossible_cap, antenna:" +
                                  str(self) +
                                  ", rb_demand:" + str(rb_demand))
            return 20.00

    def update(self):
        """
        """

        # update the RBs used by each ue
        self._update_ue_rb()

        # ---
        total_rb_demand = sum(self._rb_map.values())

        # IDEAL CASE: we have more RBs than the UEs demand
        #             == all UEs are satified with their demand
        if total_rb_demand < Antenna.BW_RB_MAP[self._cur_ch_bw]:
            self._grid.logger.log("op:antenna_good_cap, antenna:" +
                              str(self) +
                              ", rb_demand:" + str(total_rb_demand) +
                              ", avail_rb:" + str(Antenna.BW_RB_MAP[self._cur_ch_bw]) +
                              ", per_used:" +
                               str(total_rb_demand/Antenna.BW_RB_MAP[self._cur_ch_bw]) +
                              ", nconnected_ues:" + str(len(self.connected_ues))
            )

            # --
            for ue in self.connected_ues:
                ue.tx_rate = ue.demand
        # NOT IDEAL CASE: we have less RBs than the UEs demand
        #             == available RBs split evenly among UEs
        else:
            # quantity of RBs available
            avail_rb = Antenna.BW_RB_MAP[self._cur_ch_bw]
            # bivide equaly among all UEs
            rb_per_ue = math.floor(avail_rb/len(self.connected_ues))

            # set UE tx_rate based
            for ue in self.connected_ues:
                ue.tx_rate = rb_per_ue * util.snr_to_bit(util.snr(ue, self) )

            self._grid.logger.log("op:antenna_bad_cap, antenna:" +
                              str(self) +
                              ", rb_demand:" + str(total_rb_demand) +
                              ", avail_rb:" + str(Antenna.BW_RB_MAP[self._cur_ch_bw]) +
                              ", per_used:" + str(1.0) +
                              ", nconnected_ues:" + str(len(self.connected_ues))
            )



        # Notify BBU that this antenna requires more bandwidth
        self._ch_bw_required = self.rb_demand_to_ch_bw(total_rb_demand)
        if self._ch_bw_required != self._cur_ch_bw:
            self._bbu.event(controller.ANTENNA_BW_UPDATE, self)


    def __str__(self):
        """
        """
        return str(self.pos)

    def toString(self):
        numpy.set_printoptions(precision=2)
        if (self.type == Antenna.BS_ID):
            debug_printf("\n\n----- BS -----")
        else: 
            debug_printf("\n\n----- RRH -----")
        debug_printf("Users (Meet/Total) = "+ str(self.users_meet) +"/"+str(len(self.connected_ues)))
        debug_printf("Resource Block (Used/Total) = " + str(self.a.sum()) +"/"+ str(self.TOTAL_RBS))
        debug_printf("Data Rate = " + str(self.data_rate))
        debug_printf("Power Consumition = " + str(self.power_consumition))
        debug_printf("Energy Efficient = " + str(self.energy_efficient))
        debug_printf("Alloc = \n" + str(numpy.matrix(self.a)))
        debug_printf("Power = \n" + str(numpy.matrix(self.p)))
        debug_printf("Noise = \n" + str(numpy.matrix(self.i)))


    def add_antenna_in_range( self, antenna ):
        if not antenna in self.antenna_in_range:
            self.antenna_in_range.append( antenna )
            
    def get_neighbor_antenna( self ):
        return self.antenna_in_range
            
    def add_user_in_range( self, user ):
        if not user in self.user_in_range:
            self.user_in_range.append( user )
            
    def get_users_in_coverage( self ):
        return self.user_in_range

    ##########################
    # Calculo da EE
    #########################
    def obtain_data_rate(self):
        #Shannon Calc
        self.data_rate = 0
        self.users_meet = 0
        if self.connected_ues != None:
            self.user_data_rate = numpy.zeros(shape=(len(self.connected_ues)))
            for n in range(0, len(self.connected_ues)):
                for k in range (0, self.TOTAL_RBS):
                    data_bits = (util.shannon((self.a[n][k] * Antenna.B0), util.sinr(self.p[n][k], self.i[n][k], util.noise())))/2000#Qnt de bits em 0,5 ms
                    self.data_rate += data_bits
                    self.user_data_rate[n] += data_bits
                if self.connected_ues[n]._type == User.HIGH_RATE_USER:
                    if self.user_data_rate[n] >= Antenna.NR:
                        self.users_meet += 1
                else:
                    if self.user_data_rate[n] >= Antenna.NER:
                        self.users_meet += 1

    
    def obtain_power_consumition(self):
        self.power_consumition = 0
        result = 0
        for n in range(0, len(self.connected_ues)):
            for k in range(0, self.TOTAL_RBS):
                result += util.dBm_to_watts(self.a[n][k] * self.p[n][k])   
        if (self.type == Antenna.BS_ID):
            self.power_consumition = (self.MEFF * result) + self.PMC + self.PMBH
        else:
            self.power_consumition = (self.EFF * result) + self.PMC + self.PMBH
        #debug_printf('Consumo atual:' + self.power_consumition)
        #if self.power_consumition > 14692223.0241:
            #debug_printf("Data Rate = \n" + str(self.data_rate))
            #debug_printf("Power Consumition = \n" + str(self.power_consumition))
            #debug_printf("Energy Efficient = \n" + str(self.energy_efficient))
            #debug_printf("Alloc = \n" + str(numpy.matrix(self.a)))
            #debug_printf("Power = \n" + str(numpy.matrix(self.p)))
            #debug_printf("Noise = \n" + str(numpy.matrix(self.i)))
            #wait()
                                
    def obtain_energy_efficient(self):
        self.obtain_data_rate()
        self.obtain_power_consumition()
        self.energy_efficient = self.data_rate/self.CHANNEL/self.power_consumition
        #debug_printf("Data Rate = \n" + str(self.data_rate))
        #debug_printf("Power Consumition = \n" + str(self.power_consumition))
        #debug_printf("Energy Efficient = \n" + str(self.energy_efficient))
        #debug_printf(numpy.matrix(self.energy_efficient))

    ##########################
    # Peng and MC Calcs
    #########################
    def list_antennas_in_antennas(self, antennas, nAnt):
        for ant in antennas:
            if ant._id != antennas[nAnt]._id:
                antennas[nAnt]._others_ant.append(antennas[nAnt])

            #ant.init_ee(grid.TOTAL_RBS, antennas[nAnt]._others_ant, i)  

    def obtain_interference_and_power(self, grid):
        for ue in range (0, len(self.connected_ues)):
            for rb in range (0, self.TOTAL_RBS):
                self.i[ue][rb] = self.interference(self.connected_ues[ue], rb, grid._antennas) #dBm
                R  =  util.dist(self.connected_ues[ue], self)
                self.p[ue][rb] = self.p_friis(self.i[ue][rb], self.noise(), self.T_GAIN, self.R_GAIN, R, self.WAVELENTH) #dBm

    def demand_in_rbs(self, ue):
        demanda_bits = 0
        if ue._type == User.HIGH_RATE_USER:
            demanda_bits = self.NR
        else:
            demanda_bits = self.NER

        return int(math.ceil(demanda_bits/self.RB_BIT_CAPACITY))

