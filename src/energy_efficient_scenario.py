#########################################################
# @file     energy_efficient_n_bs.py
# @author   Gustavo de Araujo
# @date     17 Mar 2016
#########################################################

from peng import *
from antenna import *
from user import *
from bbu import *
from controller import *
from util import *
from grid import *
from cluster import *
from antenna_peng import *
from antenna_mc import *
from ra_mc import *
from multiprocessing import Process, Queue
from joblib import Parallel, delayed
import csv
import random
import numpy
import scipy
import multiprocessing
import gc

###############################
#Grid definitions
###############################
DEBUG                   = True
DMACROMACRO             = 500
DMACROUE                = 30    #35
DMACROCLUSTER           = 90    #105
DSMALLUE                = 5
DSMALLSMALL             = 10
DROPRADIUS_MC           = 250
DROPRADIUS_SC           = 500
DROPRADIUS_SC_CLUSTER   = 70
DROPRADIUS_UE_CLUSTER   = 70
DSMALLUE                = 5
MAX_BS                  = 7
MAX_REP                 = 10

###############################
#Test Variables
###############################
n_sites      = 7
n_ues        = 60
uesindoor    = 0.2
uessmallcell = 2/3

###################################
#Functions
###################################

DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)

########################################
def build_scenario(n_bbu, n_bs, n_clusters, n_rrh, n_ue):
    grid1 = Grid(size=(2000,2000))
    grid2 = Grid(size=(2000,2000))
    macrocells_center = list()

    cntrl1 = Controller(grid1, control_network=False)
    grid1.add_controller(cntrl1)

    cntrl2 = Controller(grid2, control_network=False)
    grid2.add_controller(cntrl2)

    for i in range(n_bbu):
        rpos = grid1.random_pos()
        bbu1 = BBU(pos=rpos, controller=cntrl1, grid=grid1)
        bbu2 = BBU(pos=rpos, controller=cntrl2, grid=grid2)
        grid1.add_bbu(bbu1)
        grid2.add_bbu(bbu2)

    grids = [grid1, grid2]

    macrocells(grids, DMACROMACRO, n_bs,  macrocells_center)

    if not(n_rrh < 1):
        clusters(grids, macrocells_center, n_clusters, n_rrh)

    users(grids, macrocells_center, n_bs, n_clusters, n_ue)

    return grids

##########################
def users(grids, macrocells_center, n_bs, n_clusters, n_ue):
    count_ue = 0
    p_users = list()

    for i in range(0, n_bs):
        reset = 1001
        count_ue = 0
        while (count_ue < n_ue):
            
            p_is_ok = True
            if reset > 1000:
                count_ue = 0
                reset = 0
                p_users = list()

            if n_clusters > 0:
                x = (i*n_clusters)
                y = ((i*n_clusters) + n_clusters)-1
                r = random.randint(x,y)
                print("x: " + str(x) + " y: " + str(y) + " r: " + str(r))
                cluster = grids[0]._clusters[r]

            #Define type of user
            if random.random() < 0.666 and n_clusters > 0:
                p = generate_xy(cluster._pos, DROPRADIUS_UE_CLUSTER, 0)
                p_is_ok = is_possition_ok(p, cluster._pos, DSMALLSMALL)
            else:
                p = generate_xy(macrocells_center[i], DMACROMACRO*0.425, DMACROUE)
            
            #Distribution
            if not(p_is_ok):
                    reset = reset + 1
            else:
                count_ue = count_ue + 1
                print p
                p_users.append(p)
            
        for j in range(0,len(p_users)):
            if random.random() < 0.3:
                user_type = User.HIGH_RATE_USER
            else:
                user_type = User.LOW_RATE_USER
            u1 = User(j, p_users[j], None, grids[0], user_type)
            grids[0].add_user(u1)
            u2 = User(j, p_users[j], None, grids[1], user_type)
            grids[1].add_user(u2)

