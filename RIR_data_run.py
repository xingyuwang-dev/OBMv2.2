from F0AM_ModelCore import F0AM_ModelCore
from multiprocessing import Pool, cpu_count
from Tool.sun_position import sun_position
from copy import deepcopy
from json import dumps, load
from numpy import append
from os import sep
from P_O3subNO import P_O3subNO


# 已弃用，但能用


J_name = {f"J{i}" for i in range(30)}


def columns(data, iHold):
    return [0 if i in {"O3", "NO", "NO2", "CO", "SO2"} else iHold for i in data.columns]


def initialize(data, time, climate, location, arg, save_path, iHold=0):
    kdil, bkgdconc, jcorr, O3col, albedo, LinkSteps, FixNOx = arg
    pool = Pool(1) #Autention! 这里这么做的原因是为了建立子进程，从而退出子进程的时候能够删除FOAM_ModelCore.FirstCall
    HOUR, MIN, SEC, UTC = data.index.to_list(), 0, 0, 8
    time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"], "min": MIN, "sec": SEC, "UTC": UTC}
    sun = sun_position(time, deepcopy(location))
    Met = {"P": climate["P"], "T": [i + 273.15 for i in climate["T"]], "RH": climate["H"], "SZA": sun["zenith"],
           "kdil": kdil, "jcorr": jcorr, "ALT": location["altitude"], "O3col": O3col, "albedo": albedo}
    J = {i for i in data.columns if i[0] == "J"}
    Met.update({i: data[i].tolist() for i in J})
    ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)", "CB05_AllRxns")
    BkgdConc = {"DEFAULT": bkgdconc}
    ModelOptions = {"Verbose": 0, "EndPointsOnly": 1, "LinkSteps": LinkSteps, "Repeat": 1, "IntTime": 3600,
                    "SavePath": "DoNotSave", "FixNOx": FixNOx, "TimeStamp": time["hour"]}
    data.columns = [data.columns, columns(data, iHold)]
    arg = (Met, data, ChemFiles, BkgdConc, ModelOptions, False)
    re = pool.apply_async(func=F0AM_ModelCore, args=(arg,))
    result = re.get()
    Conc = {i: [j[-1]]*14 for i, j in result["Conc"].items()}
    with open(save_path + sep + "result.json", "wb") as f:
        f.write(dumps(Conc).encode("utf-8"))
        f.close()


