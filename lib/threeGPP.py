import math
import scipy.spatial
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from antenna import * 
from user import *
from bbu import *
from controller import *
from util import *
from grid import *
from cluster import *
from antenna_mc import *
import random
import numpy
import scipy

#VARIABLE CONSTANTS
RRH_RADIUS  = 50
BS_RADIUS   = 710
POWER_BS    = 46
POWER_RRH   = 23
TARGET_SINR = 14.5 #[db]
HPN_T_GAIN  = 5                       #transmission antenna gain
LPN_T_GAIN  = 17                       #transmission antenna gain
UE_R_GAIN   = 0                       #receptor antenna gain
WAVELENTH   = (3/19.0)                #Comprimento de onda considerando uma frequencia de 1.9 GHz
TOTAL_RBS   = 100
CHANNEL     = 20000000 #Hz
RB_BIT_CAPACITY = 406.499955591 #bits/0.5 ms with a SINR  18.8
B0          = 180000
N0          = -17
DRN         = 1         
HRN         = 1         
DMN         = 450
HMN         = 1
PRC         = 6.8
PBH         = 3.85
PMC         = 10
PMBH        = 3.85
EFF         = 2
MEFF        = 4 
NR          = 5242880/2000 #High Rate Constraint
NER         = 5242880/2000 #Low Rate Constraint
#NR          = 1000000/2000 #High Rate Constraint
#NER         = 1000000/2000 #Low Rate Constraint

###############################
#Grid definitions
###############################
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

###################################
#Functions
###################################
def build_scenario(n_bbu, n_bs, n_clusters, n_rrh, n_ue):
    grid1 = Grid(size=(2000,2000))
    grid2 = Grid(size=(2000,2000))
    grid3 = Grid(size=(2000,2000))
    macrocells_center = list()

    cntrl1 = Controller(grid1, control_network=False)
    grid1.add_controller(cntrl1)

    cntrl2 = Controller(grid2, control_network=False)
    grid2.add_controller(cntrl2)

    cntrl3 = Controller(grid3, control_network=False)
    grid3.add_controller(cntrl3)


    for i in range(n_bbu):
        rpos = grid1.random_pos()
        bbu1 = BBU(pos=rpos, controller=cntrl1, grid=grid1)
        bbu2 = BBU(pos=rpos, controller=cntrl2, grid=grid2)
        bbu3 = BBU(pos=rpos, controller=cntrl3, grid=grid3)
        grid1.add_bbu(bbu1)
        grid2.add_bbu(bbu2)
        grid3.add_bbu(bbu3)

    grids = [grid1, grid2, grid3]

    macrocells(grids, DMACROMACRO, n_bs,  macrocells_center)

    if not(n_rrh < 1):
        clusters(grids, macrocells_center, n_clusters, n_rrh)

    users(grids, macrocells_center, n_bs, n_clusters, n_ue)

    associate_user_in_antennas(grids[0].users, grids[0].antennas)
    associate_user_in_antennas(grids[1].users, grids[1].antennas)
    associate_user_in_antennas(grids[2].users, grids[2].antennas)

    return grids

##########################
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
                if d < distance and d<BS_RADIUS:
                    distance = d
                    near = antenna
            elif antenna.type == Antenna.RRH_ID:
                if d < distance and  d<RRH_RADIUS:
                    distance = d
                    near = antenna

        ue._connected_antenna = near
        near.connected_ues.append(ue)

##########################

