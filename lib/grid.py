import random
import scipy.spatial
from util import *
import re
import time
import math
from antenna import Antenna
import Calculations as calc
import threeGPP

class Log():
    """
    """
    logs = []

    mapper = {"op:connection": 0,
              "op:disconnection": 0,
              "op:bbu_change": 0,
              "op:antenna_bw_update": 0,
              "op:antenna_impossible_cap":0,
              "good_cap":0,
              "good_cap_sum":0,
              "bad_cap":0,
              "bad_cap_sum":0,
              "bad_connection":0,
              "bad_connection_sum":0,
              }

    @staticmethod
    def clear():
        Log.mapper = {"op:connection": 0,
              "op:disconnection": 0,
              "op:bbu_change": 0,
              "op:antenna_bw_update": 0,
              "op:antenna_impossible_cap":0,
              "good_cap":0,
              "good_cap_sum":0,
              "bad_cap":0,
              "bad_cap_sum":0,
              "bad_connection":0,
              "bad_connection_sum":0,
        }
        Log.logs = []

    @staticmethod
    def log(m):

        if 'op:connection' in m:
            Log.mapper['op:connection'] += 1
        elif 'op:disconnection' in m:
            Log.mapper['op:disconnection'] += 1
        elif 'op:bbu_change' in m:
            Log.mapper['op:bbu_change'] += 1
        elif 'op:antenna_bw_update' in m:
            Log.mapper['op:antenna_bw_update'] += 1
        elif 'op:antenna_impossible_cap' in m:
            Log.mapper['op:antenna_impossible_cap'] += 1
        elif 'op:antenna_good_cap' in m:
            Log.mapper['good_cap'] += 1

            regex = re.compile("per_used:([0-9]*\.[0-9]*)")
            Log.mapper['good_cap_sum'] += float( regex.findall(m)[0] )
        elif 'op:antenna_bad_cap' in m:
            Log.mapper['bad_cap'] += 1

            regex = re.compile("per_used:([0-9]*\.[0-9]*)")
            Log.mapper['bad_cap_sum'] += float( regex.findall(m)[0] )
        elif 'op:bad_connection' in m:
            Log.mapper['bad_connection'] += 1

            regex = re.compile("avg_rate:([0-9]*\.[0-9]*)")
            Log.mapper['bad_connection_sum'] += float( regex.findall(m)[0] )

        Log.logs.append(m)

