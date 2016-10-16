import math
import numpy
import util
import controller
from user import *
import threeGPP

class Antenna(object):
    BS_ID       = 1
    RRH_ID      = 2
    
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
        self.height = 25
        self.frequency = 2.0

        #BS or RRH
        if type == self.BS_ID:
            self.power = threeGPP.POWER_BS
            self._radius = threeGPP.BS_RADIUS
            self.height = 25
        else:
            self.power = threeGPP.POWER_RRH
            self._radius = threeGPP.RRH_RADIUS
            self.height = 10
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
        
        self.i                         = None
        self.a                         = None
        self.p                         = None
        self.energy_efficient          = None 
        self.consumition               = None 
        self.datarate                  = None
        self.user_datarate             = None
        self.fairness                  = None
        self.meet_users                = None
        self.datarate_constraint       = None
        self.backup_i                  = None
        self.backup_a                  = None
        self.backup_p                  = None
        self.backup_energy_efficient   = None 
        self.backup_consumition        = None 
        self.backup_datarate           = None
        self.backup_user_datarate      = None
        self.backup_fairness           = None
        self.backup_meet_users         = None
        self.history_i                 = None
        self.history_a                 = None
        self.history_p                 = None
        self.history_energy_efficient  = None
        self.history_consumition       = None
        self.history_datarate          = None
        self.history_user_datarate     = None
        self.history_fairness          = None
        self.history_meet_users        = None

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

    def used_rbs(self, particle = 0):
        return self.a[particle].sum()

    def toString(self, particle = 0):
        numpy.set_printoptions(precision=2)
        if (self.type == Antenna.BS_ID):
            util.debug_printf("\n\n----- BS -----")
        else: 
            util.debug_printf("\n\n----- RRH -----")
        util.debug_printf("Users (Meet/Total) = "+ str(self.meet_users[particle]) +"/"+str(len(self.connected_ues)))
        util.debug_printf("Resource Block (Used/Total) = " + str(self.a[particle].sum()) +"/"+ str(threeGPP.TOTAL_RBS))
        util.debug_printf("Data Rate = " + str(self.datarate[particle]))
        util.debug_printf("Power Consumition = " + str(self.consumition[particle]))
        util.debug_printf("Energy Efficient = " + str(self.energy_efficient[particle]))
        util.debug_printf("Alloc = \n" + str(numpy.matrix(self.a[particle])))
        util.debug_printf("Power = \n" + str(numpy.matrix(self.p[particle])))
        util.debug_printf("Noise = \n" + str(numpy.matrix(self.i[particle])))


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

    def backup_state(self, particle = 0):
        self.backup_i[particle]                = self.i[particle].copy()
        self.backup_a[particle]                = self.a[particle].copy()
        self.backup_p[particle]                = self.p[particle].copy()
        self.backup_energy_efficient[particle] = self.energy_efficient[particle].copy() 
        self.backup_consumition[particle]      = self.consumition[particle].copy() 
        self.backup_datarate[particle]         = self.datarate[particle].copy()
        self.backup_user_datarate[particle]    = self.user_datarate[particle].copy()
        self.backup_fairness[particle]         = self.fairness[particle].copy()
        self.backup_meet_users[particle]       = self.meet_users[particle].copy()

    def restore_state(self, particle = 0):
        self.i[particle]                = self.backup_i[particle].copy()
        self.a[particle]                = self.backup_a[particle].copy()
        self.p[particle]                = self.backup_p[particle].copy()
        self.energy_efficient[particle] = self.backup_energy_efficient[particle].copy() 
        self.consumition[particle]      = self.backup_consumition[particle].copy() 
        self.datarate[particle]         = self.backup_datarate[particle].copy()
        self.user_datarate[particle]    = self.backup_user_datarate[particle].copy()
        self.fairness[particle]         = self.backup_fairness[particle].copy()
        self.meet_users[particle]       = self.backup_meet_users[particle].copy()


    def backup_best_particle(self, particle, history):
        self.history_i[history]                = self.i[particle].copy()
        self.history_a[history]                = self.a[particle].copy()
        self.history_p[history]                = self.p[particle].copy()
        self.history_energy_efficient[history] = self.energy_efficient[particle].copy() 
        self.history_consumition[history]      = self.consumition[particle].copy() 
        self.history_datarate[history]         = self.datarate[particle].copy()
        self.history_user_datarate[history]    = self.user_datarate[particle].copy()
        self.history_fairness[history]         = self.fairness[particle].copy()
        self.history_meet_users[history]       = self.meet_users[particle].copy()

    def restore_best_particle(self, particle, history):
        self.i[particle]                = self.history_i[history].copy()
        self.a[particle]                = self.history_a[history].copy()
        self.p[particle]                = self.history_p[history].copy()
        self.energy_efficient[particle] = self.history_energy_efficient[history].copy() 
        self.consumition[particle]      = self.history_consumition[history].copy() 
        self.datarate[particle]         = self.history_datarate[history].copy()
        self.user_datarate[particle]    = self.history_user_datarate[history].copy()
        self.fairness[particle]         = self.history_fairness[history].copy()
        self.meet_users[particle]       = self.history_meet_users[history].copy()

    def rest_power(self, particle = 0):
        psum = 0.0
        for rb in range(0, threeGPP.TOTAL_RBS):
            ue = numpy.argmax(self.a[particle,:,rb])
            if self.a[particle,ue,rb] > 0 and math.isnan(self.p[particle,ue,rb]) == False:
                #print "psum", self.p[particle,ue,rb]
                psum += util.dbm_to_mw(self.p[particle,ue,rb])

        if (self.type == self.BS_ID):
            #print "BS", util.dbm_to_mw(threeGPP.POWER_BS), psum 
            rest = util.dbm_to_mw(threeGPP.POWER_BS) - psum
        else:
            #print "RRH", util.dbm_to_mw(threeGPP.POWER_RRH), psum
            rest = util.dbm_to_mw(threeGPP.POWER_RRH) - psum

        #print "rest", rest
        if (rest > 0):
            #if (self.type != self.BS_ID):
            #    print "rest", rest, util.mw_to_dbm(rest)
            return util.mw_to_dbm(rest)
        else:
            #if (self.type != self.BS_ID):
            #    print "rest", None
            return None

    def fixed_power(self):
        power = -1
        if (self.type == self.BS_ID):
            power = util.dbm_to_mw(threeGPP.POWER_BS)/threeGPP.TOTAL_RBS
        else:
            power = util.dbm_to_mw(threeGPP.POWER_RRH)/threeGPP.TOTAL_RBS


        if (power > 0):
            return util.mw_to_dbm(power)
        else:
            return None

