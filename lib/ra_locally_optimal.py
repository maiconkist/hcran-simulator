from antenna import Antenna
from grid import Grid
from util import *
import math
import csv
import time
import threeGPP
import Calculations as calc

class LocallyOptimal(object):
    
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
        for bs in grid.bs_list:
            used_rbs = 0
            bs.i                = numpy.zeros(shape=(1, len(bs.connected_ues), threeGPP.TOTAL_RBS))
            bs.a                = numpy.zeros(shape=(1, len(bs.connected_ues), threeGPP.TOTAL_RBS))
            bs.p                = numpy.zeros(shape=(1, len(bs.connected_ues), threeGPP.TOTAL_RBS))
            bs.energy_efficient = numpy.zeros(shape=(1)) 
            bs.consumition      = numpy.zeros(shape=(1)) 
            bs.datarate         = numpy.zeros(shape=(1))
            bs.datarate_constraint = numpy.zeros(shape=(1))
            bs.user_datarate    = numpy.zeros(shape=(1,len(bs.connected_ues)))
            bs.fairness         = numpy.zeros(shape=(1))
            bs.meet_users       = numpy.zeros(shape=(1))

            if(used_rbs<threeGPP.TOTAL_RBS):
                for ue in range(0,len(bs.connected_ues)):
                    needed_rbs = calc.demand_in_rbs(bs.connected_ues[ue])
                    for rb in range(used_rbs, used_rbs+needed_rbs):
                        if(rb<threeGPP.TOTAL_RBS):
                            bs.i[0][ue][rb] = calc.power_interference(ue, rb, bs, grid) #dBm
                            bs.p[0][ue][rb] = calc.transmission_power(bs, bs.connected_ues[ue], bs.i[0][ue][rb])
                            bs.a[0][ue][rb] = 1

                    used_rbs = used_rbs+needed_rbs
            calc.datarate(bs)
            calc.consumption(bs)
            calc.efficiency(bs)
            calc.fairness(bs)

        #Para as RRHs aloca o RB de menor interferencia
        for rrh in grid.rrh_list:
            rrh.i                = numpy.zeros(shape=(1, len(rrh.connected_ues), threeGPP.TOTAL_RBS))
            rrh.a                = numpy.zeros(shape=(1, len(rrh.connected_ues), threeGPP.TOTAL_RBS))
            rrh.p                = numpy.zeros(shape=(1, len(rrh.connected_ues), threeGPP.TOTAL_RBS))
            rrh.energy_efficient = numpy.zeros(shape=(1)) 
            rrh.consumition      = numpy.zeros(shape=(1)) 
            rrh.datarate         = numpy.zeros(shape=(1))
            rrh.datarate_constraint = numpy.zeros(shape=(1))
            rrh.user_datarate    = numpy.zeros(shape=(1,len(rrh.connected_ues)))
            rrh.fairness         = numpy.zeros(shape=(1))
            rrh.meet_users       = numpy.zeros(shape=(1))
            auxi                 = numpy.zeros(shape=(1, len(rrh.connected_ues), threeGPP.TOTAL_RBS))
            for ue in range(0, len(rrh.connected_ues)):
                needed_rbs = calc.demand_in_rbs(rrh.connected_ues[ue])
                for rb in range(0, threeGPP.TOTAL_RBS):
                    i = calc.power_interference(ue, rb, rrh, grid) 
                    rrh.i[0][ue][rb] = i 
                    auxi[0][ue][rb] = i    
                for k in range(0, needed_rbs):
                    rb = numpy.argmin(auxi[0,ue,:])
                    if auxi[0][ue,rb] < 9999999:
                        auxi[0][:,rb] = 9999999 #NAO PODE USAR DUAS VEZES O MESMO RB - VERIFICAR SE OUTRO USUARIO JA NAO UTILIZOU
                        rrh.p[0][ue][rb] = calc.transmission_power(rrh, rrh.connected_ues[ue], rrh.i[0][ue][rb])
                        rrh.a[0][ue][rb] = 1
                    else:
                        break

            calc.datarate(rrh)
            calc.consumption(rrh)
            calc.efficiency(rrh)
            calc.fairness(rrh)

        grid.write_to_resume('Locally Optimal', self.repeticao, iteracao, init)

        iteracao += 1
        while iteracao < max_i:

            ant = grid.antennas[0]
            ue = -1
            datarate = 9999999999999999999999
            for antena in grid.antennas:
                if numpy.sum(antena.a[0]) < threeGPP.TOTAL_RBS:
                    for user in range(0, len(antena.connected_ues)):
                        if antena.user_datarate[0,user] < datarate:
                            ant = antena
                            ue = user
                            datarate = antena.user_datarate[0,user]
                            for rb in range(0, threeGPP.TOTAL_RBS):
                                ant.i[0][ue][rb] = calc.power_interference(ue, rb, ant, grid) #dBm

            auxi = numpy.copy(ant.i)
            needed_rbs = calc.demand_in_rbs(ant.connected_ues[ue])
            tr = 0 #total de tentativas
            while tr < threeGPP.TOTAL_RBS and needed_rbs > 0: 
                tr += 1
                rb = numpy.argmin(auxi[0,ue,:])
                mue = numpy.argmax(ant.a[0,:,rb])
                #print rb
                if ant.a[0][ue][rb] == 0 and ant.a[0][mue][rb] == 0:
                    ant.p[0][ue][rb] =calc.transmission_power(ant, ant.connected_ues[ue], ant.i[0][ue][rb])
                    ant.a[0][ue][rb] = 1
                    needed_rbs = needed_rbs - 1

                    for antena in grid.antennas:
                        if antena.a != None and len(antena.connected_ues) > 0:
                            mue = numpy.argmax(antena.a[0,:,rb])
                            if (antena.a[0,mue,rb] > 0):
                                antena.i[0][mue][rb] = calc.power_interference(mue, rb, antena, grid) #dBm
                                antena.p[0][mue][rb] = calc.transmission_power(antena, antena.connected_ues[mue], antena.i[0][mue][rb])
                    break
                else:
                    auxi[0][ue][rb] = 9999999

            calc.datarate(ant)
            calc.consumption(ant)
            calc.efficiency(ant)
            calc.fairness(ant)

            grid.write_to_resume('Locally Optimal', self.repeticao, iteracao, init)
            iteracao += 1