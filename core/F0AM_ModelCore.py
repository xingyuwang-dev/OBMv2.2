# F0AM_ModelCore(Met, InitConc, ChemFiles, BkgdConc, ModelOptions, *SolarParam):
# S=F0AM_ModelCore(Met,InitConc,ChemFiles,BkgdConc,ModelOptions,*SolorParam)
# Core model code for the Framework for 0-D Atmospheric Modeling (F0AMv3)
# Descended from the university of Washington Chemical Model (UWCM), first beget 20101211 by GMW/JAT
# See ReadMe for description of inputs and outputs
# Transformed from MATLAB code to Python code by puyukeji.cnpowder.com Data Research Group(beget 2022/04/11)
from tool.CheckDict import CheckDict
from tool.sun_position import sun_position
from datetime import datetime
from os import sep
from os.path import exists, dirname
from numpy import tile, zeros, array, ones, sum, linspace, floor, r_, median, diff
from tool.Check4NanNeg import Check4NanNeg
from warnings import warn
from tool.NumberDensity import NumberDensity
from tool.CovertHumidity import CovertHumidity
from InitializeChemistry import InitializeChemistry
from tool.victory import victory
from tool.ode15s import solver, solver2
from tool.jit_solver import solver3
from json import dumps


# 该模块是F0AM_ModelCore模型的主要部分，为什么写得这么怪的原因是从Matlab改写过来的，很多地方的处理显得很复杂与繁琐。因此现在EKMA模块
# 与RIR实际调用的是精简版的F0AM_ModelCore2模型，省去了繁琐的参数与数据校验工作。因为，外层包装的OBM模型已经做完了这部分工作。该模型
# 接受参数为元组，是为了兼顾多进程的原因！而且模型的输出包含了特别多的内容，包括反应方程式，反应速率，反应物与生成物名称等等。而精简版
# 则只提取OBM模型现需要的参数，如果对于OBM模型输出结果有更多的需要，需要详细阅读此模块然后进行更改。该模型包含了很多莫名奇妙的循环，测试，
# 包装。但现只测试了与现OBM模型有关的部分，没有测试过的部分会详细标注


