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
        #Used by peng only
        #################################
        self._cnir  = []
        self._a     = []
        self._p     = []
        self._h     = []
        self._K     = 0 
        
        self._b0         = 180
        self._n0         = -17
        self._drn        = 1         #Calculado na funcao
        self._hrn        = 1         #tem no base conf Utils tem o calcula da distancia entre usuario e antena
        self._dmn        = 450
        self._hmn        = 1
        self._p_max      = 20        #potencia maxima 20 ou 30
        self._pm_max     = 43
        self.pRmax       = 1
        self.Temp        = 0.00
        self._prc        = 0.1
        self._pbh        = 0.2
        self._eff        = 4
        self._dr2m       = 125       #calcular
        self._hr2m       = 1 

        self._nr         = 600
        self._ner        = 400

        self._epsilon_beta       = 0.1
        self._epsilon_lambda     = 0.1
        self._epsilon_upsilon    = 0.1

        self._delta_0 = 1

        self._others_ant = list()
        self._l = 0
        self._total_power_consumition = 0
        self._energy_efficient = list()

        self.dkr2m = 125
        self.pHmax = 41

        self.M = 10000
        self.N = 0
        self.K = 10                 #RBS

        self.C = numpy.zeros(shape=(self.M))
        self.rol = numpy.zeros(shape=(self.M))
        self.P = numpy.zeros(shape=(self.M))
        self.Bn = numpy.zeros(shape=(self.M))
        self.Bm = numpy.zeros(shape=(self.M))
        self.L = numpy.zeros(shape=(self.M))
        self.V = numpy.zeros(shape=(self.M))
        self.EE = numpy.zeros(shape=(self.M))
        self.a = numpy.zeros(shape=(self.M,self.N,self.K))
        self.aAnt = numpy.zeros(shape=(self.M,self.N,self.K))
        self.p = numpy.zeros(shape=(self.M,self.N,self.K))
        self.i = numpy.zeros(shape=(self.M,self.N,self.K))

        self.s0 = 1

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

    ###############################
    # Peng 
    ###############################
    def init_peng(self, n_rbs, others_ants, i):
        if len(self._ues) == 0:
            return

        self._K = n_rbs
        self._others_ant = others_ants
        self._cnir = numpy.zeros((len(self._ues), n_rbs))
        self._a = numpy.zeros((len(self._ues), n_rbs))
        self._p = numpy.zeros((len(self._ues), n_rbs))
        self._h = numpy.zeros((len(self._ues), n_rbs))
        self._w = numpy.zeros((len(self._ues), n_rbs))
        self._sub_bn = numpy.zeros((len(self._ues),1))
        self._sub_lambda_k = numpy.zeros((self._K,1))
       
        self._data_rate               = 0    #(2) C
        self._total_power_consumition = 0    #(5) P
        self._l                       = 0
        self._energy_efficient        = [0] * i

        self._pm = self._pm_max / len(self._ues)
        self._betan = numpy.zeros((len(self._ues), 2))

        self._lambdak = numpy.zeros((self._K, 2))

        for k in range(0, self._K):
            for l in range(0,2):
                self._lambdak[k][l] = 1

        for n in range(0, len(self._ues)):
            for l in range(0,2):
                self._betan[n][l] = 1

        self._upsilonl = [1, 1]

    ###################
    # Update Matrices #
    ###################
    def update_matrix(self):
        for n in range (0, len(self._ues)):
            for k in range (0, self._K):
                self._cnir[n][k] = util.peng_power_interfering(self._ues[n], k, self._others_ant) / (self._b0 * self._n0)
                self._w[n][k] = self.waterfilling_optimal(n, k)
                hp1 = self._cnir[n][k] * self._w[n][k]
                hp2 = (1 - (self._cnir[n][k] * self._w[n][k]))

                if hp1 < 1:
                    hp1 = 1

                if hp2 < 1:
                    hp2 = 1

                self._h[n][k] = ((1 + self._betan[n][0]) * math.log(hp1)) -(((1
                    + self._betan[n][0]) / math.log(2)) * hp2)
      
        
        self.calculate_a_matrix()

    ######################
    # A (n, k)
    #####################
    def calculate_a_matrix(self):
        nn = 0
        for k in range(0, self._K):
            n_max = -9999
            for n in range(0, len(self._ues)):
                if n_max < self._h[n][k]:
                    nn = n
                    n_max = self._h[n][k]

            self._a[nn][k] = 1
            self._p[nn][k] = self.calculate_p_matrix_element(nn, k)

    ######################
    # P (n, k)
    #####################
    def calculate_p_matrix_element(self, n, k):
        if self._cnir[n][k] < 1:
            h1 = 0
        else:
            h1 = (1 - 1 / self._cnir[n][k])

        result = self._w[n][k] - h1 
       
        if result < 0:
            result = 0
        
        return result

    ###########
    # W(n,K)
    ###########
    def waterfilling_optimal(self, n, k):
        p1 = (self._b0 * (1 + self._betan[n][0])) 
        p2 = math.log((self._energy_efficient[self._l] * self._eff) + (self._lambdak[k][0]
                * self._dr2m * self._hr2m) + self._upsilonl[0])
        return p1 / p2

    def mt_waterfilling_optimal(self, n, k, ee):
        p1 = (self._b0 * (1 + self._betan[n][0])) 
        p2 = math.log((ee * self._eff) + (self._lambdak[k][0] * self._dr2m * self._hr2m) + self._upsilonl[0])
        return p1 / p2



    ###########################
    # Subgradient calculations
    ###########################
    def calculate_data_rate_n(self, n):
        result = 0
        for k in range(0, self._K):
            log = (self._cnir[n][k]* self._p[n][k])
            if log <= 0:
                log = 1
            result += (self._a[n][k] * self._b0 * math.log(1+math.log(log)))
        return result

    def calculate_subgradient_beta(self, n):
        result = 0
        c = self.calculate_data_rate_n(n)
        if ((n > 0) and (n < len(self._ues))):
            result = c - self._nr
        else:
            result = c - self._ner
        return result            

    def calculate_subgradient_lambda(self, k):
        result = 0
        soma = 0
        if (len(self._ues) > 0):
            for n in range (0, len(self._ues)):
                soma += self._a[n][k] * self._p[n][k] * self._dr2m * self._hr2m
            result = self._delta_0 - soma
        return result

    def calculate_subgradient_upsilon(self):
        soma = 0
        for n in range(0, len(self._ues)):
            for k in range(0, self._K):
                soma += self._a[n][k] * self._p[n][k]
        return self._pm - soma

    def calculate_beta_n_l1(self, n):
        result = self._betan[n][0] - (self._epsilon_beta * self._sub_bn[n])
        if result > 0:
            return result
        else:
            return 1

    def calculate_lamdak_l1(self,k):
        result = self._lambdak[k][0] - (self._epsilon_lambda * self._sub_lambda_k[k])
        if result > 0:
            return result
        else:
            return 1

    def calculate_upsilon_l1(self):
        result = self._upsilonl[0] - (self._epsilon_upsilon * self._sub_upsilon)
        if result > 0:
            return result
        else:
            return 1

    ####################################
    # update multiplicadores
    ####################################
    def update_l(self):
        for n in range(0,len(self._ues)):
            self._sub_bn[n] = self.calculate_subgradient_beta(n)
            self._betan[n][1] = self.calculate_beta_n_l1(n)

        for k in range(0, self._K):
            self._sub_lambda_k[k] = self.calculate_subgradient_lambda(k)
            self._lambdak[k][1] = self.calculate_lamdak_l1(k)

        self._sub_upsilon = self.calculate_subgradient_upsilon()
        self._upsilonl[1] = self.calculate_upsilon_l1()

    def swap_l(self):
        for n in range(0, len(self._ues)):
            self._betan[n][0] = self._betan[n][1]
    
        for k in range(0, self._K):
            self._lambdak[k][0] = self._lambdak[k][1]
        
        self._upsilonl[0] = self._upsilonl[1]

    def max_dif(self):
        max_beta = -9999
        max_lambdak = -9999
        for n in range(0, len(self._ues)):
            beta = (self._betan[n][1] - self._betan[n][0]) / self._betan[n][0]
            if beta > max_beta:
                max_beta = beta

        for k in range(0, self._K):
            lambdak = (self._lambdak[k][1] - self._lambdak[k][0]) / self._lambdak[k][0]
            if lambdak > max_lambdak:
                max_lambdak = lambdak
    
        max_upsilonl = (self._upsilonl[1] - self._upsilonl[0]) / self._upsilonl[0]

        return max(max_beta, max_lambdak, max_upsilonl)

    ##########################
    # Calculo do EE
    #########################
    def data_rate(self):
        result = 0
        for n in range(0, len(self._ues)): 
            result += self.data_rate_n(n) 

        self._data_rate = result

    def data_rate_n(self, n):
        result = 0
        for k in range(0, self._K):
            log = 1+(self._cnir[n][k]* self._p[n][k])
            if log < 0:
                log = 1
            result += (self._a[n][k] * self._b0 * math.log(log))

        return result

    #P (3)
    def power_consumition(self):
        result = 0
        for n in range(0, len(self._ues)):
            for k in range(0, self._K):
                result += (self._a[n][k] * self._p[n][k])           

            self._total_power_consumition = (self._eff * result) + self._prc + self._pbh
                                
    #Y (6)
    def energy_efficient(self):
        #print "total power: " + str(self._total_power_consumition)
        #print "data rate: "  + str(self._data_rate)
        r = self._total_power_consumition
        if self._total_power_consumition == 0:
            r = 1
        self._energy_efficient.append(self._data_rate/r)

    def roleta(EE, nJogadas):
        nArea = len(EE)
        area = numpy.zeros(shape=(nArea))
        result = numpy.zeros(shape=(nJogadas))
        total = sum(EE)
        ant = 0;
        for q in range(0, len(EE)):
            area[q] = ant + EE[q]
            ant = area[q]

        print EE
        print area

        for q in range(0, nJogadas):
            rd = random.uniform(0.0, total)
            for t in range(0, len(area)):
                if rd < area[t]:
                    result[q] = t
                    break

        return result


    ###############################################
    # Roleta viciada
    ##############################################
    def init_monte_carlo(self):
        self.N = len(self._ues)
        self.C = numpy.zeros(shape=(self.M))
        self.rol = numpy.zeros(shape=(self.M))
        self.P = numpy.zeros(shape=(self.M))
        self.Bn = numpy.zeros(shape=(self.M))
        self.Bm = numpy.zeros(shape=(self.M))
        self.L = numpy.zeros(shape=(self.M))
        self.V = numpy.zeros(shape=(self.M))
        self.EE = numpy.zeros(shape=(self.M))
        self.a = numpy.zeros(shape=(self.M,self.N,self.K))
        self.aAnt = numpy.zeros(shape=(self.M,self.N,self.K))
        self.p = numpy.zeros(shape=(self.M,self.N,self.K))
        self.i = numpy.zeros(shape=(self.M,self.N,self.K))
        self.betan = numpy.zeros(shape=(self.M,len(self._ues)))
        self.sub_bn = numpy.zeros(shape=(self.M,self.N))
        self.sub_lambda_k = numpy.zeros(shape=(self.M,self.K))
        self.lambdak = numpy.zeros(shape=(self.M, self.M))
        self.upsilonl = numpy.zeros(shape=(self.M))
        self.sub_upsilon = numpy.zeros(shape=(self.M))

    def clean(self):
        self.C = numpy.zeros(shape=(self.M))
        self.P = numpy.zeros(shape=(self.M))
        self.Bn = numpy.zeros(shape=(self.M))
        self.Bm = numpy.zeros(shape=(self.M))
        self.L = numpy.zeros(shape=(self.M))
        self.V = numpy.zeros(shape=(self.M))
        self.EE = numpy.zeros(shape=(self.M))
        self.a = numpy.zeros(shape=(self.M,self.N,self.K))
        self.p = numpy.zeros(shape=(self.M,self.N,self.K))
        self.i = numpy.zeros(shape=(self.M,self.N,self.K))

    def doPartialCalc(self,z,r,y):
        #Calculos
        self.C[z] += (self.a[z,r,y] * self._b0 * math.log(1+(self.i[z,r,y] * self.p[z,r,y])))
        self.P[z] += (self.a[z,r,y] * self.p[z,r,y])
       
        #if usuario de alta demanda:
        if self._ues[r]._type == User.HIGH_RATE_USER:
            self.Bn[z] += (self.a[z,r,y] * self._b0 * math.log(1+(self.i[z,r,y] * self.p[z,r,y])) - self._nr)
        else: 
        #if usuario de baixa demanda:
            self.Bm[z] += (self.a[z,r,y] * self._b0 * math.log(1+(self.i[z,r,y] * self.p[z,r,y])) - self._ner)

        self.L[z] += (self.a[z,r,y] * self.p[z,r,y] * self.dkr2m * self.pHmax)
        self.V[z] += self.a[z,r,y] * self.p[z,r,y]

    def doFinalCalc(self,z, r):
        self.P[z] = self._eff * self.P[z] + self._prc + self._pbh
        self.L[z] = self.s0 - self.L[z]
        
        if self.type == Antenna.BS_ID:
            self.V[z] = self.pHmax - self.V[z]
        else:        
            self.V[z] = self.pRmax - self.V[z]
        #aux = (self.betan[z][r]*self.Bn[z]) + (self.betan[z][r]*self.Bm[z]) + (lambdak[z][r]*self.L[z]) + (self.upsilonl[z]*self.V[z])
        aux = (self.betan[z][r]*self.Bn[z]) + (self.upsilonl[z]*self.V[z])
        print 'capacidade: ', self.C[z]
        print 'restricoes: ', aux
        print 'custo: ', self.P[z]
        aux = self.C[z] + aux
        if aux < 0:
            aux = 0.01
        self.EE[z] = aux/self.P[z]
        print 'EE: ', self.EE[z] 

    def mt_calculate_data_rate_n(self,z,n):
        result = 0
        for k in range(0, self.K):
            log = (self.i[z][n][k]* self.p[z][n][k])
            if log <= 0:
                log = 1
            result += (self.a[z][n][k] * self._b0 * math.log(1+math.log(log)))
        return result

    def mt_calculate_subgradient_beta(self,n,z):
        result = 0
        c = self.mt_calculate_data_rate_n(z,n)
        if ((n > 0) and (n < len(self._ues))):
            result = c - self._nr
        else:
            result = c - self._ner
        return result            

    def mt_calculate_subgradient_lambda(self,z,k):
        result = 0
        soma = 0
        if (len(self._ues) > 0):
            for n in range (0, len(self._ues)):
                soma += self.a[z][n][k] * self.p[z][n][k] * self._dr2m * self._hr2m
            result = self._delta_0 - soma
        return result

    def mt_calculate_subgradient_upsilon(self,z):
        soma = 0
        for n in range(0, len(self._ues)):
            for k in range(0, self.K):
                soma += self.a[z][n][k] * self.p[z][n][k]
        return self._pm - soma

    def mt_calculate_beta_n_l1(self,n,z):
        result = self.betan[z][n] - (self._epsilon_beta * self.sub_bn[z][n])
        if result > 0:
            return result
        else:
            return 1

    def mt_calculate_lamdak_l1(self,k,z):
        result = self.lambdak[z][k] - (self._epsilon_lambda * self.sub_lambda_k[z][k])
        if result > 0:
            return result
        else:
            return 1

    def mt_calculate_upsilon_l1(self,z):
        result = self.upsilonl[z] - (self._epsilon_upsilon * self.sub_upsilon[z])
        if result > 0:
            return result
        else:
            return 1

    def mt_update_l(self,z):
        for n in range(0,len(self._ues)):
            self.sub_bn[z][n] = self.mt_calculate_subgradient_beta(n,z)
            self.betan[z][n] = self.mt_calculate_beta_n_l1(n,z)
        print n

        for k in range(0, self._K):
            self.sub_lambda_k[z][k] = self.mt_calculate_subgradient_lambda(z,k)
            self.lambdak[z][k] = self.mt_calculate_lamdak_l1(k,z)

        print ("z" + str(z))
        self.sub_upsilon[z] = self.mt_calculate_subgradient_upsilon(z)
        self.upsilonl[z] = self.mt_calculate_upsilon_l1(z)

    ##########################
    # Calculo do EE
    #########################
    def mt_data_rate(self, best_a, best_i, best_p):
        result = 0
        for n in range(0, len(self._ues)): 
            result += self.mt_data_rate_n(n,best_a,best_i, best_p) 

        return result

    def mt_data_rate_n(self, n, best_a, best_i, best_p):
        result = 0
        for k in range(0, self.K):
            log = 1+(best_i[n][k]* best_p[n][k])
            if log < 0:
                log = 1
            result += (best_a[n][k] * self._b0 * math.log(log))

        return result

    #P (3)
    def mt_power_consumition(self,best_a, best_p):
        result = 0
        for n in range(0, len(self._ues)):
            for k in range(0, self._K):
                result += (best_a[n][k] * best_p[n][k])           

            return (self._eff * result) + self._prc + self._pbh
                                
