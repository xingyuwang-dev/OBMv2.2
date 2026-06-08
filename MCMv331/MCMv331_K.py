from numpy import power, log10, array, exp


def KFPAN(T, M):
    KC0 = 3.28e-28 * M * power(T / 300, -6.87)
    KCI = 1.125e-11 * power(T / 300, -1.105)
    NC = 0.75 - 1.27 * log10(0.3)
    FC = power(10, log10(0.3) / (1 + power((log10(KC0 / KCI) / NC), 2)))
    result = (KC0 * KCI) * FC / (KC0 + KCI)
    return result


def KBPAN(T, M):
    KD0 = 1.10e-5 * M * exp(-10100 / T)
    KDI = 1.9e17 * exp(-14100 / T)
    NCD = 0.75 - 1.27 * (log10(0.3))
    FD = power(10, log10(0.3) / (1 + power((log10(KD0 / KDI) / NCD), 2)))
    result = (KD0 * KDI) * FD / (KD0 + KDI)
    return result


def KMT01(T, M):
    K10 = 1.0e-31 * M * power(T / 300, -1.6)
    K1I = 5.0e-11 * power(T / 300, -0.3)
    NC1 = 0.75 - 1.27 * (log10(0.85))
    F1 = power(10, log10(0.85) / (1 + power((log10(K10 / K1I) / NC1), 2)))
    result = (K10 * K1I) * F1 / (K10 + K1I)
    return result


def KMT02(T, M):
    K20 = 1.3e-31 * M * power(T / 300, -1.5)
    K2I = 2.3e-11 * power(T / 300, 0.24)
    NC2 = 0.75 - 1.27 * (log10(0.6))
    F2 = power(10, log10(0.6) / (1 + power((log10(K20 / K2I) / NC2), 2)))
    result = (K20 * K2I) * F2 / (K20 + K2I)
    return result


def KMT03(T, M):
    K30 = 3.6e-30 * M * power(T / 300, -4.1)
    K3I = 1.9e-12 * power(T / 300, 0.2)
    NC3 = 0.75 - 1.27 * (log10(0.35))
    F3 = power(10, log10(0.35) / (1 + power((log10(K30 / K3I) / NC3), 2)))
    result = (K30 * K3I) * F3 / (K30 + K3I)
    return result


def KMT04(T, M):
    K40 = 1.3e-3 * M * power(T / 300, -3.5) * exp(-11000 / T)
    K4I = 9.7e14 * power(T / 300, 0.1) * exp(-11080 / T)
    NC4 = 0.75 - 1.27 * (log10(0.35))
    F4 = power(10, log10(0.35) / (1 + power((log10(K40 / K4I) / NC4), 2)))
    result = (K40 * K4I) * F4 / (K40 + K4I)
    return result


def KTM07(T, M):
    K70 = 7.4e-31 * M * power(T / 300, -2.4)
    K7I = 3.3e-11 * power(T / 300, -0.3)
    NC7 = 0.75 - 1.27 * (log10(0.81))
    F7 = power(10, log10(0.81) / (1 + power((log10(K70 / K7I) / NC7), 2)))
    result = (K70 * K7I) * F7 / (K70 + K7I)
    return result


def KTM08(T, M):
    K80 = 3.2e-30 * M * power(T / 300, -4.5)
    K8I = 3e-11
    NC8 = 0.75 - 1.27 * (log10(0.41))
    F8 = power(10, log10(0.41) / (1 + power((log10(K80 / K8I) / NC8), 2)))
    result = (K80 * K8I) * F8 / (K80 + K8I)
    return result


def KTM09(T, M):
    K90 = 1.4e-31 * M * power(T / 300, -3.1)
    K9I = 4.0e-12
    NC9 = 0.75 - 1.27 * (log10(0.4))
    F9 = power(10, log10(0.4) / (1 + power((log10(K90 / K9I) / NC9), 2)))
    result = (K90 * K9I) * F9 / (K90 + K9I)
    return result


def KTM10(T, M):
    K100 = 4.1e-5 * M * exp(-10650 / T)
    K10I = 6.0e15 * exp(-11170 / T)
    NC10 = 0.75 - 1.27 * (log10(0.4))
    F10 = power(10, log10(0.4) / (1 + power((log10(K100 / K10I) / NC10), 2)))
    result = (K100 * K10I) * F10 / (K100 + K10I)
    return result


def KTM11(T, M):
    k1 = 2.4e-14 * exp(460 / T)
    k3 = 6.5e-34 * exp(1335 / T)
    k4 = 2.7e-17 * exp(2199 / T)
    k2 = k3 * M / (1 + k3 * M / k4)
    result = k1 + k2
    return result


def KTM12(T, M):
    K120 = 2.5e-31 * M * power(T / 300, -2.6)
    K12I = 2.0e-12
    NC12 = 0.75 - 1.27 * (log10(0.53))
    F12 = power(10, log10(0.53) / (1 + power((log10(K120 / K12I) / NC12), 2)))
    result = K120 * K12I * F12 / (K120 + K12I)
    return result