def F0AM_ModelCore(args):
    Met, InitConc, ChemFiles, BkgdConc, ModelOptions, special, *SolarParam = args#为了兼顾多进程，所有参数放在元组
    StartTime=datetime.now()
    F0AMversion = 'F0AMv3'
    print(f'INITIALIZING {F0AMversion}...')

    F0AM_ModelCore.FirstCall = True if not hasattr(F0AM_ModelCore, "FirstCall") else False  # 这个判断很迷糊，哈哈哈
    if not (not F0AM_ModelCore.FirstCall and special):#判断是否是第一次运行，为了加快速度

        if len(Met) == 0:  # 校验Met中的参数
            raise ValueError('F0AM_ModelCore: InvaildInput, no value in Met')
        if 'RH' not in Met.keys() and 'H2O' not in Met.keys():
            raise ValueError('F0AM_ModelCore: MissingInput, RH or H2O must be specified in Met')
        if 'RH' in Met.keys() and 'H2O' in Met.keys():#METEORLOGY
            warn('F0AM_ModelCore: UnusedInput, RH and H2O both specified in Met. H2O takes priority')

        HoldFlag = [i[1] for i in InitConc.columns]#提取hold参数
        #MODEL OPTIONS

        FieldInfo = {'Verbose': (0, 0), 'EndPointsOnly': (0, 1), 'LinkSteps': (0, 0), 'Repeat': (0, 1), 'SavePath': (0, ''),
                     'TimeStamp': (0, []), 'IntTime': (1, []), 'FixNOx': (0, 0), 'DeclareVictory': (0, 0)}
        ModelOptions = CheckDict(ModelOptions, FieldInfo)#验证并修改ModelOptions参数
        del FieldInfo

        FieldInfo = {'P': (1, []), 'T': (1, []), 'SZA': (0, 0), 'RH': (0, 50), 'H2O': (0, []), 'jcorr': (0, 1),
                     'kdil': (0, 0), 'LFlux': (0, []), 'ALT': (0, 500), 'O3col': (0, 300), 'albedo': (0, 0.1)}
        Met = CheckDict(Met, FieldInfo, 'J')#验证并修改Met参数
        if not isinstance(Met["LFlux"], (int, float)) and len(Met["LFlux"]) == 0:
            Met.pop("LFlux")
        del FieldInfo
        #force vertical arrays
        Met = {i: array(j).reshape(-1, 1) for i, j in Met.items()}#Met[i].shape -> (x,1)#if i not in {"H2O", "jcorr"} else j

        if len(SolarParam) != 0:#未测试该判断语句， 该判断语句似乎跟一个ModelOptions下的SolarFlag参数有关
            SolarFlag = 1
            FieldInfo = {'lat': (1, []), 'lon': (1, []), 'alt': (1, []), 'startTime': (1, []), 'nDays': (1, [])}
            SolarParam = CheckDict(SolarParam[0], FieldInfo)
            del FieldInfo

            sTime = dict(zip(['year', 'month', 'day', 'hour', 'min', 'sec'], SolarParam['startTime']))
            sTime.update({"UTC": 0})
            location = {'longitude': SolarParam['lon'], 'latitude': SolarParam['lat'], 'altitude': SolarParam['alt']}
            sun = sun_position(sTime, location)#zenith and azimuth angles of sun
            sun['zenith'][sun['zenith'] > 90] = 90
            Met.update({'SZA': sun['zenith']})
            del sTime, location, sun

            tem = SolarParam["startTime"]
            SolarParam['startTime'] = (datetime(*SolarParam['startTime']) - datetime(1, 1, 1, 0, 0, 0)).seconds/86400
        else:
            SolarFlag = 0
            SolarParam = dict.fromkeys(['lat', 'lon', 'alt', 'startTime', 'nDays'], float('nan'))

        InitConc.columns = [i[0] for i in InitConc.columns]
        InitConc = InitConc.to_dict("list")
        Met = Check4NanNeg(Met)#检验nan与负值
        InitConc = Check4NanNeg(InitConc)
        BkgdConc = Check4NanNeg(BkgdConc)
        SolarParam = Check4NanNeg(SolarParam, 'nan') if SolarFlag else SolarParam

        PATH, CM = dirname(__file__), ""
        for i, value in enumerate(ChemFiles):#检查是否存在相关的机理脚本
            if not value:
                continue
            if i < 2:
                CM = value[:value.index("_")]
                if 'Met' not in value:#first two inputs should be functions or empty
                    raise ValueError(f'F0AM_ModelCore: Met need to input as a parameter of {value}')

            file = value[:value.index("(")] if i < 2 else value
            if not exists('{1}{2}{3}{2}{0}.py'.format(file, PATH, sep, CM)):
                raise FileExistsError(f'F0AM_ModelCore: {file}.py not found on {PATH}')

        Mnames = Met.keys()  # climate parameter
        Inames = InitConc.keys()  # initial compounds
        Bnames = BkgdConc.keys()  # background compounds
        Snames = SolarParam.keys()  # solar parameter
        #在Python3.6之前字典是无序的，之后是有序的，与放入的顺序一致，key与values顺序对应
        lMet = [len(i) if not isinstance(i, (int, float)) else 1 for i in Met.values()]  # Dangerous syntax! Pay attention!
        lInitConc = [len(i) if not isinstance(i, (int, float)) else 1 for i in InitConc.values()]  # Dangerous syntax! Pay attention!
        lBkgdConc = [len(i) if not isinstance(i, (int, float)) else 1 for i in BkgdConc.values()]  # Dangerous syntax! Pay attention!
        lSolar = [len(i) if not isinstance(i, (int, float)) else 1 for i in SolarParam.values()]  # Dangerous syntax! Pay attention!

        lUnq = list({*lMet, *lInitConc, *lBkgdConc, *lSolar})#这块代码作用是将不同长度的参数扩展长相同长度
        lUnq = [i for i in lUnq if i != 0]
        if len(lUnq) > 2 or (len(lUnq) == 2 and not any(array(lUnq) == 1)):
            raise ValueError(
                'F0AM_ModelCore: Number of constraints is inconsistent. '
                'Check lengths of variables for Met, Init BkgdConc, and SolarParam.')

        if len(lUnq) == 2:
            lExpand = max(lUnq)
            for i, value in enumerate(Mnames):
                if lMet[i] == 1:
                    Met[value] = tile(Met[value], (lExpand, 1))
            for i, value in enumerate(Inames):
                if lInitConc[i] == 1:
                    InitConc[value] = tile(InitConc[value], (1, lExpand))
            for i, value in enumerate(Bnames):
                if lBkgdConc[i] == 1:
                    BkgdConc[value] = tile(BkgdConc[value], (1, lExpand))
            for i, value in enumerate(Snames):
                if lSolar[i] == 1:
                    SolarParam[value] = tile(SolarParam[value], (1, lExpand))
            SolarParam['nDays'] = SolarParam['nDays'][0]
        SolarParam["startTime"] = tile(tem, (1, 6)) if "tem" in dir() else tile(SolarParam["startTime"], (1, 6))
        del lUnq, lMet, lInitConc, lBkgdConc, lSolar#, lExpand

        Met.update({'M': NumberDensity(Met['P'], Met['T'])})#number density, molec/cm^3
        Mnames = Met.keys()
        if isinstance(Met['H2O'], (int, float)) or len(Met['H2O']) == 0:
            Met['H2O'] = CovertHumidity(Met['T'], Met['P'], Met['RH'], 'RH', 'NumberDensity')
        #调用初始化化学机理脚本计算重要的参数
        Cnames, Rnames, k, f, iG, iRO2, Met['jcorr'], Met['jcorr_all'] = InitializeChemistry(Met, ChemFiles, ModelOptions, 1)
        Inames = list(Inames)
        Cnames = list(Cnames)

        if SolarFlag:
            SolarParam["SZAcycle"] = 0
            k = []

        F0AM_ModelCore.Rnames = Rnames  # 将计算得到的中间参数保存为类变量，为什么这么做？因为所有情景这些中间参数都一样，不需要计算多次
        F0AM_ModelCore.Cnames = Cnames
        F0AM_ModelCore.BkgdConc = BkgdConc
        F0AM_ModelCore.Met = Met
        F0AM_ModelCore.k = k
        F0AM_ModelCore.f = f
        F0AM_ModelCore.iG = iG
        F0AM_ModelCore.iRO2 = iRO2
        F0AM_ModelCore.ModelOptions = ModelOptions
        F0AM_ModelCore.Inames = Inames
        F0AM_ModelCore.Mnames = Mnames
        #F0AM_ModelCore.ChemFiles = ChemFiles
        F0AM_ModelCore.SolarParam = SolarParam
        F0AM_ModelCore.HoldFlag = HoldFlag
        F0AM_ModelCore.Bnames = Bnames
        F0AM_ModelCore.SolarFlag = SolarFlag
        F0AM_ModelCore.Snames = Snames

    else:#如果不是第一次运行，读取保存的上一次运行结果
        InitConc.columns = [i[0] for i in InitConc.columns]
        InitConc = InitConc.to_dict("list")

        Rnames = F0AM_ModelCore.Rnames
        Cnames = F0AM_ModelCore.Cnames
        Met = F0AM_ModelCore.Met
        k = F0AM_ModelCore.k
        f = F0AM_ModelCore.f
        iG = F0AM_ModelCore.iG
        iRO2 = F0AM_ModelCore.iRO2
        ModelOptions = F0AM_ModelCore.ModelOptions
        Inames = F0AM_ModelCore.Inames
        Mnames = F0AM_ModelCore.Mnames
        #ChemFiles = F0AM_ModelCore.ChemFiles
        SolarParam = F0AM_ModelCore.SolarParam
        HoldFlag = F0AM_ModelCore.HoldFlag
        BkgdConc = F0AM_ModelCore.BkgdConc
        Bnames = F0AM_ModelCore.Bnames
        SolarFlag = F0AM_ModelCore.SolarFlag
        Snames = F0AM_ModelCore.Snames

    nRx = len(Rnames)  # number of reactions
    nSp = len(Cnames)  # number of species
    nIc = len(Met['T'])  # number of input constraints

    conc_init = zeros((nIc, nSp))
    iHold = []
    for i in set(Inames):#判断输入物质是否在机理中
        if i in set(Cnames):
            conc_init[:, Cnames.index(i)] = InitConc[i]  # 如果在就进行替换
            if HoldFlag[Inames.index(i)] == 1:
                iHold.append(Cnames.index(i))
        else:
            HoldFlag[Inames.index(i)] = 0  # 不存在初始化为0
            if ModelOptions["Verbose"] > 0:
                warn(f'CAUTION: Init Species {i} not found in reaction list.')

    conc_init *= tile(Met['M'], (1, nSp)) * 1e-9
    conc_init[:, 0] = 1
    conc_init[:, 1] = sum(conc_init[:, iRO2], axis=1)

    if ModelOptions['FixNOx']:#判断是否输入NO与NO2
        if 'NO' not in Inames or 'NO2' not in Inames:
            raise ValueError('F0AM_ModelCore: NO or NO2 missing from InitConc. Cannot use FixNox option.')
        iNOx = [Cnames.index(i) for i in ['NO', 'NO2']]
    NOxinfo = []
    del Inames, HoldFlag

    if 'DEFAULT' in BkgdConc.keys(): #and list(BkgdConc["DEFAULT"])[0][0] == 1:#通过
        try:
            tem = BkgdConc["DEFAULT"][0][0]
        except:
            tem = BkgdConc["DEFAULT"]
        conc_bkgd = tem * conc_init / tile(Met['M'], (1, nSp)) * 1e9  # 计算背景浓度
    else:
        conc_bkgd = 0 * conc_init

    for i in set(Bnames):
        if i in set(Cnames):
            conc_bkgd[:, Cnames.index(i)] = BkgdConc[i]  # 添加某个物质的背景浓度
        elif i != 'DEFAULT':
            warn('CAUTION: Bkgd Species {0} not found in reaction list.'.format(i), Warning)

    conc_bkgd *= tile(Met['M'], (1, nSp)) * 1e-9
    conc_bkgd[:, 0] = 1
    del Bnames


    print('ENTERING MODEL RUN')

    Conc = []
    Time = []
    StepIndex = []
    RepIndex = []

    for j in range(ModelOptions['Repeat']):  # 这个循环是为了干嘛，也没有搞清楚，现在Repeat为1
        for i in range(nIc):  # 对于每个积分时间进行循环，24小时就代表24个积分时间

            if ModelOptions['Verbose'] >= 1:  # 输出更多的信息
                print(f'Step={i} of {nIc}, Rep={j} of {ModelOptions["Repeat"]}\n')

            if ModelOptions['LinkSteps'] and (i > 0 or j > 0):  # 此判断是一个大坑！！！模型很多奇妙的结果跟这个判断有关
                conc_init_step = conc_out[-1, :].T #carry over end cons from previous step if desired
                conc_init_step[iHold] = conc_init[i, iHold] #override for Held species
                if ModelOptions['FixNOx']:  # 是否修正NOx，此判断是一个大坑！！！
                    modelNOx = conc_out[-1, iNOx]
                    InitNOx = conc_init[i, iNOx]
                    conc_init_step[iNOx] = modelNOx * sum(InitNOx) / sum(modelNOx)#NOxinfo = iNOx.append(initNOx)
            else:
                conc_init_step = conc_init[i, :].T #ODE solver needs 1 row for each species
            #DO INTERFATION
            if SolarFlag:  # 此判断的前半部分未测试！！！
                #in this special case, the model take a bunch of mini-steps to allow SZA, and thus
                #photochemistry, to evolve throughout a model step
                extendTime = linspace(0, SolarParam['nDays'] * 86400, SolarParam['nDays'] * 86400 / ModelOptions["IntTime"] + 1)
                extendTime -= 86400 * floor(extendTime / 86400)

                sTime = dict(zip(['year', 'month', 'day', 'hour', 'min', 'sec'], SolarParam['starTime'][i]))
                sTime.update({'sec': sTime['sec'] + extendTime})
                sTime.update({'UTC': 0})

                location = {"longitude": SolarParam["lon"][i], "latitude": SolarParam["lat"][i], "altitude": SolarParam["alt"][i]}

                sun = sun_position(sTime, location)
                sun['zenith'][sun['zenith'] > 90] = 90
                nSolar = len(extendTime)

                solarMet= {k: tile(Met[k][i, :], [nSolar, 1]) for k in Mnames}

                solarMet['SZA'] = sun['zenith']
                Met['SZA'][i] = solarMet['SZA'][-1]
                _, _, k_solar, _, _, _, _, _ = InitializeChemistry(solarMet, ChemFiles, ModelOptions, 0)
                #EXECUTE MODEL, UPDATING SZA AT EACH MINI-STEP
                conc_solar_end = zeros(nSolar, nSp) * float("nan")
                time_solar_end = zeros(nSolar, 1) * float("nan")
                for k in range(nSolar):
                    if ModelOptions["Verbose"] >= 2:
                        print(f"Solar Cycle {f} of {nSolar}")
                    #CALL ODE SOLVER
                    param = [k_solar[i, :], f, iG, iRO2, iHold, Met["kdil"][i], conc_bkgd[i, :], ModelOptions["IntTime"],
                             ModelOptions["Verbose"], NOxinfo]
                    t = ModelOptions["IntTime"]
                    solver = "solver"if sum(iHold) == 0 else "solver2"
                    time_out, conc_out = solver3(t, conc_init_step, param, solver)
                    #options = odeset("Jacobian", @(t,conc_out)Jac_eval(t, conc_out, param))#create struct for ODE and PDE solver
                    #to specify some parameters, in this case only update the field "Jacobian" use function-handler Jac_eval
                    #time_out, conc_out = ode15s(@(t,conc_out)dydt_eval(t, conc_out, param), [0,ModelOptions["IntTime"]],
                    #                    conc_init_step.T, options)#t,y=ode15s(odefun,tspan,y0,options)
                    conc_init_step = conc_out[-1, :].T
                    if ModelOptions["FixNOx"]:
                        modelNOx = conc_out[-1, iNOx]
                        initNOx = conc_init[i, iNOx]
                        conc_init_step[iNOx] = modelNOx * sum(initNOx) / sum(modelNOx)
                        NOxinfo = iNOx.append(initNOx)
                    conc_solar_end[k, :] = conc_init_step
                    time_solar_end[k] = time_out[-1] * k
                if ModelOptions["EndPointsOnly"]:
                    k[i, :] = k_solar[-1, :]
                else:
                    k = r_(k, [k_solar])
                SolarParam["SZAcycle"] = r_(SolarParam["SZAcycle"], [solarMet["SZA"]])
            else:  # OBM模型经过后半段
                param = [k[i, :], f, iG, iRO2, iHold, Met["kdil"][i], conc_bkgd[i, :], ModelOptions['IntTime'],
                         ModelOptions['Verbose'], NOxinfo]
                t = ModelOptions["IntTime"]
                solver = "solver" if sum(iHold) == 0 else "solver2"  # 如果iHold权威0调用solver求解器否则调用solver2求解器
                time_out, conc_out = solver3(t, conc_init_step, param, solver)  # 调用求解器
                #options = odeset("Jacobian", @(t,conc_out)Jac_eval(t, conc_out, param))# odeset is a tool to create struct for ode15s()
                #time_out, conc_out = ode15s(@(t,conc_out)dydt_eval(t, conc_out, param), [0,ModelOptions["IntTime"]],
                #                        conc_init_step.T, options)

            if ModelOptions["Verbose"] >= 1:
                print("MODEL STEP TIME IS: {0} SECONDS".format((datetime.now() - StartTime).seconds))

            if ModelOptions["EndPointsOnly"]:  # 是否只保存运行结果的最后部分，含义是一个积分时间内会输出很多中间结果，保存全部的情况未测试
                Conc.append(conc_out[-1].tolist())
                Time.append(time_out)
                StepIndex.append(i)
                RepIndex.append(j)
            elif not SolarFlag:  # 未测试
                Conc.append(conc_out.tolist())
                Time.append(time_out)
                StepIndex.append(ones(time_out.shape)*i)
                RepIndex.append(ones(time_out.shape)*j)
            else:  # OBM模型通过这
                Conc.append(conc_solar_end.tolist())
                Time.append(time_solar_end + SolarParam["nDays"] * (i-1))
                StepIndex.append(ones((nSolar, 1)) * i)
                RepIndex.append(ones((nSolar, 1)) * j)
    del i, j, conc_init_step, param, conc_out, time_out

    Conc=array(Conc)
    Conc[Conc<0]=0  # 可能会存在浓度为负数的情况，将其修正
    Conc[:,1]=sum(Conc[:,iRO2],axis=1)  # 这里跟RO2有关，详情见InitializeChemistry注释
    G=Conc[:,iG[:,0]]*Conc[:,iG[:,1]]  # 反应物的第一列乘以反应物的第二列
    Mbig=Met["M"][StepIndex]
    if len(k[0])!=len(G[0]):
        kbig=k[StepIndex,:]
    else:
        kbig=k
    Chem={"Rates":kbig*G*1e9/tile(Mbig,(1,nRx)),"f":f,"iG":iG,"k":k,"ChemFiles":ChemFiles,"Rnames":Rnames,"iHold":iHold}

    kdilbig=tile(Met["kdil"][StepIndex],(1,nSp))
    conc_bkgd_big=conc_bkgd[StepIndex,:]
    dilrate=-kdilbig*(Conc-conc_bkgd_big)*1e9/tile(Mbig,(1,nSp))
    dilrate[:,0:1]=0
    Chem["DilRates"] = {i: j for i, j in zip(Cnames, dilrate)}

    Conc=Conc*1e9/tile(Met["M"][StepIndex],(1,nSp))
    Conc[:,0]=1  # 将 "ONE" 物种浓度设置为1，详情见InitializeChemistry的注释
    Conc = {i: j for i, j in zip(Cnames, Conc.T)}

    if len(ModelOptions["TimeStamp"])!=0:  # 没啥作用好像，不参与计算
        Time2Rep=tile(ModelOptions["TimeStamp"],[ModelOptions["Repeat"],1])[0]
        dTime=median(diff(Time2Rep))
        if len(Time2Rep)==len(RepIndex):
            Time2Rep=Time2Rep+(max(Time2Rep)+dTime)*(array(RepIndex)-1)
            Time=Time2Rep
        else:
            warn("CAUTION: TimeStamp and Time are different lengths, Output {0} not overwritten.".format(Time))
        del Time2Rep,dTime
    del G,kbig,Mbig,kdilbig,conc_bkgd_big,conc_init,conc_bkgd,dilrate,nSp,nRx
    del nIc,f,iG,k,ChemFiles,Rnames,iHold,Mnames,Snames,SolarFlag

    result={"BkgdConc": BkgdConc, "Chem": Chem, "Cnames": Cnames, "Conc": Conc, "InitConc": InitConc,
            "Met": Met, "ModelOptions": ModelOptions, "RepIndex":RepIndex,"SolarParam":SolarParam,"StepIndex":StepIndex,
            "Time": Time, "iRO2": iRO2}

    if ModelOptions["SavePath"].lower() == "DoNotSave".lower():  # 是否保存结果到脚本路径下
        print("Model output not saved")
    else:
        save_path = dirname(__file__) + sep + "result.json"
        with open(save_path, encoding="utf-8") as f:
            f.write(dumps(result))

    if ModelOptions["DeclareVictory"]:  # 是否欢呼！
        try:
            victory(dirname(__file__)+sep+"tool"+sep+"ffVII_victory.wav")
        except FileNotFoundError:
            print("LOL")
    print(f"TOTAL RUN TIME IS {(datetime.now() - StartTime).seconds} SECONDS")

    return result