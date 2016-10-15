from antenna import Antenna
from grid import Grid
from util import *
import math
import csv
import time

DEBUG = False

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

def associate_user_in_antennas(ues, antennas):
    #######################
    # Associa usuario na 
    # antena mais proxima
    ########################
    for ue in ues:
        distance = 10000
        near = antennas[0]
        for antenna in antennas:
            d = dist( ue, antenna ) 
            if antenna.type == Antenna.BS_ID:
                if d < distance and d<Antenna.BS_RADIUS:
                    distance = d
                    near = antenna
            elif antenna.type == Antenna.RRH_ID:
                if d < distance and  d<Antenna.RRH_RADIUS:
                    distance = d
                    near = antenna

        ue._connected_antenna = near
        near.connected_ues.append(ue)

class FixedPower(object):
    
    def __init__(self, r):
        self.antennas = []
        #self.small = s
        #self.macros = m
        #self.users = u * m
        self.repeticao = r

    def run(self, grid, max_i):
        antennas = grid._antennas    
        ues = grid._user
        init = time.time()
        associate_user_in_antennas(ues, antennas)
        iteracao = 0

        #Para as BS aloca de forma sequencial iniciando do RB zero
        for bs in grid.bs_list:
            used_rbs = 0
            bs.i = numpy.zeros(shape=(len(bs.connected_ues), Antenna.TOTAL_RBS))
            bs.a = numpy.zeros(shape=(len(bs.connected_ues), Antenna.TOTAL_RBS))
            bs.p = numpy.zeros(shape=(len(bs.connected_ues), Antenna.TOTAL_RBS))
            if(used_rbs<Antenna.TOTAL_RBS):
                for ue in range(0,len(bs.connected_ues)):
                    needed_rbs = bs.demand_in_rbs(bs.connected_ues[ue])
                    for rb in range(used_rbs, used_rbs+needed_rbs):
                        if(rb<Antenna.TOTAL_RBS):
                            bs.i[ue][rb] = interference(bs.connected_ues[ue], rb, grid._antennas) #dBm
                            bs.p[ue][rb] = Antenna.POWER_BS
                            bs.a[ue][rb] = 1

                    used_rbs = used_rbs+needed_rbs
            bs.obtain_energy_efficient()
            grid.write_to_resume('FIXED POWER', self.repeticao, iteracao, init)
            iteracao += 1
            debug_printf("----- BS -----")
            debug_printf("Alloc = \n" + str(numpy.matrix(bs.a)))
            debug_printf("Power = \n" + str(numpy.matrix(bs.p)))
            debug_printf("Noise = \n" + str(numpy.matrix(bs.i)))

        #Para as RRHs aloca o RB de menor interferencia
        for rrh in grid.rrh_list:
            rrh.i = numpy.zeros(shape=(len(rrh.connected_ues), Antenna.TOTAL_RBS))
            rrh.a = numpy.zeros(shape=(len(rrh.connected_ues), Antenna.TOTAL_RBS))
            rrh.p = numpy.zeros(shape=(len(rrh.connected_ues), Antenna.TOTAL_RBS))
            auxi = numpy.zeros(shape=(len(rrh.connected_ues), Antenna.TOTAL_RBS))
            for ue in range(0, len(rrh.connected_ues)):
                needed_rbs = rrh.demand_in_rbs(rrh.connected_ues[ue])
                for rb in range(0, Antenna.TOTAL_RBS):
                    i = interference(rrh.connected_ues[ue], rb, grid._antennas) #dBm
                    rrh.i[ue][rb] = i 
                    auxi[ue][rb] = i    
                for k in range(0, needed_rbs):
                    rb = numpy.argmin(auxi[ue,:])
                    if auxi[ue,rb] < 9999999:
                        auxi[:,rb] = 9999999 #NAO PODE USAR DUAS VEZES O MESMO RB - VERIFICAR SE OUTRO USUARIO JA NAO UTILIZOU
                        rrh.p[ue][rb] = Antenna.POWER_RRH
                        rrh.a[ue][rb] = 1
                    else:
                        break
            rrh.obtain_energy_efficient()
            grid.write_to_resume('FIXED POWER', self.repeticao, iteracao, init)
            iteracao += 1
            debug_printf("----- RRH -----")
            debug_printf("Alloc = \n" + str(numpy.matrix(rrh.a)))
            debug_printf("Power = \n" + str(numpy.matrix(rrh.p)))
            debug_printf("Noise = \n" + str(numpy.matrix(rrh.i)))

        while iteracao < max_i:
            #print "Nova I"
            ant = grid.antennas[0]
            ue = -1
            datarate = 9999999999999999999999
            for antena in grid.antennas:
                if numpy.sum(antena.a) < Antenna.TOTAL_RBS:
                    for user in range(0, len(antena.connected_ues)):
                        if antena.user_data_rate[user] < datarate:
                            ant = antena
                            ue = user
                            datarate = antena.user_data_rate[user]
            
            #print "User = ", ue

            auxi = numpy.copy(ant.i)
            tr = 0 #total de tentativas
            while tr < Antenna.TOTAL_RBS: 
                #print "while"
                tr += 1
                rb = numpy.argmin(auxi[ue,:])
                mue = numpy.argmax(ant.a[:,rb])
                #print rb
                if ant.a[ue][rb] == 0 and ant.a[mue][rb] == 0:
                    if (ant.type == Antenna.BS_ID):
                        ant.p[ue][rb] = Antenna.POWER_BS
                    else:
                        ant.p[ue][rb] = Antenna.POWER_RRH
                    ant.a[ue][rb] = 1

                    for antena in grid.antennas:
                        if antena.a != None and len(antena.connected_ues) > 0:
                            mue = numpy.argmax(antena.a[:,rb])
                            if (antena.a[mue,rb] > 0):
                                antena.i[mue][rb] = interference(antena.connected_ues[mue], rb, grid._antennas)
                    #print "NOVO RB"
                    break
                else:
                    auxi[ue][rb] = 9999999

            ant.obtain_energy_efficient()
            grid.write_to_resume('FIXED POWER', self.repeticao, iteracao, init)
            iteracao += 1




        

