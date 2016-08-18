from antenna import Antenna
from grid import Grid
from util import *
import math
import csv
import time

DEBUG = True

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

class Greedy(object):
    
    def __init__(self, r):
        self.antennas = []
        #self.small = s
        #self.macros = m
        #self.users = u * m
        self.repeticao = r

    def run(self, grid):
        antennas = grid._antennas    
        ues = grid._user
        init = time.time()
        associate_user_in_antennas(ues, antennas)

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
                            bs.i[ue][rb] = bs.interference(bs.connected_ues[ue], rb, grid._antennas) #dBm
                            bs.p[ue][rb] = Antenna.POWER_BS
                            bs.a[ue][rb] = 1
                    used_rbs = used_rbs+needed_rbs
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
                    i = rrh.interference(rrh.connected_ues[ue], rb, grid._antennas) #dBm
                    rrh.i[ue][rb] = i 
                    auxi[ue][rb] = i    
                for k in range(0, needed_rbs):
                    rb = numpy.argmin(auxi[ue,:])
                    if auxi[ue,rb] < 9999999:
                        auxi[:,rb] = 9999999
                        #NAO PODE USAR DUAS VEZES O MESMO RB - VERIFICAR SE OUTRO USUARIO JA NAO UTILIZOU
                        rrh.p[ue][rb] = Antenna.POWER_RRH
                        rrh.a[ue][rb] = 1
                    else:
                        break;
            debug_printf("----- RRH -----")
            debug_printf("Alloc = \n" + str(numpy.matrix(rrh.a)))
            debug_printf("Power = \n" + str(numpy.matrix(rrh.p)))
            debug_printf("Noise = \n" + str(numpy.matrix(rrh.i)))


        grid.write_to_resume('GREEDY', self.repeticao, 1, init)




        

