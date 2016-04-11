#########################################################
# @file     energy_efficient.py
# @author   Gustavo de Araújo
# @date     29 Mar 2016
#########################################################

def k_for_omega1(dr,hr,B0,N0):
    return (dr*hr/B0*N0)

def k_for_omega2(dr,hr,,dm,hm,B0,N0,N):
    pm = p_max / N
    return (dr*hr)/((pm*dm*hm)+(B0*N0))

def c(cnir, p, a, N, M, K, B0):
    result = 0
    for n in range(0, M+N):
        for k in range(0, k):
            result = result + (a[n][k]*B0*math.log(1+(cnir[n][k]*p[n][k])))

    return result

def p(eff, a, p, prc, pbh,  N, M, K):
    result = 0
    for n in range(0, N+M):
        for k in range(0, K):
            result = result + ((a[n][k]*p[n][k]) + prc + pbh)

    return eff*result

def cm(cnir, p, a, N, M, K, B0):
    result = 0
    for t in range(0, T):
        for m in range(0, M):
            result = result + (a[t][m]*B0*math.log(1+(cnir[t][m]*p[t][m])))

    return result

def pm(eff, a, p, prc, pbh,  N, M, K):
    result = 0
    for t in range(0, T):
        for m in range(0, M):
            result = result + ((a[t][m]*p[t][m]) + prc + pbh)

    return eff*result

def y(a, p):
    for l in range(0, L):
        p1 = c(cnir,p, a, N, M, K, B0) * l
        p2 = p(eff, a, p, prc, pbh,  N, M, K) * l
    for h in range(0, H):
        pp1 = cm(cnir, p, a, N, M, K, B0) * h
        pp2 = pm(eff, a, p, prc, pbh,  N, M, K) * h

    return (p1+pp1)/(p2+pp2)

