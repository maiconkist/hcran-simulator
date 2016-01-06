from antenna import *
from user import *
from bbu import *

from grid import *

from pymobility.models.mobility import random_waypoint


rw = None
positions = []

import matplotlib.pyplot as plt
plt.ion()
ax = plt.subplot(111)
line, = ax.plot(range(1000), range(1000), linestyle='', marker='.')


def random_waypoint_strategy( id ):
    global positions
    if id == 0:
        positions = next(rw)

    # simulate for 600 steps
    for xy in positions:
        line.set_data(xy[:,0],xy[:,1])
        plt.draw()

    return positions[id]


def build_simulation(n_user, n_rrh, n_bbu):
    global rw
    global positions

    grid = Grid(size=(1000, 1000))

    for b in range(n_bbu):
        grid.add_bbu(
            BBU(pos=grid.random_pos(), grid=grid)
        )

    rw = random_waypoint(n_user, dimensions=grid.size, velocity=(0.1, 1.0), wt_max=1.0)
    positions = next(rw)
    for u in range(n_user):
        grid.add_user(
            User(
                id=u,
                pos=positions[u],
                moving_strategy=random_waypoint_strategy,
                grid=grid
            )
        )
    for r in range(n_rrh):
        grid.add_antenna(
            Antenna(
                pos=grid.random_pos(),
                radius=30,
                grid=grid,
            )
        )

    return grid

if __name__ == '__main__':
    for n_ue in (50, 100, 500, 1000, ):
        for n_rrh in (5, 10, 15, 20, 25, 30):
            grid = build_simulation(n_ue, n_rrh, 2)

            for step in range(1):
                print("-- Simulating step %d/%d" % (step, 600))
                grid.step(1)

            with open("results/ue_" + str(n_ue) + "_rrh_" + str(n_rrh) + ".txt", "w+" ) as fd:
                import grid as G
                fd.write("\n".join(G.Log.logs))
