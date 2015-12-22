from antenna import *
from user import *
from grid import *
import grid as G

from pymobility.models.mobility import random_waypoint


rw = None
positions = []


def random_waypoint_strategy( id ):
    global positions
    if id == 0:
        positions = next(rw)

    return positions[id]


def build_simulation(n_user, n_rrh):
    global rw
    global positions

    grid = Grid(size = (1000, 1000) )

    rw = random_waypoint(n_user, dimensions=grid.size, velocity=(0.1, 1.0), wt_max=1.0)
    positions = next(rw)

    for u in range(n_user):
        grid.add_user(
            User(
                id = u ,
                pos = positions[u],
                moving_strategy = random_waypoint_strategy,
                grid = grid
            )
        )
    for r in range(n_rrh):
        grid.add_antenna(
            Antenna(
                pos= grid.random_pos(),
                radius = 30,
                grid = grid,
            )
        )

    return grid

if __name__ == '__main__':
    for n_ue in (1, 100, 1000):
        for n_rrh in (100, 500):
            grid = build_simulation(n_ue, n_rrh)

            # simulate for 600 steps
            for step in range(600):
                print("-- Simulating step %d/%d" % (step, 600) )
                grid.step( 1 )

            with open("results/ue_" + str(n_ue) + "_rrh_" + str(n_rrh) + ".txt", "w+" ) as fd:
                fd.write("\n".join( G.Log.logs) )
