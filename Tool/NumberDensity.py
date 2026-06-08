def NumberDensity(P, T):  # 现不需要修改
    # input:
    # P: pressure in mbar (or hPa, if you prefer)
    # T: temperature in K

    # output:
    # M: number density in molecules per cm^3

    Na = 6.022e23
    R = 8.314e4

    M = Na * P / R / T

    return M