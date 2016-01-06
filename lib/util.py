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
