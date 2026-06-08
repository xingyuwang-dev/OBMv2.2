from numpy import exp, log10, array, power  # normally, it is faster than **


# function K=CB05_K(met)
# Calculate generic rate constants for use with the CB05 chemical mechainsm.
#
# INPUTS:
# Met: structure containing the following fields:
# T: temperature, K
# M: number density, molec/cm^3
#
# OUTPUTS:
# K: structure of rate constants. Each is size length(T) x # of rate constants
#
# 20130106 GWM
# 20130317 MM Triple-checked for consistency with CB05 documentation.
# 20160304 GWM Changed output from name/value pair to structure, input to structure
# 20160516 MM Corrected error in exponents for all termolecular reactions (-2 vs 2).
# This was an error in the original documentation.


# 该脚本用于计算K值，K值表示特定反应的反应速率，下面每个函数都经过严格的计算与对照，不需要进行任何修改！！！
# 在计算的时候，会考虑到温度T与1立方厘米分子数M，计算之后将许多的K映射为字典


def K_O3P_NO2(T, M):
    LPL = 2.50e-31 * power(T / 300, -1.8) * exp(-2 / T) * M
    HPL = 2.20e-11 * power(T / 300, -0.7) * exp(-3 / T)
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_O3P_NO(T, M):
    LPL = 9.0e-32 * power(T / 300, -1.5) * M
    HPL = 3.0e-11
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_OH_NO(T, M):
    LPL = 7.00e-31 * power(T / 300, -2.6) * M
    HPL = 3.60e-11 * power(T / 300, -0.1)
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_OH_NO2(T, M):
    LPL = 2.00e-30 * power(T / 300, -3.0) * M
    HPL = 2.5e-11
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_OH_HNO3(T, M):
    K1 = 2.400e-14 * exp(460 / T)
    K3 = 6.50e-34 * exp(1335 / T)
    K4 = 2.7e-17 * exp(2199 / T)
    K2 = (K3 * M) / (1 + K3 * M / K4)
    krx = K1 + K2
    return krx


def K_OH_OLE(T, M):
    LPL = 8.00e-27 * power(T / 300, -3.5) * M
    HPL = 3.00e-11 * power(T / 300, 0)
    krx = (LPL / (1 + LPL / HPL)) * power(0.5, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_OH_ETH(T, M):
    LPL = 1.00e-28 * power(T / 300, -0.8) * M
    HPL = 8.8e-12
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_SO2_OH(T, M):
    LPL = 3e-31 * power(T / 300, -3.3) * M
    HPL = 1.5e-12
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_OH_OH(T, M):
    LPL = 6.9e-31 * power(T / 300, -1.0) * M
    HPL = 2.6e-11
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_OH_CO(T, M):
    LPL = 5.9e-33 * power(T / 300, -1.4) * M
    HPL = 1.1e-12 * power(T / 300, 1.3)
    K_OH_COa = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    LPL = 1.5e-13 * power(T / 300, 0.6)
    HPL = 2.1e9 * power(T / 300, 6.1)
    K_OH_COb = (LPL / (1 + LPL / (HPL / M))) * power(0.6, 1 / (1 + power(log10(LPL / (HPL / M)), 2)))
    krx = K_OH_COb + K_OH_COa
    return krx


def K_NO3_NO2(T, M):
    LPL = 2.0e-30 * power(T / 300, -4.4) * M
    HPL = 1.4e-12 * power(T / 300, -0.7)
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_N2O5(T, M):
    LPL = 1.0e-03 * power(T / 300, -3.5) * exp(-11000 / T) * M
    HPL = 9.7e14 * power(T / 300, 0.1) * exp(-11080 / T)
    krx = (LPL / (1 + LPL / HPL)) * power(0.45, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_HO2_NO2(T, M):
    LPL = 3.0e-31 * power(T / 300, -3.2) * M
    HPL = 4.7e-12
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_PNA(T, M):
    LPL = 4.1e-05 * exp(-10650 / T) * M
    HPL = 4.8e15 * exp(-11170 / T)
    krx = (LPL / (1 + LPL / HPL)) * power(0.6, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_C203_NO2(T, M):
    LPL = 2.7e-28 * power(T / 300, -7.1) * M
    HPL = 1.2e-11 * power(T / 300, -0.9)
    krx = (LPL / (1 + LPL / HPL)) * power(0.3, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_PAN(T, M):
    LPL = 4.90e-3 * exp(-12100 / T) * M
    HPL = 5.4e16 * exp(-13830 / T)
    krx = (LPL / (1 + LPL / HPL)) * power(0.3, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_CXO3_NO2(T, M):
    LPL = 2.7e-28 * power(T / 300, -7.1) * M
    HPL = 1.2e-11 * power(T / 300, -0.9)
    krx = (LPL / (1 + LPL / HPL)) * power(0.3, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def K_PANX(T, M):
    LPL = 4.9e-3 * exp(-12100 / T) * M
    HPL = 5.4e16 * exp(-13830 / T)
    krx = (LPL / (1 + LPL / HPL)) * power(0.3, 1 / (1 + power(log10(LPL / HPL), 2)))
    return krx


def CB05_K(Met: dict):
    # input:
    # Met={'T':,'M':,'H2O':}

    # output:
    # K:rate constants

    try:
        T = array(Met['T']).reshape(1, -1)[0]
        M = array(Met['M']).reshape(1, -1)[0]
    except:
        raise ValueError('MCMv331_K: InvalidInput, Check your Met data.')

    Knames = ["K_O3P_NO2", "K_O3P_NO", "K_OH_NO", "K_OH_NO2", "K_OH_HNO3", "K_OH_OLE",
              "K_OH_ETH", "K_SO2_OH", "K_OH_OH", "K_OH_CO", "K_NO3_NO2", "K_N2O5",
              "K_HO2_NO2", "K_PNA", "K_C2O3_NO2", "K_PAN", "K_CXO3_NO2", "K_PANX"]
    Kvalues = array([K_O3P_NO2(T, M), K_O3P_NO(T, M), K_OH_NO(T, M), K_OH_NO2(T, M), K_OH_HNO3(T, M), K_OH_OLE(T, M),
                     K_OH_ETH(T, M), K_SO2_OH(T, M), K_OH_OH(T, M), K_OH_CO(T, M), K_NO3_NO2(T, M), K_N2O5(T, M),
                     K_HO2_NO2(T, M), K_PNA(T, M), K_C203_NO2(T, M), K_PAN(T, M), K_CXO3_NO2(T, M), K_PANX(T, M)])
    K = {i: j for i, j in zip(Knames, Kvalues)}

    return K
