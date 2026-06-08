from numpy import array, ones, tile, argwhere
from collections import Counter, defaultdict
from core.AddSpecies import AddSpecies
from importlib import import_module
from MCMv331.MCMv331_K import MCMv331_K
from MCMv331.MCMv331_J import MCMv331_J
from CB05.CB05_J import CB05_J
from CB05.CB05_K import CB05_K
# from CB05 import CB05_AllRxns
from warnings import warn


# function [Cnames,Rnames,k,f,iG,iRO2,jcorr,jcorr_all,InitializeChemistry(Met,ChemFiles,ModelOptions,FirstCall)
# Generates parameters for calculating time rate of change of chemical species
# using the dydt_eval function
# input:
# Met: a structure containing the following fields:
# T: temperature, K
# P: pressure, mbar
# M: number density, molec/cm3
# RH: relative humidity, %
# H2O: water conc, molec/cm3
# SZA: solar zenith angle, degrees
# jcorr: correction factor for MCM j-values
# jcorr_all: (optional) array of correction factors for all J-values, Generated as an output
# on first call to this function
# Jx: Any photolysis rates (J values) to be replaced. The name should be the same as that of
# the MCM J-value (e.g., J4 for NO2 photolysis). One row for each J-value. units of /s
# ChemFiles: a cell array containing the names of all sub-mechanism scripts
# The first cell is assumed to be a function or script to create generic rate
# constants for a given mechanism (or it can be empty)
# The second cell is assuemd to be a function or script to create J-values for a given
# mechanism (or it can be empty)
# ModelOptions: a structure containing various options. For more info, see ModelCore comments
# firstcall: a flag to let function know whether or not it is being called for the first time
#
# output:
# Cnames: cell array of species names
# Rnames: cell array of reaction names
# k: matrix of rate constants, dimensions are length(T) x length(Rnames)
# f: sparse stoichiometric coefficient matrix, used in dydt_eval to calculate dydt for each species
# dimensions are length(nRx) x #ofspecies
# iG: 2-column vector containing indices of reactants for each reaction
# iRO2: 1-column index of RO2 species locations
# jcorr: generic scaling factor for un-constrained j-values
# jcorr_all: matrix of scaling factors for all J-values
#
# 20120713 GMW
# 20121022 GMW Modified for UWCMv2.2 to accomodate Met input as structure
# 20140108 GMW Added minor hack for CB05 rate constants
# 20150604 GMW Major modifications for WUCMv3:
# - Added code to bring in generic K and J rate constant scripts through ChemFiles
# - Added code to scale non-constrained J-values multiple ways (with a constant scalar)
# with a constrained J-values, or with the average of serveral constrained J-values)
# - Added outputs/inputs jcorr and jcorr_all, which will allow scaling of J-values in
# SolarCyle mode
# Added code to check for duplicate reactions (based on Rnames)
# 20150913 GMW Added line in j-correction code to set jcorr to 1 if SZA>=90
# This prevents issues when feeding in nighttime j-values data
# 20160304 GMW Modified to accept J, K function outputs as structures


# 此脚本的主要上面的英文已经解释得较为详细，主要来源于matlab版本的F0AM_ModelCore里的英文注释；该注释对一些小的地方进行解释，
# 如同F0AM_ModelCore2中所说，该脚本主要用于初始化化学机理，不处理监测物种浓度
# 在F0AM_ModelCore模型与OBM模型(当然，后者是对前者的包装)中，存在两个较为特殊的模型物种 "ONE" 与 "RO2"。前者用于补位，由于
# 模型处理的是二级反应(有两个反应物的反应)，但化学机理中存在一些一级反应(如光解反应)，这时候就添加 "ONE"对其进行补位，其在反应中
# 浓度一直为1；而RO2表征了所有RO2物质的浓度和(没有啥特别实际的意义，F0AM_ModelCore如此，应该把这个冗余的给删了)
# 对于光解速率的校正：1，先计算模型中自带的光解速率矩阵jval，再构造一个全局光解速率校正系数矩阵jcorr_all，判断Met中是否输入了光解速率，
# 如果输入了，修正相应部分的jcorr_all；将没有输入的光解速率的部分的jcorr_all用jcorr替代。由此可以看出可以精细化控制光解速率
# k，f，iG是比较重要的参数，k表示的是n行(时间)，m列(反应个数)的反应速率常数矩阵；f为m行，k列(机理中的k个物质)的反应系数稀疏矩阵；
# iG为m行，2列的反应物位置矩阵。这里的位置表示的是Cnames中所有物质的排列，这也等于f中的k列的排列顺序。k与iG中的m的排列由Rnames决定


