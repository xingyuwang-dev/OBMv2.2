from numpy import power, exp, array, cos, tile, pi
from photolysis.J_Hybrid import J_Hybrid


#function J=MCMv331_J(Met,Jmethod)
#calculates generic photolysis rate constants used in MCMv3.3.1 mechanism
#
#INPUTS:
#Met: structure containing required meteorological constraints. Required vars depend on Jmethod
#Met.SZA: solar zenith angle in degrees
#Met.O3col: overhead ozone column, DU
#Met.albedo: surface reflectance, 0-1 (unitless)
#Met.T: temperature, T
#Met.P: pressure, mbar
#Met.LFlux: name of a text file containing an actinic flux spectrum
#
#Jmethod: numeric flag or string specifying how to calculate J-values, Default is "MCM"
#0 or "MCM": sue MCMv3.3.1 parameterization
#Required Met fields: SZA
#1 or "BOTTOMUP": bottom-up integration of cross sections/quantum yields
#See J_BottomUp.m for more info
#Required Met fields: LFlux, T, P
#2 or "HYBIRD": Interpolation of hybrid J-values from TUV solar spectra
#See J_TUVhybrid.m for more info
#Required Met fields: SZA, ALT, O3col, albedo


def MCMv331_J(Met, Jmethod = "MCM"):
    # input:
    # Met={'SZA':,'ALT':,'O3col':,'albedo':,'T':,'P':,'LFlux':}
    # Jmethod: 0-'MCM' or 1-'BOTTOM' or 2-'HYBRID'

    # output:
    # J:{"":}
    Jmethod=str(Jmethod).upper()

    if Jmethod == "0" or Jmethod == "MCM":
        try:
            SZA = array(Met["SZA"])#SZA.shape -> (x,1)
        except:
            raise ValueError("MCMv331_J: InvalidInput, Check SZA in your Met data.")
        Jnames = ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J11", "J12", "J13", "J14", "J15", "J16", "J17",
                  "J18", "J19", "J20", "J21", "J22", "J23", "J24", "J31", "J32", "J33", "J34", "J35", "J41", "J51",
                  "J52", "J53", "J54", "J55", "J56", "J61"]
        I_origin = array([6.073e-5, 4.775e-4, 1.041e-5, 1.165e-2, 2.485e-2, 1.747e-1, 2.644e-3, 9.312e-7, 4.642e-5,
                          6.853e-5, 7.344e-6, 2.879e-5, 2.792e-5, 1.675e-5, 7.914e-5, 1.482e-6, 1.482e-6, 7.6e-4,
                          7.992e-7, 5.804e-6, 2.4246e-6, 2.4246e-6, 6.845e-5, 1.032e-5, 3.802e-5, 1.537e-4, 3.326e-4,
                          7.649e-6, 1.588e-6, 1.907e-6, 2.485e-6, 4.095e-6, 1.135e-5, 4.365e-5, 7.537e-4])
        m_origin = array([1.743, 0.298, 0.723, 0.244, 0.168, 0.155, 0.261, 1.230, 0.762, 0.477, 1.202, 1.067, 0.805,
                          0.805, 0.764, 0.396, 0.396, 0.396, 1.578, 1.092, 0.395, 0.395, 0.130, 0.130, 0.644, 0.170,
                          0.148, 0.682, 1.154, 1.244, 1.196, 1.111, 0.974, 1.089, 0.499])
        n_origin = array([0.474, 0.080, 0.279, 0.267, 0.108, 0.125, 0.288, 0.307, 0.353, 0.323, 0.417, 0.358, 0.338,
                          0.338, 0.364, 0.298, 0.298, 0.298, 0.271, 0.377, 0.296, 0.296, 0.201, 0.201, 0.312, 0.208,
                          0.215, 0.279, 0.318, 0.335, 0.328, 0.316, 0.309, 0.323, 0.266])
        SZAbig = tile(SZA, [1, len(Jnames)])#35 is the J_values total number
        Ibig = tile(I_origin, [SZA.shape[0], 1])
        mbig = tile(m_origin, [SZA.shape[0], 1])
        nbig = tile(n_origin, [SZA.shape[0], 1])
        J_values = Ibig * power(cos(SZAbig * pi / 180), mbig) * exp(-nbig / cos(SZAbig * pi / 180))
        J_values[SZAbig >= 90] = 0
        J = {i: j for i, j in zip(Jnames, J_values.T)}

        return J
    elif Jmethod == "1" or Jmethod == 'BOTTOMUP':

        raise ValueError("J_BottomUp function did not implemented")
    # TODO calculate J=J_BottomUp(LFlux,T,P)
    elif Jmethod == "2" or Jmethod == 'HYBRID':
        J = J_Hybrid(Met["SZA"], Met["ALT"], Met["O3col"], Met["albedo"])

        return J
    else:
        raise SyntaxError(f"MCMv331_J: invalid {Jmethod}. Valid options are \"MCM (0)\", \"BOTTOMUP (1)\", \"HYBRID (3)\"")