from numpy import log, exp, zeros


# 通过一系列公式计算湿度，下面两个函数不要改动任意一个地方


def CovertHumidity(T, P, HumidityIn, UnitIn, UnitOut):
    # input:
    # T=np.array([])
    # P=np.array([])
    # Humidity=np.array([])
    # UnitIn=''
    # UnitOut=''

    # output:
    # HumidityOut=np.array([])

    eta = 0.622  # ratio of weights of dry and mosit air
    es = h2o_pvap_calc(T) * 1013 / 760  # saturation vapor pressure, hPa
    R = 8.3145 * 1e6 / 100  # gas constant, cm^3 hPa/mol/K
    Na = 6.022e23  # number density, molec/cm
    M = P * Na / (R * T)

    if UnitIn == 'PartialPressure':
        e = HumidityIn
    elif UnitIn == 'RH':
        e = HumidityIn / 100 * es
    elif UnitIn == 'SpecificHumidity':
        e = (HumidityIn * P) / (eta + (1 - eta) * HumidityIn)
    elif UnitIn == 'MixingRatio':
        e = (HumidityIn * P) / (HumidityIn + eta)
    elif UnitIn == 'NumberDensity':
        e = HumidityIn / M * P
    elif UnitIn == 'DewPoint':
        e = h2o_pvap_calc(HumidityIn) * 1013 / 760
    elif UnitIn == 'VPD':
        e = es - HumidityIn
    else:
        e = zeros(T.shape)

    if UnitOut == 'PartialPressure':
        HumidityOut = e
    elif UnitOut == 'RH':
        HumidityOut = 100 * e / es
    elif UnitOut == 'SpecificHumidity':
        HumidityOut = (e * eta) / (e * eta + P - e)
    elif UnitOut == 'MixingRatio':
        HumidityOut = (e / (P - e)) * eta
    elif UnitOut == 'NumberDensity':
        HumidityOut = e / P * M
    elif UnitOut == 'DewPoint':
        while abs(1 - e / es) > 0.001:
            T = T + 10 * log(e / es)
            es = h2o_pvap_calc(T) * 1013 / 760
        HumidityOut = T
    elif UnitOut == 'VPD':
        HumidityOut = es - e
    else:
        HumidityOut = e

    return HumidityOut


def h2o_pvap_calc(T):
    # input:
    # T=np.array([])

    # output:
    # h2o_pvap=np.array([])

    aSAT = 0.750061683
    bSAT = 6.112
    cSAT = 6816
    dSAT = 5.1309
    T0 = 273.15

    h2o_pvap = aSAT * bSAT * exp(cSAT * (1 / T0 - 1 / T) + dSAT * log(T0 / T))

    return h2o_pvap