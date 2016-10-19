from antenna import Antenna
from grid import Grid
from util import *
import math
import csv
import time
import threeGPP
import Calculations as calc

class Sequential(object):
    
    def __init__(self, r):
        self.antennas = []
        self.repeticao = r


    def run(self, grid, max_i):
        antennas = grid._antennas    
        ues = grid._user
        init = time.time()
        iteracao = 0

        grid.energy_efficient          = numpy.zeros(shape=(1)) 
        grid.consumition               = numpy.zeros(shape=(1))
        grid.datarate                  = numpy.zeros(shape=(1))
        grid.fairness                  = numpy.zeros(shape=(1))
        grid.meet_users                = numpy.zeros(shape=(1))

        #Para as BS aloca de forma sequencial iniciando do RB zero
        for bs in grid.antennas:
            used_rbs = 0
            bs.i                = numpy.zeros(shape=(1, len(bs.connected_ues), threeGPP.TOTAL_RBS))
            bs.a                = numpy.zeros(shape=(1, len(bs.connected_ues), threeGPP.TOTAL_RBS))
            bs.p                = numpy.zeros(shape=(1, len(bs.connected_ues), threeGPP.TOTAL_RBS))
            bs.energy_efficient = numpy.zeros(shape=(1)) 
            bs.consumition      = numpy.zeros(shape=(1)) 
            bs.datarate         = numpy.zeros(shape=(1))
            bs.datarate_constraint = numpy.zeros(shape=(1))
            bs.user_datarate    = numpy.zeros(shape=(1,len(bs.connected_ues)))
            bs.user_consumption = numpy.zeros(shape=(1,len(bs.connected_ues)))
            bs.fairness         = numpy.zeros(shape=(1))
            bs.meet_users       = numpy.zeros(shape=(1))

            if(used_rbs<threeGPP.TOTAL_RBS):
                for ue in range(0,len(bs.connected_ues)):
                    needed_rbs = calc.demand_in_rbs(bs, ue)
                    for rb in range(used_rbs, used_rbs+needed_rbs):
                        if(rb<threeGPP.TOTAL_RBS):
                            bs.i[0][ue][rb] = calc.power_interference(ue, rb, bs, grid) #dBm
                            bs.p[0][ue][rb] = calc.transmission_power(bs, bs.connected_ues[ue], bs.i[0,ue,rb], noise(), threeGPP.TARGET_SINR)
                            if bs.p[0][ue][rb] != None and math.isnan(bs.p[0][ue][rb]) == False:
                                bs.a[0][ue][rb] = 1
                            else:
                                bs.a[0][ue][rb] = 0
                                bs.i[0][ue][rb] = None
                                bs.p[0][ue][rb] = None
                    used_rbs = used_rbs+needed_rbs

            calc.datarate(bs, grid)
            calc.consumption(bs)
            calc.efficiency(bs)
            calc.fairness(bs)
            #bs.toString()

        grid.write_to_resume('Sequential', self.repeticao, iteracao, init)

        iteracao += 1
        while iteracao < max_i:
            ant = grid.antennas[0]
            ue = -1
            datarate = 9999999999999999999999
            for antena in grid.antennas:
                if numpy.sum(antena.a[0]) < threeGPP.TOTAL_RBS and len(antena.connected_ues) > 0:
                    rest = antena.rest_power()
                    if rest != None and math.isnan(rest) == False:
                        for user in range(0, len(antena.connected_ues)):
                            #print antena.user_datarate[0,user], datarate
                            if antena.user_datarate[0,user] < datarate:
                                ant = antena
                                ue = user
                                datarate = antena.user_datarate[0,user] 

            #print "Antena", ant.type
            #auxi = numpy.copy(ant.i)
            if ue > 0:
                needed_rbs = calc.demand_in_rbs(ant, ue)
                #print "Need RBs = ", needed_rbs
                while ant.used_rbs() < threeGPP.TOTAL_RBS and needed_rbs > 0: 
                    rb = ant.used_rbs()
                    mue = numpy.argmax(ant.a[0,:,rb])
                    #print rb
                    if ant.a[0][ue][rb] == 0 and ant.a[0][mue][rb] == 0:
                        ant.p[0][ue][rb] = calc.transmission_power(ant, ant.connected_ues[ue], ant.i[0,ue,rb], noise(), threeGPP.TARGET_SINR)
                        if ant.p[0][ue][rb] != None and math.isnan(ant.p[0][ue][rb]) == False:
                            ant.a[0][ue][rb] = 1
                            #print "Need -1"
                            needed_rbs = needed_rbs - 1
                        else:
                            ant.a[0][ue][rb] = 0
                            ant.i[0][ue][rb] = None
                            ant.p[0][ue][rb] = None
                            break;                    

                        for antena in grid.antennas:
                            if antena.a != None and len(antena.connected_ues) > 0:
                                mue = numpy.argmax(antena.a[0,:,rb])
                                if (antena.a[0,mue,rb] > 0):
                                    antena.i[0][mue][rb] = calc.power_interference(mue, rb, antena, grid) #dBm
                                    antena.p[0][mue][rb] = calc.transmission_power(antena, antena.connected_ues[mue], antena.i[0][mue][rb], noise(), threeGPP.TARGET_SINR)
                   
            calc.datarate(ant, grid)
            calc.consumption(ant)
            calc.efficiency(ant)
            calc.fairness(ant)

            grid.write_to_resume('Sequential', self.repeticao, iteracao, init)
            iteracao += 1