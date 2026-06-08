from numpy import ones, array  # ones：全1数组，array，数组初始化
from photolysis.J_Hybrid import J_Hybrid_new  # 导入J_Hybrid_new函数
from MCMv331.MCMv331_J import MCMv331_J  # 导入 MCMv331_J函数


#def CB05_J(Met,Jmethod)->J:
#Calculates photolysis frequencies for CB05
#
#INPUTS:
#Met: structure containing required meteorological constrains, Require vars depend on Jmethod
#  Met.SZA: solar zenith angle in degree
#  Met.ALT: altitude, meters
#  Met.O3col: overhead zone column, DU
#  Met.albedo: surface reflecance,0-1 (unitless)
#  Met.P: pressure, mbar
#  Met.LFlux: name of a text file containing an actinic flux spectrum
#
#JMthod: numeric flag or string specifying how to calculate J_value. Default is "MCM".
#  0 or "MCM": use MCM3.3.1 parameterization. some reactions are not included in MCM. For these, "HYBRID" values are used.
#          required Met fields: SZA
#  1 or "BOTTOM": bottom-up integration of cross sections/quantum yields.
#          see J BottomUp.m for more info.
#          required Met fileds: LFlux,T,P
#  2 or "HYBRID": interpolation of hybrid J-value from TUV solar spectra
#          see J_TUVhybrid.m for more info.
#          required Met fields: SZA,ALT,O3col,albedo
#
#OUTPUTS:
#J: structure of J-values.
#
#20150618 GMW
#20160131 GMW Minor change to names for HCHO to match CB05 doc.
#20160304 GMW Changed output from name/value pairs to structure, added Jmethod.


# 上面英文的脚本是来源于matlab的F0AM_Model，便于开发人员对照原有m文件进行修改；
# 该脚本主要用来计算光解速率，接受Met参数，与计算光解速率方法的Jmethod。当计算
# 方法为MCM与HYBRID时，调用photolysis下的J_Hybrid.py方法进行计算，当为BOTTOMUP
# 调用phtolysis下的J_BottomUp方法，但由于实现方法过于复杂，因此现不考虑该方法


def CB05_J(Met: dict, Jmethod="MCM"):
    Jmethod=str(Jmethod).upper()

    try:  # 读取Met下的albedo，SZA，ALT，O3col等变量
        #T = array(Met["T"])
        #P = array(Met["P"])
        #LFlux = Met["LFlux"]
        albedo = Met["albedo"]
        SZA = array(Met["SZA"])
        ALT = array(Met["ALT"])
        O3col = array((Met["O3col"]))
    except:
        raise KeyError('CB05_J: InvalidInput, Check Met data.')

    if Jmethod == "0" or Jmethod == "MCM":  # 如果采用MCM方法，忽略Met的参数，采用默认值计算逛街速率
        Jmcm = MCMv331_J(Met, "MCM")
        # also need hybrid values for non-MCM species
        # override Met inputs to match hibrid and MCM J's (See Fig.2 in description paper)

        ALT = ones(SZA.shape)*500 #meters
        O3col = ones(SZA.shape)*350 #DU
        albedo = ones(SZA.shape)*0.01 #unitless
        Jhyb = J_Hybrid_new(SZA, ALT, O3col, albedo)
    elif Jmethod == "1" or Jmethod == "BOTTOMUP":  # 尚未开发
        #TODO Jmcm=J_BottomUp(LFlux,T,P)
        #TODO Jhyb=Jmcm
        raise ValueError("J_BottomUp function did not implemented")
    elif Jmethod == "2" or Jmethod == "HYBRID":  # 如果采用HYBRID方法，利用输入的Met的参数计算光解速率
        Jmcm=J_Hybrid_new(SZA, ALT, O3col, albedo)
        Jhyb=Jmcm
    else:
        raise ValueError(f"MCMv331_J: invalid Jmethod {Jmethod}. Valid options are 'MCM' (0), 'BOTTOMUP' (1), 'HYBRID' (2).")

    J = {"JNO2": Jmcm["J4"], "JNO3_NO": Jmcm["J5"], "JNO3_NO2": Jmcm["J6"],  # 将许多光解速率映射为字典
         "JHNO3": Jmcm["J8"], "JO3P": Jmcm["J2"], "JO1D": Jmcm["J1"],
         "JHONO": Jmcm["J7"], "JH2O2": Jmcm["J3"], "JNTR": Jmcm["J54"],
         "JCOOH": Jmcm["J41"], "JMEPX": Jmcm["J41"], "JCCHO_R": Jmcm["J13"],
         "JC2CHO": Jmcm["J14"], "JHCHO_M": Jmcm["J12"], "JHCHO_R": Jmcm["J11"],
         "JMGLY": Jmcm["J34"], "JN2O5": Jhyb["Jn19"] + Jhyb["Jn20"], "JHO2NO2": Jhyb["Jn21"],
         "JPAN": Jhyb["Jn14"] + Jhyb["Jn15"], "JACRO": Jhyb["Jn11"]}

    return J