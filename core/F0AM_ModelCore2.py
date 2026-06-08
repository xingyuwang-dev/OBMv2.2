# F0AM_ModelCore(Met, InitConc, ChemFiles, BkgdConc, ModelOptions, *SolarParam):
# S=F0AM_ModelCore(Met,InitConc,ChemFiles,BkgdConc,ModelOptions,*SolorParam)
# Core model code for the Framework for 0-D Atmospheric Modeling (F0AMv3)
# Descended from the university of Washington Chemical Model (UWCM), first beget 20101211 by GMW/JAT
# See ReadMe for description of inputs and outputs
# Transformed from MATLAB code to Python code by puyukeji.cnpowder.com Data Research Group(beget 2022/04/11)
from datetime import datetime
from numpy import tile, zeros, array, sum
from warnings import warn
from core.NumberDensity import NumberDensity
from core.CovertHumidity import CovertHumidity
from core.InitializeChemistry import InitializeChemistry
from core.jit_solver import solver3


# 该模块为精简化的F0AM_ModelCore, 拆分为了两个子模块：1:F0AM_ModelCore_read，2:F0AM_ModelCore_calculate，前者通过
# InitializeChemistry脚本来初始化化学机理，后者利用初始化后的化学机理与监测物质浓度，基于求解器计算浓度变化。
# 拆开的原因是因为前一部分可以拆开，hhh；主要是因为再多进程之前，提前初始化适用于所有情景的化学机理，然后再结合监测浓度，利用多进程
# 加快计算。但其实主要的计算时间消耗在于求解器积分，拆开也能减少一部分文件IO时间。具体效用与提升未测试


def F0AM_ModelCore_read(Met, ChemFiles):
    StartTime = datetime.now()
    if len(Met) == 0:
        raise ValueError('F0AM_ModelCore: InvaildInput, no value in Met')
    if 'RH' not in Met.keys() and 'H2O' not in Met.keys():
        raise ValueError('F0AM_ModelCore: MissingInput, RH or H2O must be specified in Met')
    if 'RH' in Met.keys() and 'H2O' in Met.keys():
        warn('F0AM_ModelCore: UnusedInput, RH and H2O both specified in Met. H2O takes priority')

    Met.update({"H2O": []})  # , 'O3col': 300, 'albedo': 0.1})
    Met = {i: array(j).reshape(-1, 1) for i, j in Met.items()}  # Met[i].shape -> (x,1)
    lExpand = Met["P"].shape[0]
    for key, value in Met.items():
        if isinstance(value, (float, int)) or len(value) == 1:
            Met[key] = tile(Met[key], (lExpand, 1))
    Met.update({'M': NumberDensity(Met['P'], Met['T'])})
    if isinstance(Met['H2O'], (int, float)) or len(Met['H2O']) == 0:
        Met['H2O'] = CovertHumidity(Met['T'], Met['P'], Met['RH'], 'RH', 'NumberDensity')
    # SolarParam = dict.fromkeys(['lat', 'lon', 'alt', 'startTime', 'nDays'], [float('nan')]*lExpand)
    # SolarParam['nDays'] = SolarParam['nDays'][0]
    # SolarParam["startTime"] = tile(SolarParam["startTime"], (1, 6))

    Cnames, _, k, f, iG, iRO2, Met['jcorr'], Met['jcorr_all'] = InitializeChemistry(Met, ChemFiles, 1)
    print(f"READ RUN TIME IS {(datetime.now() - StartTime).seconds} SECONDS")

    return Met["M"], k, f, iG, iRO2, Cnames


