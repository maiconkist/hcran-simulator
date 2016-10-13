import math
import scipy.spatial
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from antenna import * 

DEBUG = True

def debug_printf(string):
    if DEBUG:
        print(string)

def wait():
    raw_input("Press Enter to continue.")

def list_append(lista, value):
    lista = np.delete(lista, -1)
    lista = np.append(value, lista)
    return lista

def shannon(B, SINR):
    #Shannon Calc
    # B is in hertz
    # the signal and noise_plus_interference powers S and N are measured in watts or volts
    return B * math.log(1 + SINR, 2)

def friis(Pt, Gt, Gr, R, Wl):
   Pr = Pt + Gt + Gr + (20 * math.log(Wl/(4*math.pi*R), 10))
   return Pr

def sinr(P, I, N):
    sinr = P - (abs(I)+N) #dB
    return abs(sinr)

def noise():
    #fixed noise in dBm
    return -90 

def dBm_to_watts(dBm):
    watts = abs(dBm * 0.001258925)
    return watts

def nearest(p1, p_list, idx=0):
    """ Return the closest point to p1 in p_list

    @param p1 Object to check proximity. Must have 'p1.pos' property
    @param p_list List of objects (similar to p1) to check which is the closest one
    @param Index of the 'closest' object. 0 is the closest one, 1 the second closest one, ...
    """
    p_tree = scipy.spatial.KDTree([a.pos for a in p_list])
    return p_list[p_tree.query([p1.pos, ])[1][idx]]


def dist(p1, p2):
    """ Return the distance between p1 and p2

    @param p1 Object. Must have 'obj.pos' property
    @param p2 Object. Must have 'obj.pos' property
    """
    dist = math.sqrt((p1.pos[0] - p2.pos[0]) ** 2 + (p1.pos[1] - p2.pos[1]) ** 2)
    if dist == 0:
        return 0.00001
    else:
        return dist


#def friis( user, antenna ):
#    WAVE_LENGTH = (3/19.0)  #Comprimento de onda considerando uma frequencia de 1.9 GHz
#    GAIN = 0.1              #Representa o ganho das antenas = -5 dB
#    distance = dist( user, antenna )
#    #Friis -> power transmnited in watts
#    power_received = ( math.pow( 10, ( antenna.power/10.0 ) ) * GAIN * math.pow( ( WAVE_LENGTH/(4 * math.pi * distance ) ), 2 ) )
#
#    return power_received


def sum_coll(lista, x):
    soma = 0
    for y in range (0,len(lista)):
        soma += lista[y][x]

    return soma

def path_loss(ue, antenna):
    result = 0
    if (antenna.type == antenna.BS_ID):
        result = 31.5 + 40.0 * math.log(dist(ue, antenna))
    else:
        result = 31.5 + 35.0 * math.log(dist(ue, antenna))
    return result

def dbm_to_mw(dbm):
    return 1.0 * math.pow(10,dbm/10.0)

def mw_to_dbm(mw):
    return 10.0 * math.log(mw,10)

def snr_to_bit(snr):
    if snr <= 6.0:
        return 1
    elif snr <= 9.4:
        return 2
    elif snr <= 16.24:
        return 4
    else:
        return 6

def bandwidth_to_rb(band):
    if band == 1.4:
        return 6
    elif band == 3:
        return 15
    elif band == 5:
        return 25
    elif band == 10:
        return 50
    elif band == 15:
        return 75
    elif band == 20:
        return 100
    else:
        return 100

#build list of antennas that are in the same coverage area
def build_list_antennas_in_same_coverage_area( rrh_list ):
    if len( rrh_list ):
        rrh_tree = scipy.spatial.KDTree( [ ( rrh.x, rrh.y ) for rrh in rrh_list ] )
    else:
        rrh_tree = None

    data = rrh_tree.query_ball_tree( rrh_tree, rrh_list[0].RRH_RADIUS * 2 )

    for rrh_index, obj in enumerate( rrh_tree.data ):
        rrh = rrh_list[ rrh_index ]
        rrh.antenna_in_range = []

        for i in data[ rrh_index ]:
            antenna = rrh_list[ i ]

            if rrh != antenna:
                rrh.add_antenna_in_range( antenna )

        #if not 0 in rrh.list_antennas:
            #rrh.list_antennas.append( 0 )

def build_list_users_in_antenna_coverage_area( user_list, rrh_list ):
    user_tree = scipy.spatial.KDTree( [ ( user.x, user.y ) for user in user_list ] )
    if len( rrh_list ):
        rrh_tree = scipy.spatial.KDTree( [ ( rrh.x, rrh.y ) for rrh in rrh_list ] )
    else:
        rrh_tree = None

    data = user_tree.query_ball_tree( rrh_tree, rrh_list[0].RRH_RADIUS*999 ) #para cada usuario as antenas curjo o sinal e recebido pelo usuario

    for user_index, obj in enumerate( user_tree.data ):
        user = user_list[ user_index ]
        user.antenna_in_range = []
        user.list_antennas = []
        user.list_antennas.append( 0 )

        for i in data[ user_index ]:
            antenna = rrh_list[ i ]
            antenna.add_user_in_range( user )
            user.add_antenna_in_range( antenna )
            #associa usuarios e antenas

def build_traffic_user( user_list ):
    #generates demand rate for UEs according to Poisson distribution
    data = np.random.poisson( user_list[0].TX_REQUEST, len( user_list ) )

    total_request_ue = 0
    for pos, ue in enumerate( user_list ):
        ue.request = data[ pos ]
        total_request_ue += ue.request


def plot_grid( grid ):

    fig = plt.figure()
    ax = fig.add_subplot(111)
    fig.subplots_adjust(top=0.85)
    x = []
    y = []
    colors = []
    area = []

    for i, ue in enumerate( grid._user ):
        x.append(ue.x)
        y.append(ue.y)
        #ax.text(ue.x-25, ue.y-35, 'UE'+str(ue._id))
        colors.append('#1214a9')
        area.append(np.pi * 1**2)

        if ue._connected_antenna != None:
            ax.arrow(ue.x, ue.y, ue._connected_antenna.x-ue.x, ue._connected_antenna.y-ue.y, head_width=10, head_length=10, fc='k', ec='k')

    for i, cluster in enumerate(grid._clusters):
        x.append(cluster.x)
        y.append(cluster.y)
        colors.append('#FF0000')
        area.append(np.pi * 2**2)

    for i, rrh in enumerate( grid._antennas ):
        if rrh.type == rrh.BS_ID:
            #colors.append('#ee1313')
            #area.append(np.pi * 7**2)
            ax.add_patch(patches.RegularPolygon(
                    (rrh.x,rrh.y),
                    3,
                    10,
                    fill=False )
                )

            #Add Hexagon
            ax.add_patch(patches.RegularPolygon(
                    (rrh.x,rrh.y),
                    6,
                    290, #Chutei e funcinou! :D
                    fill=False,
                    orientation=math.pi/2)
                )
            #Add Text
            #ax.text(rrh.x-25, rrh.y-60, 'BS'+str(rrh._id))
        elif rrh.type == rrh.RRH_ID:
            x.append(rrh.x)
            y.append(rrh.y)
            #colors.append('#7abf57')
            colors.append('#FFFFFF')
            area.append(np.pi * 2**2)
            #ax.text(rrh.x-35, rrh.y-12, 'RRH'+str(rrh._id))

    plt.scatter(x, y, s=area, c=colors, alpha=0.5)
    plt.ylim([0,grid.size[0]])
    plt.xlim([0,grid.size[1]])
    plt.show()