def build_fixed_scenario():
    grid = Grid(size=(2000,2000))
    grid2 = Grid(size=(2000,2000))
    macrocells_center = list()

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)
    cntrl2 = Controller(grid2, control_network=False)
    grid2.add_controller(cntrl2)

    n_bbu = 2
    for i in range(n_bbu):
        bbu = BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        grid.add_bbu(bbu)
        bbu2 = BBU(pos=grid.random_pos(), controller=cntrl2, grid=grid2)
        grid2.add_bbu(bbu2)

    #Center Antenna
    center = numpy.array([grid.size[0]/2, grid.size[1]/2])
    #BS
    bs = Antenna(0, Antenna.BS_ID, center, None, grid)
    grid.add_antenna(bs)
    #bs2 = AntennaMc(0, Antenna.BS_ID, center, None, grid)
    bs2 = Antenna(0, Antenna.BS_ID, center, None, grid2)
    grid2.add_antenna(bs2)

    #Cluster
    cluster = Cluster(1, [1050, 1050], grid)
    grid.add_cluster(cluster)
    cluster2 = Cluster(1, [1050, 1050], grid2)
    grid2.add_cluster(cluster2)

    #RRHs
    rrh = Antenna(1, Antenna.RRH_ID, [1040, 1040], None, grid)
    grid.add_antenna(rrh)
    #rrh = AntennaMc(1, Antenna.RRH_ID, [1040, 1040], None, grid2)
    rrh2 = Antenna(1, Antenna.RRH_ID, [1040, 1040], None, grid2)
    grid2.add_antenna(rrh2)

    #Users
    u1 = User(0, [880, 880], None, grid, User.HIGH_RATE_USER)
    grid.add_user(u1)

    u2 = User(1, [1045, 1045], None, grid, User.LOW_RATE_USER)
    grid.add_user(u2)

    u1 = User(0, [880, 880], None, grid2, User.HIGH_RATE_USER)
    grid2.add_user(u1)

    u2 = User(1, [1045, 1045], None, grid2, User.LOW_RATE_USER)
    grid2.add_user(u2)

#    do_fixedpower(1, grid2)

 #   do_greedy(1, grid2)

  #  do_mc(1, grid, 1, 1)

    return grid

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
                #print("x: " + str(x) + " y: " + str(y) + " r: " + str(r))
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
                #print p
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
            u3 = User(j, p_users[j], None, grids[2], user_type)
            grids[2].add_user(u3)


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
                    #print "rest"
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
        cluster3 = Cluster(l+1, p_clusters[l], grids[2])
        grids[2].add_cluster(cluster3)


    for t in range(0, len(p_antennas)):
        rrh1 = Antenna(t+1, Antenna.RRH_ID, p_antennas[t], None, grids[0])
        grids[0].add_antenna(rrh1)
        rrh2 = Antenna(t+1, Antenna.RRH_ID, p_antennas[t], None, grids[1])
        grids[1].add_antenna(rrh2)
        rrh3 = Antenna(t+1, Antenna.RRH_ID, p_antennas[t], None, grids[2])
        grids[2].add_antenna(rrh3)


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

    bs1 = Antenna(0, Antenna.BS_ID, center, None, grids[0])
    grids[0].add_antenna(bs1)

    bs2 = Antenna(0, Antenna.BS_ID, center, None, grids[1])
    grids[1].add_antenna(bs2)

    bs3 = Antenna(0, Antenna.BS_ID, center, None, grids[2])
    grids[2].add_antenna(bs3)

    #Others
    for i in range (0, n_bs-1):
        v = (2 * i) + 1
        #It is not cool initiazile variables in loops...
        #But it only works like this :(
        p_antenna = [None] * 2
        p_antenna[0] = center[0] + radius * math.cos(v*math.pi/6)
        p_antenna[1] = center[1] + radius * math.sin(v*math.pi/6)
        macrocells_center.append(p_antenna)

        bs1 = Antenna(i+1, Antenna.BS_ID, p_antenna, None, grids[0])
        grids[0].add_antenna(bs1)

        bs2 = Antenna(i+1, Antenna.BS_ID, p_antenna, None, grids[1])
        grids[1].add_antenna(bs2)

        bs3 = Antenna(i+1, Antenna.BS_ID, p_antenna, None, grids[2])
        grids[2].add_antenna(bs3)

########################################