def InitializeChemistry(Met, ChemFiles, *firstCall):
    Mnames = Met.keys()  # Met中气象参数的名称
    jcorr = Met["jcorr"]  # 光解速率校正系数
    # T = array(Met['T'])
    SZA = array(Met['SZA'])
    # nRx = 18000 #number of reactions (try to over-guess)
    # nSp = 5900 #number of species (try to over-guess)
    # nIc = len(Met["T"]) #number of initial conditions

    # fstr=[] #horizontal string for concatenating coefficient (f) vectors#no need in Python code
    # Rnames=[]  # np.empty(nRx) #reaction name
    # k=np.zeros((nIc,nRx)) #reaction rate constant matrix
    # Gstr=[]#np.empty((nRx,2)) #collect reactant names
    # Cnames=[]  # np.empty(nSp) #species names
    # RO2names=[]  # np.empty(nSp) #RO2 names

    SpeciesToAdd = ['ONE', 'RO2']  # Placeholder species, seems no need in Python
    Cnames, RO2names = AddSpecies(SpeciesToAdd)  # 添加物种到Cnames，RO2names

    if len(ChemFiles[0]) != 0:  # 计算一些重要的反应速率常数k值
        K = eval(ChemFiles[0])  # very dangerous syntax  # K={'':,}
    if len(ChemFiles[1]) != 0:  # 计算光解速率j值
        J = eval(ChemFiles[1])  # very dangerous syntax  # J={'':,}
        jval = array(list(J.values())).T  # after python3.6 dict is ordered!!! #jval.shape -> (x,len(J))
        Jnames = list(J.keys())
        if firstCall:  # 这个判断的主要作用是通过jcorr与输入Met中的光解速率对计算得到的j值进行校正
            jcorr_all = ones(jval.shape)  # if len(jval.shape==2) else np.ones([jval.shape[0],1])
            sec = list(set(Jnames).intersection(set(Mnames)))  # 判断Met中有哪些光解速率需要去替换j中的
            loc = [Jnames.index(i) for i in sec]  # 判断j中位置
            not_loc = set(range(len(Jnames))).difference(set(loc))
            if len(sec) != 0:  # 修改全局光解速率校正系数
                jcorr_all[:, loc] = array([Met[i] for i in sec]) / jval[:, loc]
                jcorr_all[jval == 0] = 1
                jcorr_all[argwhere(SZA >= 90)[:, 0]] = 1
            if isinstance(jcorr, str) or isinstance(jcorr, list):  # 看着有点怪，这个判断
                if isinstance(jcorr, str):
                    jcorr = [jcorr]
                tem = [Jnames.index(i) for i in jcorr]
                if len(tem) == 0:
                    raise ValueError("InitializeChemistry: one or more jcorr J-values not found in Met!")
                jcorr = jcorr_all[:, tem].mean(axis=1).reshape(-1, 1)  # jcorr.shape -> (x, 1)
            jcorr_all[:, list(not_loc)] = tile(jcorr, [1, len(not_loc)])
        jval = jcorr_all * jval  # 校正后光解速率
        J = {i: j for i, j in zip(Jnames, jval.T)}
    for file in ChemFiles[2:]:  # 调用化学机理模块获取Cnames，Rnames，k，f等
        try:
            if "mcm" in file:
                CM = import_module(f"MCMv331.{file}")
            if "CB05" in file:
                CM = import_module(f"CB05.{file}")
        except:
            warn("InitializeChemistry: import_module execute failed")
        if "CM" not in dir():
            CM = import_module("CB05.CB05_AllRxns")
        SpeciesToAdd = CM.get_SpeciesToAdd()
        RO2ToAdd = CM.get_RO2ToAdd()
        Cnames, RO2names = AddSpecies(SpeciesToAdd, Cnames, RO2names, RO2ToAdd)
        Rnames = CM.get_Rnames()
        k = CM.calculate_k(K, J, Met, len(Rnames))  # k.shape -> (x,len(Rnames)  # 计算k
        f = CM.calculate_f(Cnames, len(Rnames))  # return a sparse matrix#shape -> (nRx,nSp) # 计算f
        Gstr = CM.get_Gnames()

    iRO2 = [Cnames.index(i) for i in set(RO2names).intersection(set(Cnames))]  # 所有RO2自由基位置
    iG = array([[Cnames.index(i) if i in Cnames else 0 for i in j] for j in Gstr])  # 所有反应物的位置，二维矩阵

    if len(firstCall) == 0 or firstCall:  # 看是否有重复的反应式存在，对于输出没有啥影响
        repRx = [i for i, j in dict(Counter(Rnames)).items() if j > 1]  # filter further by rate constants
        loc = defaultdict(list)
        for i, value in enumerate(Rnames):
            if value in repRx:
                loc[value].append(i)
        for i, value in enumerate(loc.values()):
            if len(set(k[:, value].sum(axis=0).tolist())) != len(value):
                warn(f"CAUTION: Potential duplicate reactions found: {i}", Warning)

    return (Cnames, Rnames, k, f, iG, iRO2, jcorr, jcorr_all)
