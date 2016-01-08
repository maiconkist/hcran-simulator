import math
import scipy.spatial

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
    return math.sqrt((p1.pos[0] - p2.pos[0]) ** 2 + (p1.pos[1] - p2.pos[1]) ** 2)


def snr(ue, antenna, channel=0):
    """
    """
    TX_POWER = 23.0
    NOISE_FLOOR = -90.0
    CENTER_FREQ = 700  # in MHz

    # 23 is the antenna tx power in dbm
    received_power = TX_POWER - (20 * math.log(10, dist(ue, antenna)) + 20*math.log(10, CENTER_FREQ) - 27.55)
    snr = received_power - (NOISE_FLOOR)

    return snr