def KTM13(T, M):
    K130 = 2.5e-30 * M * power(T / 300, -5.5)
    K13I = 1.8e-11
    NC13 = 0.75 - 1.27 * (log10(0.36))
    F13 = power(10, log10(0.36) / (1 + power((log10(K130 / K13I) / NC13), 2)))
    result = K130 * K13I * F13 / (K130 + K13I)
    return result


def KTM14(T, M):
    K140 = 9.0e-5 * M * exp(-9690 / T)
    K14I = 1.1e16 * exp(-10560 / T)
    NC14 = 0.75 - 1.27 * (log10(0.36))
    F14 = power(10, log10(0.36) / (1 + power((log10(K140 / K14I) / NC14), 2)))
    result = (K140 * K14I) * F14 / (K140 + K14I)
    return result


def KTM15(T, M):
    K150 = 8.6e-29 * M * power(T / 300, -3.1)
    K15I = 9.0e-12 * power(T / 300, -0.85)
    NC15 = 0.75 - 1.27 * (log10(0.48))
    F15 = power(10, log10(0.48) / (1 + power((log10(K150 / K15I) / NC15), 2)))
    result = (K150 * K15I) * F15 / (K150 + K15I)
    return result


def KTM16(T, M):
    K160 = 8e-27 * M * power(T / 300, -3.5)
    K16I = 3.0e-11 * power(T / 300, -1)
    NC16 = 0.75 - 1.27 * (log10(0.5))
    F16 = power(10, log10(0.5) / (1 + power((log10(K160 / K16I) / NC16), 2)))
    result = (K160 * K16I) * F16 / (K160 + K16I)
    return result


def KTM17(T, M):
    K170 = 5.0e-30 * M * power(T / 300, -1.5)
    K17I = 1.0e-12
    tem = 0.17 * exp(-51 / T) + exp(-T / 204)
    NC17 = 0.75 - 1.27 * (log10(tem))
    F17 = power(10, log10(tem) / (1 + power((log10(K170 / K17I) / NC17), 2)))
    result = (K170 * K17I) * F17 / (K170 + K17I)
    return result


def KBPPN(T, M):
    KPPN0 = 1.7e-3 * M * exp(-11280 / T)
    KPPNI = 8.3e16 * exp(-13940 / T)
    NCPPN = 0.75 - 1.27 * (log10(0.36))
    FPPN = power(10, log10(0.36) / (1 + power((log10(KPPN0 / KPPNI) / NCPPN), 2)))
    result = (KPPN0 * KPPNI) * FPPN / (KPPN0 + KPPNI)
    return result


def MCMv331_K(Met):
    # input:
    # Met={'T':,'M':,'H2O':}

    # output:
    # K:rate constants

    try:
        T = array(Met['T']).reshape(1, -1)[0]
        M = array(Met['M']).reshape(1, -1)[0]
        H2O = array(Met['H2O']).reshape(1, -1)[0]
    except:
        raise ValueError('MCMv331_K: InvalidInput, Check your Met data.')

    Knames = ['KRO2NO', 'KRO2HO2', 'KAPHO2', 'KAPNO', 'KRO2NO3', 'KNO3AL', 'KDEC','KROPRIM', 'KROSEC', 'KCH3O2',
              'K298CH3O2', 'K14ISOM1', 'KFPAN', 'KBPAN','KMT01', 'KMT02', 'KMT03', 'KMT04', 'KMT05', 'KMT06',
              'KMT07', 'KMT08','KMT09', 'KMT10', 'KMT11', 'KMT12', 'KMT13', 'KMT14', 'KMT15', 'KMT16', 'KMT17','KMT18', 'KBPPN']
    krx = [2.7e-12 * exp(360 / T), 2.91e-13 * exp(1300 / T), 5.2e-13 * exp(980 / T),
           7.5e-12 * exp(290 / T), array([2.3e-12]*len(T)), 1.4e-12 * exp(-1860 / T),
           array([1e6]*len(T)), 2.5e-14 * exp(-300 / T), 2.5e-14 * exp(-300 / T),
           1.03e-13 * exp(365 / T), array([3.5e-13]*len(T)), 3e7 * exp(-5300 / T),
           KFPAN(T, M), KBPAN(T, M), KMT01(T, M),
           KMT02(T, M), KMT03(T, M), KMT04(T, M),
           1.44e-13 * (1 + (M / 4.2e19)), 1 + (1.40e-21 * exp(2200 / T) * H2O), KTM07(T, M),
           KTM08(T, M), KTM09(T, M), KTM10(T, M),
           KTM11(T, M), KTM12(T, M), KTM13(T, M),
           KTM14(T, M), KTM15(T, M), KTM16(T, M),
           KTM17(T, M), 9.5e-39 * 0.21 * M * exp(5270 / T) / (1 + 7.5e-29 * 0.21 * M * exp(5610 / T)), KBPPN(T, M)]
    K = {i: j for i, j in zip(Knames, krx)}

    return K