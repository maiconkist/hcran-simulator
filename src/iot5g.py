from grid import *
from antenna import Antenna
from controller import *
from bbu import *
from cluster import *
import util

DMACROMACRO             = 500
DMACROUE                = 30
DMACROCLUSTER           = 90
DSMALLUE                = 5
DSMALLSMALL             = 10
DROPRADIUS_MC           = 250
DROPRADIUS_SC           = 500
DROPRADIUS_SC_CLUSTER   = 70
DROPRADIUS_UE_CLUSTER   = 70
DSMALLUE                = 5
MAX_DELTA               = 1
MAX_REP                 = 1
MAX_I                   = 50

TOTAL_SIMULATION_TIME = 86400

def build_scenario(n_bbu, n_bs, n_clusters, n_ue):
    grid = Grid(size=(2000,2000))
    macrocells_center = list()

    cntrl = Controller(grid, control_network=False)
    grid.add_controller(cntrl)

    for i in range(n_bbu):
        rpos = grid.random_pos()
        bbu = BBU(pos=rpos, controller=cntrl, grid=grid)
        grid.add_bbu(bbu)

    macrocells(grid, DMACROMACRO, n_bs,  macrocells_center)
    clusters(grid, macrocells_center, n_clusters)
    users(grid, macrocells_center, n_bs, n_clusters, n_ue)

    return grid

def macrocells(grid, radius, n_bs, macrocells_center):
    center = numpy.array([grid.size[0]/2, grid.size[1]/2])
    index = 0

    #Center Antenna
    macrocells_center.append((grid.size[0]/2, grid.size[1]/2))
    bs = Antenna(0, Antenna.BS_ID, center, None, grid)
    grid.add_antenna(bs)

def clusters(grid, macrocells_center, n_clusters):
    count_clusters = 0
    p_clusters = list()
    reset = 0;

    for i in range(0, len(macrocells_center)):
        count_clusters = 0
        #print("Create macrocells cluster and rhh: " + str(i))

        for l in range (0, n_clusters):
            pos = generate_xy(macrocells_center[i],
                    DMACROMACRO*0.425, DMACROCLUSTER)
            p_clusters.append(pos)

            cluster = Cluster(l+1, p_clusters[l], grid)
            grid.add_cluster(cluster)


def users(grid, macrocells_center, n_bs, n_clusters, n_ue):
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
                cluster = grid._clusters[r]

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
            r = 1#random.randint(0,100)
            if r < 25:
                user_type = User.APP_WEARABLES
            elif r > 26 and r < 50:
                user_type = User.APP_ASSIST_LIVING
            elif r > 51 and r < 75:
                user_type = User.APP_DATA_COLLECTED
            else:
                user_type = User.APP_AUTOMATION
            u = User(j+1, p_users[j], None, grid, user_type)
            grid.add_user(u)

def generate_xy(center, radius, min_distance):
    pos = [None] * 2 
    not_done = True
    while not_done:
        pos[0] = radius * (1 - 2 * random.random()) + center[0]
        pos[1] = radius * (1 - 2 * random.random()) + center[1]
        not_done = euclidian(pos, center) < min_distance

    return pos

def euclidian(a,b):
   return scipy.spatial.distance.euclidean(a,b)

def is_possition_ok(p, vector, min_distance):
    result = True
    if len(vector) != 0:
        for i in range(0, len(vector)):
            d = euclidian(p,vector[i])
            if  (d < min_distance) or (d == 0):
                result = False
    return result

def no_sdn_schedulling(matrix, sensor_list, msg_per_day):
    i = 0
    time = 0
    for m in range (0, msg_per_day):
        for s in sensor_list:
            for i in range(0,ue):
                if matrix[time][i] == 0:
                   matrix[time][i] = s._id
                   break
        time += TOTAL_SIMULATION_TIME / msg_per_day

def verify_collision(matrix):
    total_collisions = 0
    print "Verifica Colisao"
    for t in range  (0,TOTAL_SIMULATION_TIME):
        has_colision = False
        collision_per_time = 0
        for s in range (0,ue):
            if matrix[t][s] != 0:
                #print "["+ str(t)+"] ["+str(s)+"]" + " = " + str(matrix[t][s])
                collision_per_time += 1
            else:
                break
   
        if collision_per_time > 1:
            total_collisions += collision_per_time
    print "Collisions: " + str(total_collisions)


def nosdn_simulation(grid, ue):
    simulation_hour = 0
    matrix = numpy.zeros(shape=(TOTAL_SIMULATION_TIME+1, ue))
    sensors_a = list()
    sensors_b = list()
    sensors_c = list()
    sensors_d = list()

    for sensor in grid._user:
        if sensor._type == User.APP_WEARABLES:
            sensors_a.append(sensor)
        elif sensor._type == User.APP_ASSIST_LIVING:
            sensors_b.append(sensor)
        elif sensor._type == User.APP_DATA_COLLECTED:
            sensors_c.append(sensor)
        else:
            sensors_d.append(sensor)

    print "Sensores A: " + str(len(sensors_a))
    print "Sensores B: " + str(len(sensors_b))
    print "Sensores C: " + str(len(sensors_c))
    print "Sensores D: " + str(len(sensors_d))

    no_sdn_schedulling(matrix, sensors_a, User.APP_MSG_DAY_WEARABLES) 
    no_sdn_schedulling(matrix, sensors_b, User.APP_MSG_DAY_ASSIST_LIVING)
    no_sdn_schedulling(matrix, sensors_c, User.APP_MSG_DAY_DATA_COLLECTED)
    no_sdn_schedulling(matrix, sensors_a, User.APP_MSG_DAY_AUTOMATION)

    #Verifica Retransmisao
    verify_collision(matrix)

def sdn_schedulling(matrix, sensor_list):
    for s in grid._user:
        time = 0
        slot = 0
        for m in range (0, s._msg_per_day):
            bk_time = time
            while matrix[time][slot] != 0:
                time += 1
                if time >= 1:#nx_time:
                    time = bk_time
                    slot += 1
                print "["+ str(time)+"] ["+str(slot)+"]" 
            matrix[time][slot] = s._id
            print "["+ str(time)+"] ["+str(slot)+"]" + " = " + str(matrix[time][slot]) 
            time += TOTAL_SIMULATION_TIME / s._msg_per_day
            nx_time = time + (TOTAL_SIMULATION_TIME / s._msg_per_day)
            

#        for m in range (0, s._msg_per_day):
#            for i in range(0,ue):
#                if matrix[time][i] != 0:
#                    time += 1
#                if time >= nx_time:
#                    i += 1
#            matrix[time][i] = s._id
                #print "["+ str(time)+"] ["+str(i)+"]" + " = " + str(matrix[time][i])
#            time += TOTAL_SIMULATION_TIME / s._msg_per_day

def sdn_siumlation(grid, ue):
    matrix = numpy.zeros(shape=(TOTAL_SIMULATION_TIME+1, ue))

    sdn_schedulling(matrix, grid._user)
    verify_collision(matrix)

if __name__ == "__main__":
    bbu = 1 
    bs = 1
    cluster = 1
    ue = 3

    device_per_rat = ue % 4
    total_transmission = (10*ue) + (8*ue) + (24*ue) + (5*ue)
    print "Total de Transmissoes: " + str(total_transmission)

    grid = build_scenario(bbu, bs, cluster, ue)
    #nosdn_simulation(grid, ue)
    sdn_siumlation(grid, ue)
    #plot_grid(grid)