def F0AM_ModelCore_calculate(args):  # 为了兼顾多进程，所有参数放在元组
    print('ENTERING MODEL RUN, @(｡･o･)@ @(｡･o･)@ @(｡･o･)@', flush=True)
    InitConc, BkgdConc, ModelOptions, kdil, Met_M, k, f, iG, iRO2, Cnames = args
    HoldFlag = [i[1] for i in InitConc.columns]  # 提取hold参数
    InitConc.columns = [i[0] for i in InitConc.columns]  # 重新设置列名
    Inames, Bnames = list(InitConc.keys()), list(BkgdConc.keys())
    M, N = InitConc.shape[0], len(Cnames)
    InitConc = InitConc.to_dict("list")

    conc_init = zeros((M, N))
    IcutC = set(Inames) & set(Cnames)  # 判断输入物质是否在机理中
    iHold = [Cnames.index(i) for i in IcutC if HoldFlag[Inames.index(i)] == 1]
    for i in IcutC:
        conc_init[:, Cnames.index(i)] = InitConc[i]
    conc_init *= tile(Met_M, (1, N)) * 1e-9
    conc_init[:, 0] = 1  # 将 "ONE" 物种浓度设置为1，详情见InitializeChemistry的注释
    conc_init[:, 1] = sum(conc_init[:, iRO2], axis=1)  # 这里跟RO2有关，详情见InitializeChemistry注释

    iNOx, iO3 = [Cnames.index("NO"), Cnames.index("NO2")], Cnames.index("O3")
    NOxinfo = []

    if 'DEFAULT' in BkgdConc.keys():  # 这一块计算背景浓度
        conc_bkgd = BkgdConc["DEFAULT"] * conc_init / tile(Met_M, (1, N)) * 1e9
    else:
        conc_bkgd = 0 * conc_init
    BcutC = set(Bnames) & set(Cnames)
    for i in BcutC:
        conc_bkgd[:, Cnames.index(i)] = BkgdConc[i]
    conc_bkgd *= tile(Met_M, (1, N)) * 1e-9
    conc_bkgd[:, 0] = 1

    Conc, StepIndex = [], []
    solver = "solver" if sum(iHold) == 0 else "solver2"
    for j in range(ModelOptions['Repeat']):  # 这个循环没有测试过，让叔替你把握
        for i in range(M):  # 这个for循环里面的水很深，不是你能把握得住的
            if ModelOptions['LinkSteps'] and (i > 0 or j > 0):  # 如果不是第一次循环，且LinkSteps参数为1，进行物种浓度替换
                conc_init_step = conc_out[-1, :].T  # carry over end cons from previous step if desired
                conc_init_step[iHold] = conc_init[i, iHold]  # override for Held species
            else:
                conc_init_step = conc_init[i, :].T  # ODE solver needs 1 row for each species
            if i > 0 or j > 0:  # 一个小trick，一个小秘密，一个不知道是否正确的做法
                conc_init_step[iO3] = conc_out[-1, iO3]
            if ModelOptions['FixNOx'] and (i > 0 or j > 0):  # 相比于F0AM_ModelCore，该版本将这个判断放在了LinkSteps判断外
                modelNOx = conc_out[-1, iNOx]
                InitNOx = conc_init[i, iNOx]
                conc_init_step[iNOx] = modelNOx * sum(InitNOx) / sum(modelNOx)  # NOxinfo = iNOx.append(initNOx)
            # DO INTERFATION
            param = [k[i, :], f, iG, iRO2, iHold, array([kdil]), conc_bkgd[i, :], ModelOptions['IntTime'],
                     ModelOptions['Verbose'], NOxinfo]
            t = ModelOptions["IntTime"]
            _, conc_out = solver3(t, conc_init_step, param, solver)
            # _, conc_out = julia_solver(t, conc_init_step, param)
            # options = odeset("Jacobian", @(t,conc_out)Jac_eval(t, conc_out, param))# odeset is a tool to create struct for ode15s()
            # time_out, conc_out = ode15s(@(t,conc_out)dydt_eval(t, conc_out, param), [0,ModelOptions["IntTime"]],
            #                        conc_init_step.T, options)
            Conc.append(conc_out[-1].tolist())
            StepIndex.append(i)

    Conc = array(Conc)
    Conc[Conc < 0] = 0
    Conc[:, 1] = sum(Conc[:, iRO2], axis=1)
    Conc = Conc * 1e9 / tile(Met_M[StepIndex], (1, N))
    Conc[:, 0] = 1
    Conc = {i: j for i, j in zip(Cnames, Conc.T)}

    result = {"Chem": {"k": k}, "Conc": Conc, "Met": {"M": Met_M}}  # 只返回反应速率，物种浓度与Met
    print('ENTERING MODEL END, ٩(͡๏̯͡๏)۶ ^_~ ٩(͡๏̯͡๏)۶ ^_~ ٩(͡๏̯͡๏)۶ ^_~', flush=True)

    return result
