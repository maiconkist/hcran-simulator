from ra_greedy import *
from antenna import *
from user import *
from bbu import *
from controller import *
from util import *
from grid import *
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
n_clusters   = 1
n_antennas   = 10
n_ues        = 60
uesindoor    = 0.2
uessmallcell = 2/3

###################################
#Functions
###################################

########################################
def build_scenario(n_bbu, n_bs, n_rrh, n_ue):
    grid = Grid(size=(1500,1500))

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)

    for i in range(n_bbu):
        bbu = BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        grid.add_bbu(bbu)

    macrocells(grid, DMACROMACRO, n_bs)

    return grid

########################################
def macrocells(grid, radius, n_bs):
    center = numpy.array([grid.size[0]/2, grid.size[1]/2])
    macrocells_center = []
    index = 0
    radius = 500

    #Center Antenna
    bs = Antenna(0, Antenna.BS_ID, center, None, grid)
    grid.add_antenna(bs)

    #Others
    for i in range (0, n_bs-1):
       v = (2 * i) + 1
       antenna_x = center[0] + radius * math.cos(v*math.pi/6)
       antenna_y = center[1] + radius * math.sin(v*math.pi/6)
       bs = Antenna(i+1, Antenna.BS_ID, (antenna_x,antenna_y), None, grid)
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
    rrh = 1
    ue = 1

    #Build Scenario
    grid = build_scenario(bbu, bs, rrh, ue)

    util.plot_grid(grid)

