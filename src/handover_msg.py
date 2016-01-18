import matplotlib.pyplot as plt
from antenna import *
from user import *
from bbu import *
from controller import *

from grid import *

from pymobility.models.mobility import random_waypoint

TEST_DURATION=600

rw = None
positions = []

#plt.ion()
#ax = plt.subplot(111)
#line, = ax.plot(range(1000), range(1000), linestyle='', marker='.')

def random_waypoint_strategy(id):
    global positions
    if id == 0:
        positions = next(rw)

#    line.set_data(positions[:,0],positions[:,1])
#    plt.draw()

    return positions[id]


def build_simulation(n_user, n_rrh, n_bbu):
    global rw
    global positions

    # Instantiation order. Must be respected
    # 1- Grid
    # 2- Controller
    # 3- BBUs
    # 4- Antennas
    # 5- Users

    grid = Grid(size=(1000, 1000))

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)

    for b in range(n_bbu):
        grid.add_bbu(
            BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        )

    rw = random_waypoint(n_user, dimensions=grid.size, velocity=(10.0, 100.0), wt_max=1.0)
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
                bw=random.choice([1.4, 3, 5, 10, 15, 20])
            )
        )

    return grid


def dump_res():
    import grid as G
    import re

    tmp_str = ''

    ## calculate good_cap
    #g_list = [i for i in G.Log.logs if "op:antenna_good_cap" in i]
    #good_cap = len(g_list)
    ## avg of good_caps
    #regex = re.compile("per_used:([0-9]*\.[0-9]*)")
    #good_cap_avg_used = sum([float(i) for i in regex.findall("\n".join(g_list))]) / len(g_list)

    ## calculate bad_cap
    #g_list = [i for i in G.Log.logs if "op:antenna_bad_cap" in i]
    #bad_cap = len(g_list)
    ## avg of bad_caps
    #regex = re.compile("per_used:([0-9]*\.[0-9]*)")
    ## obviously is 100%. But who cares? lets do the calculation
    #bad_cap_avg_used = sum([float(i) for i in regex.findall("\n".join(g_list))]) / len(g_list)

    ## build up string
    #tmp_str += str(n_ue) + " "
    #tmp_str += str(n_rrh) + " "
    #tmp_str += str(it) + " "
    #tmp_str += str( sum("op:connection" in l for l in G.Log.logs)) + " "
    #tmp_str += str( sum("op:disconnection" in l for l in G.Log.logs)) + " "
    #tmp_str += str( sum("op:bbu_change" in l for l in G.Log.logs)) + " "
    #tmp_str += str( sum("op:antenna_bw_update" in l for l in G.Log.logs)) + " "
    #tmp_str += str( sum("op:antenna_impossible_cap" in l for l in G.Log.logs)) + " "
    #tmp_str += str(good_cap) + "  "
    #tmp_str += str(bad_cap) + "  "
    #tmp_str += str((good_cap_avg_used + bad_cap_avg_used)/ 2) + " "
    #tmp_str += str(sum([ue.total_tx for ue in grid.users])/(len(grid.users)*TEST_DURATION)) + "\n"
    ## clear all logs
    #G.Log.logs = []

    tmp_str += str(n_ue) + " "
    tmp_str += str(n_rrh) + " "
    tmp_str += str(it) + " "
    tmp_str += str(G.Log.mapper['op:connection']) + " "
    tmp_str += str(G.Log.mapper['op:disconnection']) + " "
    tmp_str += str(G.Log.mapper['op:bbu_change']) + " "
    tmp_str += str(G.Log.mapper['op:antenna_bw_update']) + " "
    tmp_str += str(G.Log.mapper['op:antenna_impossible_cap']) + " "
    tmp_str += str(G.Log.mapper['good_cap_sum']) + " "
    tmp_str += str(G.Log.mapper['bad_cap_sum']) + " "
    tmp_str += str((G.Log.mapper['good_cap_sum'] + G.Log.mapper['bad_cap_sum']) /
                   (G.Log.mapper['good_cap']     + G.Log.mapper['bad_cap'])) + " "
    tmp_str += str(sum([ue.total_tx for ue in grid.users])/(len(grid.users)*TEST_DURATION)) + " "
    tmp_str += str(G.Log.mapper['bad_connection']) + "\n"
    # clear all logs
    G.Log.clear()

    return tmp_str

if __name__ == '__main__':

    res_str = "ue rrh it conn dis bbu_ch bw_update bw_max good_cap bad_cap avg_rbs_used avg_throughput bad_connection\n"
    n_ue = 0
    n_ue = 0
    grid = None

    try:
        for it in range(5):
            for n_ue in (100, 500, 1000 ):
                for n_rrh in (5, 15, 30):
                    grid = build_simulation(n_ue, n_rrh, 2)

                    for step in range(TEST_DURATION):
                        print("-- Simulating step %d/%d" % (step, 600))
                        grid.step(1)

                    res_str += dump_res()
    except Exception as e:
        import traceback
        traceback.print_exc()
        with open("nosdwn_results.txt", "w+") as fd:
            fd.write(res_str)

    with open("nosdwn_results.txt", "w+") as fd:
        fd.write(res_str)
