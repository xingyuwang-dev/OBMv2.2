from numpy import sum, tile, ndarray, diag_indices_from, concatenate
from scipy.sparse import coo_matrix


# 该脚本已弃用，但能用


def Jac_eval(t, conc: ndarray, param: list):
    # input:

    # output:
    # the Jacobian matrix dF/dy, which has dimension of nSp*nSp

    # for key, value in param.items():
    #    eval(f"{key}={value}")
    k, f, iG, iRO2, iHold, kdil = param[0:6]

    nRx, nSp = f.shape
    conc = conc.reshape(1, -1)  # ODE solver feeds this in as 1 row for each species#shape -> (nZ,nSp)
    # CALCULATE JACOBIAN MATRIX
    conc[:, 1] = sum(conc[:, iRO2], axis=1)  # sum RO2#shape -> (nZ,nSp)
    # partial derivatives for 1st-order reactions
    DratesDy1 = k * conc[:, iG[:, 1]]  # shape -> (1,nRx)
    DratesDy2 = k * conc[:, iG[:, 0]]  # shape -> (1,nRx)
    # distribute derivatives
    i = tile(range(nRx), (1, 2)).reshape(1, -1)[0]  # shape -> (1,2nRx)
    j = concatenate((iG[:, 0], iG[:, 1]), axis=0).reshape(1, -1)[0]  # shape -> (2nRx,)
    v = concatenate((DratesDy1, DratesDy2), axis=1).reshape(1, -1)[0]  # shape -> (1,2nRx)
    DratesDy = coo_matrix((v, (i, j)), shape=(nRx, nSp)).tolil()  # shape -> (nRx,nSp)
    # correct second-order reactions
    i2 = iG[:, 0] == iG[:, 1]
    DratesDy[i2, iG[i2, 0]] *= 2
    Jac = f.T @ DratesDy  # shape -> (nSp,nSp)#sparse matrix
    Jac = Jac.tolil()
    row, col = diag_indices_from(Jac)
    Jac[row[2:], col[2:]] -= kdil  # get diagonal indices
    Jac[iHold, :] = 0  # fixed species

    return Jac.toarray()