########################################
def clusters(grids, macrocells_center, n_clusters, n_antennas):
    count_antennas = 0
    count_clusters = 0
    p_antennas = list()
    p_clusters = list()
    p_local_clusters = list()
    p_local_antennas = list()
    reset = 0;

    for i in range(0, len(macrocells_center)):
        count_clusters = 0
        #print("Create macrocells cluster and rhh: " + str(i))

        while (count_clusters < n_clusters):
            #Generate antennas
            reset = 0;
            count_antennas = 0

            pos = generate_xy(macrocells_center[i],
                    DMACROMACRO*0.425, DMACROCLUSTER)
            p_local_clusters.append(pos)

            while (count_antennas <= n_antennas-1):
                #If it is impossible to allocate the antennas
                #then clean the clusters and do it again
                if reset > 1000:
                    print "rest"
                    count_antennas = 0
                    count_clusters = 0
                    p_local_clusters = list()
                    p_local_antennas = list()
                    pos = generate_xy(macrocells_center[i],
                        DMACROMACRO*0.425, DMACROCLUSTER)
                    p_local_clusters.append(pos)
                    reset = 0

                p = generate_xy(pos, DROPRADIUS_SC_CLUSTER*0.425, 0)
               
                if (is_possition_ok(p, p_local_antennas, DSMALLSMALL) and 
                        (is_possition_ok(p, pos, DSMALLSMALL))):
                    count_antennas = count_antennas + 1
                    p_local_antennas.append(p)
                else:
                    reset = reset + 1
                 
            count_clusters = count_clusters + 1

            for j in range(0,len(p_local_antennas)):
                p_antennas.append(p_local_antennas[j])
        
            p_local_antennas = list()

        for k in range(0,len(p_local_clusters)):
            p_clusters.append(p_local_clusters[k])

        #Tem que limpar as listas
        p_local_clusters = list()

    for l in range(0, len(p_clusters)):
        cluster1 = Cluster(l+1, p_clusters[l], grids[0])
        grids[0].add_cluster(cluster1)
        cluster2 = Cluster(l+1, p_clusters[l], grids[1])
        grids[1].add_cluster(cluster2)

    for t in range(0, len(p_antennas)):
        rrh1 = AntennaMc(t+1, Antenna.RRH_ID, p_antennas[t], None, grids[0])
        grids[0].add_antenna(rrh1)
        rrh2 = AntennaPeng(t+1, Antenna.RRH_ID, p_antennas[t], None, grids[1])
        grids[1].add_antenna(rrh2)

########################################
def is_possition_ok(p, vector, min_distance):
    result = True
    if len(vector) != 0:
        for i in range(0, len(vector)):
            d = euclidian(p,vector[i])
            if  (d < min_distance) or (d == 0):
                result = False
    return result

######################################## 
def generate_xy(center, radius, min_distance):
    pos = [None] * 2 
    not_done = True
    while not_done:
        pos[0] = radius * (1 - 2 * random.random()) + center[0]
        pos[1] = radius * (1 - 2 * random.random()) + center[1]
        not_done = euclidian(pos, center) < min_distance

    return pos

######################################## 
def euclidian(a,b):
   return scipy.spatial.distance.euclidean(a,b)

########################################
def macrocells(grids, radius, n_bs, macrocells_center):
    center = numpy.array([grids[0].size[0]/2, grids[0].size[1]/2])
    index = 0

    #Center Antenna
    macrocells_center.append((grids[0].size[0]/2, grids[0].size[1]/2))
    #bs = Antenna(0, Antenna.BS_ID, center, None, grid)
    #bs = AntennaPeng(0, Antenna.BS_ID, center, None, grid)
    bs1 = AntennaMc(0, Antenna.BS_ID, center, None, grids[0])
    grids[0].add_antenna(bs1)

    bs2 = AntennaPeng(0, Antenna.BS_ID, center, None, grids[1])
    grids[1].add_antenna(bs2)

    #Others
    for i in range (0, n_bs-1):
        v = (2 * i) + 1
        #It is not cool initiazile variables in loops...
        #But it only works like this :(
        p_antenna = [None] * 2
        p_antenna[0] = center[0] + radius * math.cos(v*math.pi/6)
        p_antenna[1] = center[1] + radius * math.sin(v*math.pi/6)
        macrocells_center.append(p_antenna)

        bs1 = AntennaMc(i+1, Antenna.BS_ID, p_antenna, None, grids[0])
        grids[0].add_antenna(bs1)

        bs2 = AntennaPeng(i+1, Antenna.BS_ID, p_antenna, None, grids[1])
        grids[1].add_antenna(bs2)

########################################

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

