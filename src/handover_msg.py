import matplotlib.pyplot as plt
from antenna import *
from user import *
from bbu import *
from controller import *

from grid import *

from pymobility.models.mobility import random_waypoint

LOG_DUMP = "./results/rrh_{rrh}_ue_{ue}_it_{it}.txt"

rw = None
positions = []


# set in the main source
control_network = None

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
    global control_network


    # Instantiation order. Must be respected
    # 1- Grid
    # 2- Controller
    # 3- BBUs
    # 4- Antennas
    # 5- Users

    grid = Grid(size=(1000, 1000))

    cntrl = Controller(grid, control_network=control_network)
    grid.add_controller(cntrl)

    for b in range(n_bbu):
        grid.add_bbu(
            BBU(pos=grid.random_pos(), controller=cntrl, grid=grid)
        )

    rw = random_waypoint(n_user, dimensions=grid.size, velocity=(1.0, 40.0), wt_max=10.0)
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
                id=r,
                type=Antenna.RRH_ID,
                pos=grid.random_pos(),
                radius=30,
                grid=grid,
                bw=random.choice([1.4, 3, 5, 10, 15, 20])
            )
        )

    return grid


def dump_res():
    global control_network

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
    tmp_str += str(G.Log.mapper['bad_connection']) + " "
    tmp_str += str(G.Log.mapper['bad_connection_sum']) + " "
    tmp_str += str((G.Log.mapper['bad_connection_sum'] / G.Log.mapper['bad_connection']) if G.Log.mapper['bad_connection'] > 0 else 0 ) + " "

    # calculate the number of the SUM OF ALL SECONDS IN WHICH RRHS HAD 0 USERS 
    IDLE_PW = 4.3 / 3600.0 # energy consumed per second
    FULL_PW = 6.8 / 3600.0 # energy consumed per second
    if control_network:
        g_list = [i for i in G.Log.logs if "nconnected_ues:" in i]
        regex = re.compile("nconnected_ues:([-+]?\d+[\.]?\d*[eE]?[-+]?\d*)")
        no_users = sum([1 for i in regex.findall("\n".join(g_list)) if int(i) == 0])
        tmp_str += str(no_users) + " "

        # sum energy consumed w/out users +  energy with users
        # 600 is the total test duration
        tmp_str += str(no_users * IDLE_PW + ((n_rrh * TEST_DURATION - no_users) * FULL_PW)) + " "
    else:
        # force no sdwn to have 0 as rrh idle time
        # we do this because both of them dont actually have 'idle mode'. we are just counting from the log when rrh had 0 users
        tmp_str += str(0) + " "
        tmp_str += str(n_rrh * TEST_DURATION * FULL_PW) + " "

    tmp_str += str(G.Log.mapper['op:antenna_idle']) + " "
    tmp_str += str(G.Log.mapper['op:antenna_wake_up']) + "\n"


    with open(LOG_DUMP.format(rrh=n_rrh, ue=n_ue, it=it), "w+") as fd:
        fd.write("\n".join(G.Log.logs))

    # clear all logs
    G.Log.clear()

    return tmp_str

if __name__ == '__main__':
    res_str = "ue rrh it conn dis bbu_ch bw_update bw_max good_cap bad_cap avg_rbs_used avg_throughput bad_connection bad_connection_sum bad_connection_avg rrh_idle_time energy_consumed idle_msg wake_up_msg\n"

    n_ue = 0
    n_rrh = 0
    grid = None

    TEST_DURATION=10
    control_network = True

    try:
        for it in range(5):
            for n_ue in (100, 500, 1000 ):
                for n_rrh in (5, 15, 30):
                    grid = build_simulation(n_ue, n_rrh, 2)

                    for step in range(TEST_DURATION):
                        print("-- Simulating UE:%d, RRH:%d, IT:%d step %d/%d" % (n_ue, n_rrh, it, step, TEST_DURATION))
                        grid.step(1)

                    res_str += dump_res()

    # sdwn_results.txt -> use 'cntrl = Controller(grid, control_network=True)' in build_simulations
    # nosdwn_results.txt -> use 'cntrl = Controller(grid, control_network=False)' in build_simulations
    except Exception as e:
        import traceback
        traceback.print_exc()
        with open("sdwn_results.txt" if control_network else "nosdwn_results.txt", "w+") as fd:
            fd.write(res_str)

    with open("sdwn_results.txt" if control_network else "nosdwn_results.txt", "w+") as fd:
        fd.write(res_str)
