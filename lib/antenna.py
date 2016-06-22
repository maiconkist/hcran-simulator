import math
import numpy
import util
import controller
from user import *

class Antenna(object):
    BS_ID       = 1
    RRH_ID      = 2
    RRH_RADIUS  = 50
    BS_RADIUS   = 710
    POWER_BS    = 46
    POWER_RRH   = 23

    ################
    # Peng and MC constants
    B0           = 180
    N0           = -17
    DRN          = 1         
    HRN          = 1         
    DMN          = 450
    HMN          = 1
    Pmax         = 20        
    PMmax        = 43
    PRmax        = 1
    PRC          = 0.1
    PBH          = 0.2
    EFF          = 4
    DR2M         = 125       
    HR2M         = 1 
    NR           = ((((128/1000) *1024) / 2) / 8) * 180
    NER          = ((((64/1000) *1024) / 2) / 8) * 180 
    E_BETA       = 0.01
    E_LAMBDA     = 0.01
    E_UPSILON    = 0.01
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
        # List of connected UEs
        self._ues = []
        self._rb_map = {}

        # Register to the closest BBU
        self._bbu = util.nearest(self, grid.bbus)
        self._bbu.register(self)
        
        #################################
        #Used by peng and monte carlo
        #################################
        self.cnir                       = []
        self.a                          = []
        self.p                          = []
        self.h                          = []
        self.energy_efficient           = [] 
        self.total_power_consumition    = 0 
        self.data_rate                  = 0


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
        if ue not in self._ues and util.dist(ue, self) < self.radius:
            self._ues.append(ue)
            self._bbu.event(controller.UE_CONNECT, self, ue)
            return True

        elif ue in self._ues:
            # already connected, nothing to do
            return True

        else:
            return False

    def disconnect(self, ue):
        """ Called by ue when disconnects

        @param ue UE disconnecting
        """
        if ue in self._ues:
            self._ues.remove(ue)
            self._bbu.event(controller.UE_DISCONNECT, self, ue)
            return True
        return False



    def _update_ue_rb(self):
        """ Check the total RBs required to satisfy UEs demands
        """

        self._rb_map = {}
        for ue in self._ues:
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
                              ", n_ues:" + str(len(self._ues))
            )

            # --
            for ue in self._ues:
                ue.tx_rate = ue.demand
        # NOT IDEAL CASE: we have less RBs than the UEs demand
        #             == available RBs split evenly among UEs
        else:
            # quantity of RBs available
            avail_rb = Antenna.BW_RB_MAP[self._cur_ch_bw]
            # bivide equaly among all UEs
            rb_per_ue = math.floor(avail_rb/len(self._ues))

            # set UE tx_rate based
            for ue in self._ues:
                ue.tx_rate = rb_per_ue * util.snr_to_bit(util.snr(ue, self) )

            self._grid.logger.log("op:antenna_bad_cap, antenna:" +
                              str(self) +
                              ", rb_demand:" + str(total_rb_demand) +
                              ", avail_rb:" + str(Antenna.BW_RB_MAP[self._cur_ch_bw]) +
                              ", per_used:" + str(1.0) +
                              ", n_ues:" + str(len(self._ues))
            )



        # Notify BBU that this antenna requires more bandwidth
        self._ch_bw_required = self.rb_demand_to_ch_bw(total_rb_demand)
        if self._ch_bw_required != self._cur_ch_bw:
            self._bbu.event(controller.ANTENNA_BW_UPDATE, self)


    def __str__(self):
        """
        """
        return str(self.pos)

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
        for n in range(0, len(self._ues)):
            for k in range (0, self.TOTAL_RBS):
                self.data_rate += shannon((self.a[n][k] * Antenna.B0), self.p[n][k], self.noise[n][k])

    def shannon(self, B, S, N):
        #Shannon Calc
        # B is in hertz
        # the signal and noise powers S and N are measured in watts or volts
        return B * math.log(1 + (S/N))

    def obtain_power_consumition(self):
        result = 0
        for n in range(0, len(self._ues)):
            for k in range(0, self.TOTAL_RBS):
                result += (self._a[n][k] * self._p[n][k])           
        self.total_power_consumition = (self.EFF * result) + self.PRC + self.PBH
                                
    def obtain_energy_efficient(self):
        self.obtain_data_rate()
        self.obtain_power_consumition()
        self.energy_efficient = self.data_rate/self.total_power_consumition
        #print numpy.matrix(self.energy_efficient)

    ##########################
    # Peng and MC Calcs
    #########################
    def list_antennas_in_antennas(self, antennas, nAnt):
        for ant in antennas:
            if ant._id != antennas[nAnt]._id:
                antennas[nAnt]._others_ant.append(antennas[nAnt])

            #ant.init_ee(grid.TOTAL_RBS, antennas[nAnt]._others_ant, i)  

    def interference_calc(self, grid):
        for ue in range (0, len(self._ues)):
            for rb in range (0, self.TOTAL_RBS):
                self.noise[ue][rb] = self.noise(self._ues[ue], rb, grid._antennas)
                self.p[ue][rb] = self.calculate_p(ue, rb)
                #self._w[ue][rb]= self.waterfilling_optimal(ue, rb)

    def noise(self, ue, rb, antennas):
        interference = 0
        Gt = 0.1                       #transmission antenna gain
        Gr = 0.1                       #receiver antenna gain
        Wl = (3/19.0)                  #Comprimento de onda considerando uma frequencia de 1.9 GHz
        for ant in antennas:
            if (ue._connected_antenna._id != ant._id and hasattr(ant, '_a') and sum(ant._a[:,rb])>0):
                index = numpy.argmax(ant._a[:,rb])
                R  =  dist(ue, ant)
                interference += ant._a[index,rb] * ant._p[index,rb] * (Gt * Gr * ( Wl / math.pow((4 * math.pi * R), 2)))
                #print "Interference: ", interference
            else:
                interference += path_loss(ue, ant)
                print "Path loss: ", path_loss(ue, ant)

        return interference

    def path_loss(self, ue):
        result = 0
        if (self.type == Antenna.BS_ID):
            result = 31.5 + 40.0 * math.log(dist(ue, self))
        else:
            result = 31.5 + 35.0 * math.log(dist(ue, self))
        return result


    def calculate_p(self, ue, rb):
        #Obtain P in W                                                                                
        #p = self.waterfilling_optimal(n,k) - (1 / self._cnir[n][k])  
        N = 0.000000000001             #ruido
        Pr = N * (math.pow(2,4.5234)-1)#receivedpower 
        Gt = 0.1                       #transmission antenna gain
        Gr = 0.1                       #receiver antenna gain
        Wl = (3/19.0)                  #Comprimento de onda considerando uma frequencia de 1.9 GHz
        R  = dist(self._ues[ue], self) #distance between antennas 
        Ar =  self._cnir[ue, rb]       #interference plus pathloss
        p = (Pr + Ar) / (Gt * Gr * ( Wl / math.pow((4 * math.pi * R), 2)))                                            
        return p