def build_fixed_scenario():
    grid = Grid(size=(2000,2000))
    macrocells_center = list()

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)

    n_bbu = 2
    for i in range(n_bbu):
        bbu = BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        grid.add_bbu(bbu)

    #Center Antenna
    center = numpy.array([grid.size[0]/2, grid.size[1]/2])
    #BS
    bs = AntennaMc(0, Antenna.BS_ID, center, None, grid)
    #bs = AntennaPeng(0, Antenna.BS_ID, center, None, grid)
    grid.add_antenna(bs)

    #Cluster
    cluster = Cluster(1, [1050, 1050], grid)
    grid.add_cluster(cluster)

    #RRHs
    rrh = AntennaMc(1, Antenna.RRH_ID, [1040, 1040], None, grid)
    #rrh = AntennaPeng(1, Antenna.RRH_ID, [1040, 1040], None, grid)
    grid.add_antenna(rrh)

    #Users
    u1 = User(1, [1045, 1045], None, grid, User.HIGH_RATE_USER)
    grid.add_user(u1)

    u2 = User(2, [880, 880], None, grid, User.LOW_RATE_USER)
    grid.add_user(u2)

    associate_user_in_antennas(grid._user, grid._antennas)


    bs.snir = numpy.zeros(shape=(len(bs.connected_ues), bs.TOTAL_RBS))
    bs.noise_plus_interference = numpy.zeros(shape=(len(bs.connected_ues), bs.TOTAL_RBS))
    bs.a = numpy.ones(shape=(len(bs.connected_ues), bs.TOTAL_RBS))
    bs.p = numpy.zeros(shape=(len(bs.connected_ues), bs.TOTAL_RBS))

    rrh.snir = numpy.zeros(shape=(len(rrh.connected_ues), rrh.TOTAL_RBS))
    rrh.noise_plus_interference = numpy.zeros(shape=(len(rrh.connected_ues), rrh.TOTAL_RBS))
    rrh.a = numpy.zeros(shape=(len(rrh.connected_ues), rrh.TOTAL_RBS))
    rrh.p = numpy.zeros(shape=(len(rrh.connected_ues), rrh.TOTAL_RBS))

    bs.obtain_sinr(grid)
    rrh.obtain_sinr(grid)
    
    debug_printf("----- BS -----")
    debug_printf("Alloc = \n" + str(numpy.matrix(bs.a)))
    debug_printf("Power = \n" + str(numpy.matrix(bs.p)))
    debug_printf("Noise = \n" + str(numpy.matrix(bs.noise_plus_interference)))
    bs.obtain_energy_efficient()
    debug_printf("Data Rate = \n" + str(bs.data_rate))
    debug_printf("Power Consumition = \n" + str(bs.power_consumition))
    debug_printf("Energy Efficient = \n" + str(bs.energy_efficient))


    debug_printf("----- RRH -----")
    debug_printf("Alloc = \n" + str(numpy.matrix(rrh.a)))
    debug_printf("Power = \n" + str(numpy.matrix(rrh.p)))
    debug_printf("Noise = \n" + str(numpy.matrix(rrh.noise_plus_interference)))
    rrh.obtain_energy_efficient()
    debug_printf("Data Rate = \n" + str(rrh.data_rate))
    debug_printf("Power Consumition = \n" + str(rrh.power_consumition))
    debug_printf("Energy Efficient = \n" + str(rrh.energy_efficient))

    return grid

def do_mc(nbs, ue, rep, grid):
    print "Starting scenario", rep, "with", nbs, "macros for MC!"
    mc = Mc(nbs, ue, rep)
    mc.run(grid);

def do_peng(nbs, ue, rep, grid):
    print "Starting scenario", rep, "with", nbs, "macros for Peng!"
    peng = Peng(nbs, ue, rep)
    peng.run(grid);

def processInput(nbs):
    bbu = 2 
    cluster = 1
    rrh = 10
    ue = 30

    bs = (nbs%MAX_BS)+1
    rep = (nbs%MAX_REP)+1

    #print "Starting scenario", rep, "with", bs, "macros for MC!"

    grids = build_scenario(bbu, bs, cluster, rrh, ue) 
    do_mc(bs, ue, rep, grids[0])
    
    #do_peng(bs, ue, rep, grids[1])

    del grids
    gc.collect()
    

########################################
# Main
########################################
if __name__ == "__main__":

    # Trying to create a new file or open one
    f = open('resumo.csv','w')
    f.write('CASE,U,R,I,C,P,EE,T\n')
    f.close()
    
    #Parametros do Bob
    #bs = 2
    #bbu = 2 
    #cluster = 2
    #rrh = 3
    #ue = 10

    #grids = build_scenario(bbu, bs, cluster, rrh, ue)
    #util.plot_grid(grids[0])

    #bs = [1, 2, 3, 4, 5, 6, 7]

    num_cores = multiprocessing.cpu_count()

    #for rep in range(0, 10):
    #Parallel(n_jobs=num_cores)(delayed(processInput)(nbs) for nbs in range(0, MAX_BS*MAX_REP))

    #grid = build_scenario(bbu, bs, cluster, rrh, ue)
    grid = build_fixed_scenario()
    util.plot_grid(grid)
    #mc = Mc(1, 30, 1)
    #mc.run(grid)

    #peng = Peng(bs, ue, 1)
    #peng.run(grid)

            