class Grid(object):
    
    def __init__(self, size=(1000, 1000)):
        """
        """
        self._size = size
        self._user = []
        self._antennas = []
        self.bs_list = []
        self.rrh_list = []
        self._bbus = []
        self._controllers = []
        self._clusters = []
        self._antenna_tree = None
        self._initialized = 0
        self._matrix_resources = None #Matrix [Antenna, RB] = id user
        self._bandwidth = 20

        self.energy_efficient          = None 
        self.consumition               = None 
        self.datarate                  = None
        self.fairness                  = None
        self.meet_users                = None
        self.history_weighted_efficient= None


    def set_bandwidth(self, band):
        """
        """
        self._bandwidth = band
        self.TOTAL_RBS = bandwidth_to_rb(band)            
        self.TOTAL_RBS_RRH = int(self.TOTAL_RBS * 0.2)
        self.TOTAL_RBS_BS = int(self.TOTAL_RBS * 0.8)
        if self.TOTAL_RBS_RRH + self.TOTAL_RBS_BS < self.TOTAL_RBS:
            self.TOTAL_RBS_RRH +=1

    @property
    def matrix_resources(self):
        """
        """
        if self._matrix_resources == None:
            self._matrix_resources = [ [ None for i in range( self.TOTAL_RBS ) ] for j in range( len( self._antennas ) ) ]

        return self._matrix_resources

    def add_user(self, user):
        """
        """
        self._user.append(user)

    def remove_users(self):
        """
        """
        #print self._user
        self._user = []
        #print self._user

    def add_antenna(self, antenna):
        """
        """
        if antenna.type == antenna.BS_ID:
            self.bs_list.append( antenna )
        elif antenna.type == antenna.RRH_ID:
            self.rrh_list.append( antenna )
        self._antennas.append(antenna)

    def add_bbu(self, bbu):
        """
        """
        self._bbus.append(bbu)

    def add_controller(self, cntrl):
        """
        """
        self._controllers.append(cntrl)

    def add_cluster(self, cluster):
        """
        """
        self._clusters.append(cluster)

    @property
    def bbus(self):
        """
        """
        return self._bbus

    @property
    def users(self):
        """
        """
        return self._user

    @property
    def antennas(self):
        """
        """
        return self._antennas
    
    @property
    def clusters(self):
        """
        """
        return self._clusters

    @property
    def size(self):
        """
        """
        return self._size

    @property
    def logger(self):
        """
        """
        return Log()

    def random_pos(self):
        """
        """
        x = random.randrange(0, self.size[0])
        y = random.randrange(0, self.size[1])
        return [x, y]

    @property
    def antenna_tree(self):
        """
        """
        return self._antenna_tree

    def init(self):
        """
        """
        if self._antenna_tree is None:
            self._antenna_tree = scipy.spatial.KDTree(
                [a.pos for a in self._antennas]
            )

    def step(self, time):
        """
        """
        self.init()

        # move for 1 second (ue must perform operations)
        for ue in self._user:
            ue.move(time)

        # update ue (after performing movements )
        for ue in self._user:
            ue.update()

        # update antennas
        for antenna in self._antennas:
            antenna.update()

        # update bbus
        for bbu in self._bbus:
            bbu.update()

        # update controllers
        for cntrl in self._controllers:
            cntrl.update()


    def write_to_resume(self, solucao, repeticao, iteracao, init, particle = 0):
        calc.griddatarate(self, particle)
        if particle < 0:
            particle = 0
        calc.gridconsumption(self, particle)
        calc.gridefficiency(self, particle)
        calc.gridfairness(self, particle)

        isum = 0
        asum = 0
        for antenna in self.antennas:
            for ue in range (0, len(antenna.connected_ues)):
                for rb in range(0, threeGPP.TOTAL_RBS):
                    i = antenna.a[particle, ue, rb] * antenna.i[particle, ue, rb]
                    if math.isnan(i) == False:
                        isum += dbm_to_mw(i)
            asum += numpy.sum(antenna.a[particle])


        #print "Datarate p/ rbs", asum/self.datarate[particle]*2000
        print iteracao, "-", solucao, 'TotalRbs:', str(threeGPP.TOTAL_RBS*len(self.antennas)), "UsedRBS:", str(asum), "IMean:", str(mw_to_dbm(isum)/asum), "MU:", str(self.meet_users[particle]), "Fairness:", str(self.fairness[particle])

        f = open('resumo.csv','a')
        f.write(solucao+','+solucao+'['+str(len(self.bs_list))+'-'+str(len(self.rrh_list))+'-'+str(len(self.users))+'],'+str(len(self.bs_list))+','+str(len(self.rrh_list))+','+str(len(self.users))+','+str(repeticao)+','+str(iteracao)+','+str(self.datarate[particle])+','+str(self.consumition[particle])+','+str(self.energy_efficient[particle])+','+str(self.meet_users[particle])+','+str(self.fairness[particle])+','+str(time.time()-init)+'\n')
        f.close()

    def backup_best_particles(self, weighted_efficient, history_legth):
        for history in range(0, history_legth):
            particle = numpy.argmax(weighted_efficient[:])
            self.history_weighted_efficient[history] = weighted_efficient[particle]
            weighted_efficient[particle] = -999999999999999999999999
            for antenna in self.antennas: 
                antenna.backup_best_particle(particle, history)
                

    def restore_best_particles(self, weighted_efficient, history_legth):
        for history in range(0, history_legth):
            particle = numpy.argmin(weighted_efficient[:])
            if (weighted_efficient[particle] < self.history_weighted_efficient[history]):
                weighted_efficient[particle] = 999999999999999999999999
                for antenna in self.antennas: 
                    antenna.restore_best_particle(particle, history)