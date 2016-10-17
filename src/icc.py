#!/usr/bin/python
from threeGPP import *
from grid import *
from ra_new_mc import *
from ra_fixedpower import *
from ra_sequentially import *
from ra_locally_optimal import *
from ra_gobal_optimal import *
from ra_randon_mc import *
#from multiprocessing import Process, Queue
#from joblib import Parallel, delayed
import csv
import random
import numpy
import scipy
import multiprocessing
import gc
import time
import sys

MAX_DELTA               = 1
MAX_REP                 = 30
MAX_I                   = 10


def do_new_mc(rep, grid):
    #print "Starting scenario", rep, "with", len(grid.bs_list), "macros for NewMC!"
    newmc = NewMc(rep, MAX_I)
    newmc.run(grid);

def do_random_mc(rep, grid):
    #print "Starting scenario", rep, "with", len(grid.bs_list), "macros for NewMC!"
    ramdommc = RandonMc(rep, MAX_I)
    ramdommc.run(grid);

def do_global_optimal(rep, grid):
    #print "Starting scenario", rep, "with", len(grid.bs_list), "macros for Global Optimal!"
    globaly = GlobalOptimal(rep)
    globaly.run(grid, MAX_I);

def do_locally_optimal(rep, grid):
    #print "Starting scenario", rep, "with", len(grid.bs_list), "macros for Locally Optimal!"
    locallly = LocallyOptimal(rep)
    locallly.run(grid, MAX_I);

def do_fixedpower(rep, grid):
    #print "Starting scenario", rep, "with", len(grid.bs_list), "macros for Fixed Power!"
    fixedpower = FixedPower(rep)
    fixedpower.run(grid, MAX_I);

def do_sequential(rep, grid):
    #print "Starting scenario", rep, "with", len(grid.bs_list), "macros for Sequential!"
    sequential = Sequential(rep)
    sequential.run(grid, MAX_I);

# def do_mc(rep, grid):
#     print "Starting scenario", rep, "with", len(grid.bs_list), "macros for MC!"
#     mc = Mc(rep, MAX_I)
#     mc.run(grid);

# def do_peng(rep, grid):
#     print "Starting scenario", rep, "with", len(grid.bs_list), "macros for Peng!"
#     peng = Peng(rep)
#     peng.run(grid);

# def do_greedy(rep, grid):
#     print "Starting scenario", rep, "with", len(grid.bs_list), "macros for Greedy!"
#     greedy = Greedy(rep)
#     greedy.run(grid, MAX_I);

def processInput(rep, nues):
    bs = 1
    bbu = 2 
    cluster = 2
    rrh = 4
    ue = nues

    grids = build_scenario(bbu, bs, cluster, rrh, ue) 
    #util.plot_grid(grids[0])
    
    #do_locally_optimal(rep, grids[0])

    #do_global_optimal(rep, grids[0])

    #do_sequential(rep, grids[1])

    #do_fixedpower(rep, grids[1])

    do_new_mc(rep, grids[2])

    do_random_mc(rep, grids[2])
    
    del grids
    gc.collect()
    

########################################
# Main
########################################
if __name__ == "__main__":
    # Create a new file to log
    f = open('resumo.csv','a+')
    #f.write('DATA:'+ time.strftime("%Y-%m-%d %H:%M") +'\n')
    #f.write('ALG,CASE,M,S,U,R,I,C,P,EE,MU,FS,T\n')
    f.close()

    #print 'Number of arguments:', len(sys.argv), 'arguments.'
    #print 'Argument List:', str(sys.argv)

    #ues = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100]
    #ues = [15]
    ues = 15
    rep = 0
    if len(sys.argv) > 1:
        rep = int(sys.argv[1])

    if len(sys.argv) > 1:
        ues = int(sys.argv[2])

    processInput(rep, ues)
    
    #print ues
    #num_cores = multiprocessing.cpu_count()
    #for nues in ues:
    #    Parallel(n_jobs=num_cores)(delayed(processInput)(nbs, nues) for nbs in range(0, MAX_REP))

    #grid = build_fixed_scenario()
    #util.plot_grid(grid)
    
            



