from numpy import ones, sum, ndarray
from tool.meter import meter


# function dydt=dydt_eval(t,conc,param)
# evaluates chemical rates
# Note that, below, nSp=number of species, nRx=number of reactions, nZ=number of box
# input:
# t:current integration time
# conc:matrix of species concentrations in molec/cm3, shape -> (nZ,nSp)
# param:
# k:matrix of rate constants for reation/photolysis/deposition/emission, shape -> (nZ,nRx)
# f:SPARSE matrix of species coefficients for each reaction, shape -> (nRx,nSp)
# iG:index for species to be multiple for each reaction, shape -> (nRx,2)
# iRO2:index to identify RO2 species
# kdil:dilution rate constant(/s). If this is 0, dilution is ignored
# conc_bkgd:background concentrations, used for dilution
# IntTime:total integration time, used to calculate % complete
# Verbose:set to 1 to include "% complete" display

# output
# dydt:matrix of rate of change of speices, shape -> (nZ,nSp)


def dydt_eval(t, conc: ndarray, param: list):
    # 对于普通化学机理，需要考虑到隐函数常微分方程组及其雅可比矩阵的建立
    # dydt_eval函数即返回该常微分方程组
    # Jac_eval函数即返回该常微分方程组的雅可比矩阵
    #
    # 现考虑物质conc=(y1,y2,y3), y=[y1, y2, y3]
    # 及两组反应：y1+y3=y2;y2+y3=y1
    # 由于二级反应，速率分别为：Df1/Dt=k1*y1*y3;Df2/Dt=k2*y2*y3  -> f1=k1*y1*y3*t; f2=k2*y2*y3*t
    # dy/dt = [k1 * y1 * y3, k2 * y2 * y3] @ f = [-k1y1y3 + k2y2y3, k1y1y3 - k2y2y3, -k1y1y3 - k2y2y3]
    # 上则表征了y相对于时间的变化速率的矩阵即dydt_eval
    #
    # 反应速率矩阵相对于所有第一个反应物质的分量: Drates/D1 = [k1 * y3, k2 * y3]
    # 反应速率矩阵相对于所有第二个反应物质的分量: Drates/D2 = [k1 * y1, k2 * y2]
    # 反应速率矩阵相对于y的分量，稀疏矩阵: Drates/Dy = [[k1 * y3, 0, k1 * y1], [0, k2 * y3, k2 * y2]]
    # 雅可比矩阵: Jac=f.T @ Drates/Dy = [[-k1y3,k2y3,-k1y1+k2y2],[k1y3,-k2y3,k1y1-k2y2],[-k1y3,-k2y3,-k1y2-k2y2]]
    # 该矩阵和利用dy/dt计算的结果一致
    # for key, value in param.items():#.*:要求对应行列数相等，和numpy的*一样；*：矩阵乘法，和numpy的@一样
    #    eval(f"{key}={value}")
    k, f, iG, iRO2, iHold, kdil, conc_bkgd, IntTime, Verbose, NOxinfo = param

    conc = conc.reshape(1, -1)  # ODE solver feeds this in as 1 row for each species#shape -> (nZ,nSp)
    # calculations for vectorization of dydt
    m = conc.shape[0]
    if m > 1:
        o = ones((m, 1))
        conc_bkgd = o @ conc_bkgd  # shape -> (m,nSp)
        k = o @ k  # shape -> (m,nRx)
    # CALCULATE RATES
    conc[:, 1] = sum(conc[:, iRO2], axis=1)  # calculate sum of iRO2 species#shape -> (nZ,nSp)
    G = conc[:, iG[:, 0]] * conc[:, iG[:, 1]]  # 1 column for each reaction#shape -> (nZ,nRx)
    rates = k * G  # chemical rates#shape -> (nZ,nRx)
    dydt = rates @ f  # multiply rates for each reactant by coefficients ans sum up#shape -> (nZ,nSp)
    # dilution
    dilrate = -kdil * (conc - conc_bkgd)  # dilution rate#shape -> (nZ,nSp)
    dydt += dilrate  # shape -> (nZ,nSp)
    # experimental code to fix total NOx
    if len(NOxinfo) != 0:  # python不包含静态变量，采用类变量，而python万物皆对象
        if not hasattr(dydt_eval, "tlast") or t == dydt_eval.tlast:
            dydt_eval.tlast = t
        else:
            dt = t - dydt_eval.tlast
            dydt_eval.tlast = t

            iNOx = NOxinfo[0, :]  # index
            cNOx = NOxinfo[1, :]  # constant concentration
            mNOx = conc[:, iNOx]  # model concentration
            nNOx = sum(cNOx) / sum(mNOx, axis=1) @ mNOx  # new NOx concentrations
            dydt[:, iNOx] = (nNOx - mNOx) / dt + dydt[:, iNOx]

        if t == IntTime:  # ready for next step
            del dydt_eval.tlast

    dydt[:, iHold] = 0  # no change for held species
    # dydt = dydt.T#shape -> (nSp,nZ)#??

    if Verbose >= 3:
        meter(IntTime, t, 10)

    return dydt.tolist()[0]