def update(data, time, climate, location, arg, save_path, iHold=0, multi_process=True):
    kdil, bkgdconc, jcorr, O3col, albedo, LinkSteps, FixNOx = arg
    if multi_process:
        pool = Pool(min(cpu_count(), 14))
    voc = {"FORM", "ALD2", "PAN", "ALDX", "PANX", "NTR", "ETOH", "CH4", "MEOH", "MEPX", "FACD", "ETHA", "ROOH",
           "AACD", "PACD", "PAR", "ETH", "OLE", "IOLE", "ISOP", "ISPD", "TERP", "TOL", "XYL", "CRES", "OPEN", "MGLY"}
    voc_nox = voc | {"NO", "NOx"}

    HOUR, MIN, SEC, UTC = data.index.to_list(), 0, 0, 8
    time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"], "min": MIN, "sec": SEC, "UTC": UTC}
    sun = sun_position(time, deepcopy(location))
    Met = {"P": climate["P"], "T": [i + 273.15 for i in climate["T"]], "RH": climate["H"], "SZA": sun["zenith"],
           "kdil": kdil, "jcorr": jcorr, "ALT": location["altitude"], "O3col": O3col, "albedo": albedo}
    J = {i for i in data.columns if i[0] == "J"}
    Met.update({i: data[i].tolist() for i in J})
    ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)", "CB05_AllRxns")
    BkgdConc = {"DEFAULT": bkgdconc}
    ModelOptions = {"Verbose": 0, "EndPointsOnly": 1, "LinkSteps": 1, "Repeat": 1, "IntTime": 3600,
                    "SavePath": "DoNotSave", "FixNOx": FixNOx, "TimeStamp": time["hour"]}
    re = []
    with open(save_path + sep + "result.json", "rb") as f:
        result = load(f)
    temp = set(result.keys()) - set(data.keys()) | {"O3"}
    j = 0

    for i in temp:
        data[i] = result[i][j]
    data.columns = [data.columns, columns(data, iHold)]
    data_keys = [i[0] for i in data.keys()]
    arg = (Met, data, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data1 = deepcopy(data)#RIR_CO
    data1["CO"] *= 0.9
    for i in temp:
        data1[i] = result[i][j]
    arg = (Met, data1, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data2 = deepcopy(data)#RIR_NOx
    data2["NO"] *= 0.9
    data2["NO2"] *= 0.9
    for i in temp:
        data2[i] = result[i][j]
    arg = (Met, data2, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data3 = deepcopy(data)#RIR_VOCs
    for i in data_keys:
        if i in voc:
            data3[i] *= 0.9
    for i in temp:
        data3[i] = result[i][j]
    arg = (Met, data3, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data4 = deepcopy(data)#RIR_OLEFIN
    for i in data_keys:
        if i in ["IOLE", "OLE", "ETH", "ISOP", "TERP"]:
            data4[i] *= 0.9
    for i in temp:
        data4[i] = result[i][j]
    arg = (Met, data4, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data5 = deepcopy(data)#RIR_AROMATICS
    for i in data_keys:
        if i in ["XYL", "TOL", "MGLY", "OPEN"]:
            data5[i] *= 0.9
    for i in temp:
        data5[i] = result[i][j]
    arg = (Met, data5, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data6 = deepcopy(data)#RIR_OVOCS
    for i in data_keys:
        if i in ["ALD2", "ETOH", "ALDX", "FORM", "MEOH", "FACD", "ROOH", "AACD", "PACD", "CRES"]:
            data6[i] *= 0.9
    for i in temp:
        data6[i] = result[i][j]
    arg = (Met, data6, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data7 = deepcopy(data)  # NOx_20
    data7["NO"] *= 0.8
    data7["NO2"] *= 0.8
    for i in temp:
        data7[i] = result[i][j]
    arg = (Met, data7, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data8 = deepcopy(data)  # VOCs_20
    for i in data_keys:
        if i in voc:
            data8[i] *= 0.8
    for i in temp:
        data8[i] = result[i][j]
    arg = (Met, data8, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data9 = deepcopy(data)  # NOx_30
    data9["NO"] *= 0.7
    data9["NO2"] *= 0.7
    for i in temp:
        data9[i] = result[i][j]
    arg = (Met, data9, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data10 = deepcopy(data)  # VOCs_30
    for i in data_keys:
        if i in voc:
            data10[i] *= 0.7
    for i in temp:
        data10[i] = result[i][j]
    arg = (Met, data10, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data11 = deepcopy(data)  # VOCs_NOx_10
    for i in data_keys:
        if i in voc_nox:
            data11[i] *= 0.9
    for i in temp:
        data11[i] = result[i][j]
    arg = (Met, data11, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data12 = deepcopy(data)  # VOCs_NOx_20
    for i in data_keys:
        if i in voc_nox:
                data12[i] *= 0.8
    for i in temp:
        data12[i] = result[i][j]
    arg = (Met, data12, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    j += 1

    data13 = deepcopy(data)  # VOCs_NOx_30
    for i in data_keys:
        if i in voc_nox:
            data13[i] *= 0.7
    for i in temp:
        data13[i] = result[i][j]
    arg = (Met, data13, ChemFiles, BkgdConc, ModelOptions, False)
    re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))

    pool.close()
    pool.join()

    O3_G, O3_D, component, R_special = P_O3subNO(re[0].get(), True)
    O3_CO_G, O3_CO_D, _ = P_O3subNO(re[1].get())
    O3_NOx_G, O3_NOx_D, _ = P_O3subNO(re[2].get())
    O3_VOCs_G, O3_VOCs_D, _ = P_O3subNO(re[3].get())
    O3_olefin_G, O3_olefin_D, _ = P_O3subNO(re[4].get())
    #O3_alkyne_G, O3_alkyne_D, _ = P_O3subNO(re[5].get())
    O3_aromatics_G, O3_aromatics_D, _ = P_O3subNO(re[5].get())
    O3_ovocs_G, O3_ovocs_D, _ = P_O3subNO(re[6].get())
    P_O3 = O3_G - O3_D
    P_O3_CO = O3_CO_G - O3_CO_D
    P_O3_NOx = O3_NOx_G - O3_NOx_D
    P_O3_VOCs = O3_VOCs_G - O3_VOCs_D
    P_O3_olefin = O3_olefin_G - O3_olefin_D
    P_O3_aromatics = O3_aromatics_G -O3_aromatics_D
    P_O3_ovocs = O3_ovocs_G - O3_ovocs_D
    a1 = 10 * (P_O3 - P_O3_CO) / P_O3
    a2 = 10 * (P_O3 - P_O3_NOx) / P_O3
    a3 = 10 * (P_O3 - P_O3_VOCs) / P_O3
    a4 = 10 * (P_O3 - P_O3_olefin) / P_O3
    a5 = 10 * (P_O3 - P_O3_aromatics) / P_O3
    a6 = 10 * (P_O3 - P_O3_ovocs) / P_O3

    O3_NOx_10 = float(re[2].get()["Conc"]["O3"])
    O3_VOCs_10 = float(re[3].get()["Conc"]["O3"])
    O3_NOx_20 = float(re[7].get()["Conc"]["O3"])
    O3_VOCs_20 = float(re[8].get()["Conc"]["O3"])
    O3_NOx_30 = float(re[9].get()["Conc"]["O3"])
    O3_VOCs_30 = float(re[10].get()["Conc"]["O3"])
    O3_NOxVOCs_10 = float(re[11].get()["Conc"]["O3"])
    O3_NOxVOCs_20 = float(re[12].get()["Conc"]["O3"])
    O3_NOxVOCs_30 = float(re[13].get()["Conc"]["O3"])

    M = float(re[0].get()["Met"]["M"]) * 1e-9
    RO2 = float(re[0].get()["Conc"]["XO2"] + re[0].get()["Conc"]["XO2N"] + re[0].get()["Conc"]["MEO2"] + re[0].get()["Conc"]["TO2"]) * M
    OH = float(re[0].get()["Conc"]["OH"]) * M
    HO2 = float(re[0].get()["Conc"]["HO2"]) * M
    HONO = float(re[0].get()["Conc"]["HONO"]) * M

    k = re[0].get()["Chem"]["k"][0]
    J = [k[8], k[73], k[74], k[0], k[35], k[24], k[14], k[13]]


    save_result = re[0].get()["Conc"]
    for result in re[1:]:
        temp = result.get()["Conc"]
        for i, j in temp.items():
            j[j < 0] = 0
            save_result[i] = append(save_result[i], j)
    save_result = {i: j.tolist() for i, j in save_result.items()}
    with open(save_path + sep + "result.json", "wb") as f:
        f.write(dumps(save_result).encode("utf-8"))
        f.close()
    T = str(time["year"][0]) + "-" + str(time["month"][0]).rjust(2, "0") + "-" + \
        str(time["day"][0]).rjust(2, "0") + " " + str(time["hour"][0]).rjust(2, "0") + ":00:00"

    R1 = [T] + [round(i, 5) for i in [RO2, OH, HO2, HONO]]
    R2 = [T] + [round(i, 5) for i in [O3_G, O3_D]] + [round(i, 5) for i in list(component)]
    R3 = [T] + [round(i, 5) for i in [a1, a2, a3, a4, a5, a6]]
    R4 = [T] + [round(i, 5) for i in list(R_special)]
    R5 = [T] + [round(i, 5) for i in [O3_NOx_10, O3_NOx_20, O3_NOx_30, O3_VOCs_10, O3_VOCs_20, O3_VOCs_30]]
    R6 = [T] + [round(i, 5) for i in [O3_NOxVOCs_10, O3_NOxVOCs_20, O3_NOxVOCs_30]]
    R7 = [T] + [round(i, 8) for i in J]

    return R1, R2, R3, R4, R5, R6, R7


def initialize_update(data_list, arg2, location, iHold=0, vocs_cut=-1, nox_cut=-1):
    kdil, bkgdconc, jcorr, O3col, albedo, LinkSteps, FixNOx = arg2
    voc = {"FORM", "ALD2", "PAN", "ALDX", "PANX", "NTR", "ETOH", "CH4", "MEOH", "MEPX", "FACD", "ETHA", "ROOH",
           "AACD", "PACD", "PAR", "ETH", "OLE", "IOLE", "ISOP", "ISPD", "TERP", "TOL", "XYL", "CRES", "OPEN", "MGLY"}
    MIN, SEC, UTC = 0, 0, 8
    ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)", "CB05_AllRxns")
    BkgdConc = {"DEFAULT": bkgdconc}
    ModelOptions = {"Verbose": 0, "EndPointsOnly": 1, "LinkSteps": LinkSteps, "Repeat": 1, "IntTime": 3600,
                    "SavePath": "DoNotSave", "FixNOx": FixNOx}

    CPU, re = len(data_list)-1, []
    pool = Pool(CPU)
    for i in range(CPU):#计算所有🤔的预热情况
        InitConc, time, climate = deepcopy(data_list[i])
        time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"], "min": MIN, "sec": SEC,
                "UTC": UTC}
        sun = sun_position(time, deepcopy(location))
        Met = {"P": climate["P"], "T": [i + 273.15 for i in climate["T"]], "RH": climate["H"], "SZA": sun["zenith"],
               "kdil": kdil, "jcorr": jcorr, "ALT": location["altitude"], "O3col": O3col, "albedo": albedo}
        J = {i for i in InitConc.columns if i[0] == "J"}
        Met.update({i: InitConc[i].tolist() for i in J})
        InitConc.columns = [InitConc.columns, columns(InitConc, iHold)]
        ModelOptions.update({"TimeStamp": time["hour"]})
        arg = (deepcopy(Met), InitConc, deepcopy(ChemFiles), deepcopy(BkgdConc), deepcopy(ModelOptions), False)
        re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))
    pool.close()
    pool.join()

    result_list = [{i: j[-1] for i, j in item.get()["Conc"].items()} for item in re]
    O3 = []
    for hour in range(24):
        pool = Pool(CPU)
        data_hour = [data_[0].iloc[[hour]] for data_ in data_list]
        T_list, re = [], []
        for day in range(CPU):#计算所有🤔的24小时更新情况
            result, data = result_list[day], data_hour[day]
            _, time, climate = data_list[day+1]
            time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"][hour], "min": MIN, "sec": SEC,
                    "UTC": UTC}
            sun = sun_position(time, location)
            Met = {"P": climate["P"][hour], "T": 273.15 + climate["T"][hour], "RH": climate["H"][hour], "SZA": sun["zenith"],
                   "kdil": kdil, "jcorr": jcorr, "O3col": O3col, "albedo": albedo}
            J = {i for i in data.columns if i[0] == "J"}
            Met.update({i: data[i].tolist() for i in J})
            ModelOptions.update({"TimeStamp": time["hour"]})
            data.columns = [data.columns, columns(data, iHold)]
            temp = set(result.keys()) - set(data.keys()) | {"O3"}
            data_keys = [i[0] for i in data.keys()]

            if vocs_cut and not nox_cut:
                data2 = deepcopy(data)
                for i in data_keys:
                    if i in voc:
                        data2[i] *= (1 - vocs_cut)
                for i in temp:
                    data2[i] = result[i]
                arg = (Met, data2, ChemFiles, BkgdConc, ModelOptions, False)
                re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))

            elif nox_cut and not vocs_cut:
                data2 = deepcopy(data)
                for i in data_keys:
                    if i in {"NO2", "NO"}:
                        data2[i] *= (1 - nox_cut)
                for i in temp:
                    data2[i] = result[i]
                arg = (Met, data2, ChemFiles, BkgdConc, ModelOptions, False)
                re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))

            else:
                data2 = deepcopy(data)
                for i in data_keys:
                    if i in voc:
                        data2[i] *= (1 - vocs_cut)
                    if i in {"NO2", "NO"}:
                        data2[i] *= (1 - nox_cut)
                for i in temp:
                    data2[i] = result[i]
                arg = (Met, data2, ChemFiles, BkgdConc, ModelOptions, False)
                re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg,)))

            T = str(time["year"][0]) + "-" + str(time["month"][0]).rjust(2, "0") + "-" + \
                str(time["day"][0]).rjust(2, "0") + " " + str(time["hour"][0]).rjust(2, "0") + ":00:00"
            T_list.append(T)
        pool.close()
        pool.join()
        result_list = [item.get()["Conc"] for item in re]
        temp = [float(k["O3"]) for k in result_list]
        O3.append([{"dateTime": t, "value": o3} for t, o3 in zip(T_list, temp)])

    O3 = list(map(list, zip(*O3)))
    return_result = {str(day): O3[day] for day in range(CPU)}

    return return_result