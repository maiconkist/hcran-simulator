from ra_greedy import *
from antenna import *
from user import *
from bbu import *
from controller import *
from util import *
from grid import *
from cluster import *
import csv
import random
import numpy
import scipy

###############################
#Grid definitions
###############################
DEBUG                   = True
DMACROMACRO             = 500
DMACROUE                = 35
DMACROCLUSTER           = 105
DSMALLUE                = 5
DSMALLSMALL             = 20
DROPRADIUS_MC           = 250
DROPRADIUS_SC           = 500
DROPRADIUS_SC_CLUSTER   = 50
DROPRADIUS_UE_CLUSTER   = 70

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

########################################
def build_scenario(n_bbu, n_bs, n_clusters, n_rrh, n_ue):
    grid = Grid(size=(2000,2000))
    macrocells_center = list()

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)

    for i in range(n_bbu):
        bbu = BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        grid.add_bbu(bbu)

    macrocells(grid, DMACROMACRO, n_bs,  macrocells_center)

    clusters(grid, macrocells_center, n_clusters, n_rrh)

    return grid

########################################
def clusters(grid, macrocells_center, n_clusters, n_antennas):
    count_antennas = 0
    count_clusters = 0
    p_antennas = list()
    reset = 0;

    for i in range(0,len(macrocells_center)):
        print("i = %d" % i)
        for j in range(0, n_clusters):
            print("j = " + str(j))
            #Generate Cluster center
            count_antennas = 1
            count_clusters = count_clusters + 1
            pos = generate_xy(macrocells_center[i],
                    DMACROMACRO*0.425,DMACROCLUSTER)
            cluster = Cluster(count_clusters, pos, grid)
            grid.add_cluster(cluster)

            #Generate antennas
            while (count_antennas <= n_antennas):
            #    if reset <= 1000:
            #    count_antennas = 1
            #    reset = 0
            #    print("count_antennas = %d" % count_antennas)
                p = generate_xy(pos, DROPRADIUS_SC_CLUSTER*0.425, 0)
                count_antennas = count_antennas + 1
                p_antennas.append(p)
            
            for i in range(0, len(p_antennas)):
                rrh = Antenna(i+1, Antenna.RRH_ID, p_antennas[i], None, grid)
                grid.add_antenna(rrh)


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
def macrocells(grid, radius, n_bs, macrocells_center):
    center = numpy.array([grid.size[0]/2, grid.size[1]/2])
    index = 0
    radius = 500

    #Center Antenna
    macrocells_center.append((grid.size[0]/2, grid.size[1]/2))
    bs = Antenna(0, Antenna.BS_ID, center, None, grid)
    grid.add_antenna(bs)

    #Others
    for i in range (0, n_bs-1):
       v = (2 * i) + 1
       #It is not cool initiazile variables in loops...
       #But it only works like this :(
       p_antenna = [None] * 2
       p_antenna[0] = center[0] + radius * math.cos(v*math.pi/6)
       p_antenna[1] = center[1] + radius * math.sin(v*math.pi/6)
       macrocells_center.append(p_antenna)
       bs = Antenna(i+1, Antenna.BS_ID, p_antenna, None, grid)
       grid.add_antenna(bs)

########################################
# Main
########################################
if __name__ == "__main__":
    guloso = Greedy()

    # Trying to create a new file or open one
    f = open('resumo.csv','w')
    f.write('TOTAL_BS,TOTAL_RRH,TOTAL_UE,USED_RRH,USER_NOT_MEET,EE,SE\n')
    f.close()

    bbu = 2 
    bs = 7 
    cluster = 1
    rrh = 5
    ue = 1

    #Build Scenario
    grid = build_scenario(bbu, bs, cluster, rrh, ue)

    util.plot_grid(grid)

