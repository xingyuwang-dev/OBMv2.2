from diffeqpy import ode
from numba import jit


# 该脚本暂时未启用，测试未通过
# 该脚本本意是利用Julia的微分库diffeqpy来替代基于jitcode的求解器，需要提前安装Julia及相关库
# 看过网上一片关于探讨不同语言对于求解微分方方程的速度与精确性的文章，Julia表现可能优于Jitcode

def julia_solver(t, conc, args):
    k, f, iG, iRO2, iHold, kdil, conc_bkgd, _, _, _ = args
    u0 = conc
    tspan = (0., t)
    p = (iG, k, f, iHold, kdil, conc_bkgd)
    numba_f = jit(julia_f)
    prob = ode.ODEProblem(numba_f, u0, tspan, p)
    sol = ode.solve(prob)
    return sol.t, sol.u


def julia_f(du, u, p, t):
    iG, k, f, iHold, kdil, conc_bkgd = p
    G = u[:, iG[:, 0]] * u[:, iG[:, 1]]
    rates = k * G
    du = rates @ f
    dilrate = -kdil * (u - conc_bkgd)
    du += dilrate
    du[iHold] = 0
