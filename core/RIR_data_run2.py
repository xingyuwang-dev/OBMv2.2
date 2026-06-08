from core.F0AM_ModelCore2 import F0AM_ModelCore_read, F0AM_ModelCore_calculate
from multiprocessing import Pool, cpu_count, freeze_support
from tool.sun_position import sun_position
from copy import deepcopy
from json import dumps, load
from numpy import append
from os import sep
from core.P_O3subNO import P_O3subNO
from pandas import DataFrame

# 此为RIR模块的的运算模块，用于预热模式，更新模式，情景削减模式
# initialize用于预热，update用于更新模式，initialize_update用于情景削减模式


J_name = {f"J{i}" for i in range(30)}


def columns(data, iHold):
    return [0 if i in {"O3", "NO", "NO2", "CO", "PAN"} else iHold for i in data.columns]


def initialize(data, time, climate, location, arg, save_path, iHold=0):
    kdil, bkgdconc, jcorr, O3col, albedo, LinkSteps, FixNOx = arg
    HOUR, MIN, SEC, UTC = data.index.to_list(), 0, 0, 8
    time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"], "min": MIN, "sec": SEC,
            "UTC": UTC}
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
    args = F0AM_ModelCore_read(Met, ChemFiles)
    args2 = (data, BkgdConc, ModelOptions, kdil, *args)
    result = F0AM_ModelCore_calculate(args2)
    Conc = {i: [j[-1]] * 36 for i, j in result["Conc"].items()}  # 36和下面update的情景个数对应
    with open(save_path + sep + "result.json", "wb") as f:
        f.write(dumps(Conc).encode("utf-8"))
        f.close()


def update(data, time, climate, location, arg, save_path, iHold=0, multi_process=True):
    freeze_support()
    voc = {"FORM", "ALD2", "PAN", "ALDX", "PANX", "NTR", "ETOH", "CH4", "MEOH", "MEPX", "FACD", "ETHA", "ROOH",
           "AACD", "PACD", "PAR", "ETH", "OLE", "IOLE", "ISOP", "ISPD", "TERP", "TOL", "XYL", "CRES", "OPEN", "MGLY"}
    data_keys = set(data.keys())
    olefin = list({"IOLE", "OLE", "ETH", "ISOP", "TERP"} & data_keys)
    vocs = list(voc & data_keys)
    aromatics = list({"XYL", "TOL", "MGLY", "OPEN"} & data_keys)
    ovocs = list({"ALD2", "ETOH", "ALDX", "FORM", "MEOH", "FACD", "ROOH", "AACD", "PACD", "CRES"} & data_keys)
    voc_nox = list(voc | {"NO", "NOx"} & data_keys)

    kdil, bkgdconc, jcorr, O3col, albedo, LinkSteps, FixNOx = arg
    if multi_process:
        pool = Pool(min(cpu_count(), 25))
    else:
        pool = Pool(1)
    HOUR, MIN, SEC, UTC = data.index.to_list(), 0, 0, 8
    time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"], "min": MIN, "sec": SEC,
            "UTC": UTC}
    sun = sun_position(time, deepcopy(location))
    Met = {"P": climate["P"], "T": [i + 273.15 for i in climate["T"]], "RH": climate["H"], "SZA": sun["zenith"],
           "kdil": kdil, "jcorr": jcorr, "ALT": location["altitude"], "O3col": O3col, "albedo": albedo}
    J = {i for i in data.columns if i[0] == "J"}
    Met.update({i: data[i].tolist() for i in J})
    ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)", "CB05_AllRxns")
    BkgdConc = {"DEFAULT": bkgdconc}
    ModelOptions = {"Verbose": 0, "EndPointsOnly": 1, "LinkSteps": LinkSteps, "Repeat": 1, "IntTime": 3600,
                    "SavePath": "DoNotSave", "FixNOx": FixNOx, "TimeStamp": time["hour"]}
    args = F0AM_ModelCore_read(Met, ChemFiles)

    re = []
    with open(save_path + sep + "result.json", "rb") as f:
        result = DataFrame(load(f))
    temp = list(set(result.keys()) - set(data.keys()) | {"O3"})

    j = 0

    data[temp] = result[temp].loc[j]
    data.columns = [data.columns, columns(data, iHold)]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # RIR_CO
    data_["CO"] *= 0.9
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # RIR_NOx
    data_[["NO", "NO2"]] *= 0.9
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # RIR_VOCs
    data_[vocs] *= 0.9
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.9
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # RIR_OLEFIN
    data_[olefin] *= 0.9
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # RIR_AROMATICS
    data_[aromatics] *= 0.9
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # RIR_OVOCS
    data_[ovocs] *= 0.9
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # NOx_20
    data_[["NO", "NO2"]] *= 0.8
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # VOCs_20
    data_[vocs] *= 0.8
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # NOx_30
    data_[["NO", "NO2"]] *= 0.7
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # VOCs_30
    data_[vocs] *= 0.7
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[["NO", "NO2"]] *= 0.6
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.6
    data_[temp] = result[temp].loc[j]
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # VOCs_NOx_10
    data_[voc_nox] *= 0.9
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.9
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # VOCs_NOx_20
    data_[voc_nox] *= 0.8
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.8
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)  # VOCs_NOx_30
    data_[voc_nox] *= 0.7
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.7
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))

    data_ = deepcopy(data)
    data_[voc_nox] *= 0.6
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.6
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))

    data_ = deepcopy(data)
    data_[vocs] *= 0.95
    data_[["NO2", "NO"]] *= 0.9
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.92
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.9
    data_[["NO2", "NO"]] *= 0.8
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.85
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.85
    data_[["NO2", "NO"]] *= 0.7
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.78
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.8
    data_[["NO2", "NO"]] *= 0.6
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.7
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.9
    data_[["NO2", "NO"]] *= 0.95
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.92
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.8
    data_[["NO2", "NO"]] *= 0.9
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.95
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.7
    data_[["NO2", "NO"]] *= 0.85
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.9
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    data_ = deepcopy(data)
    data_[vocs] *= 0.6
    data_[["NO2", "NO"]] *= 0.8
    data_[temp] = result[temp].loc[j]
    # data_["O3"] *= 0.7
    re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=((data_, BkgdConc, ModelOptions, kdil, *args),)))
    j += 1

    pool.close()
    pool.join()

    O3_G, O3_D, component, R_special = P_O3subNO(re[0].get(), True)
    O3_CO_G, O3_CO_D, _ = P_O3subNO(re[1].get())
    O3_NOx_G, O3_NOx_D, _ = P_O3subNO(re[2].get())
    O3_VOCs_G, O3_VOCs_D, _ = P_O3subNO(re[3].get())
    O3_olefin_G, O3_olefin_D, _ = P_O3subNO(re[4].get())
    # O3_alkyne_G, O3_alkyne_D, _ = P_O3subNO(re[5].get())
    O3_aromatics_G, O3_aromatics_D, _ = P_O3subNO(re[5].get())
    O3_ovocs_G, O3_ovocs_D, _ = P_O3subNO(re[6].get())
    P_O3 = O3_G - O3_D
    a1 = 10 * (P_O3 - O3_CO_G + O3_CO_D) / P_O3
    a2 = 10 * (P_O3 - O3_NOx_G + O3_NOx_D) / P_O3
    a3 = 10 * (P_O3 - O3_VOCs_G + O3_VOCs_D) / P_O3
    a4 = 10 * (P_O3 - O3_olefin_G + O3_olefin_D) / P_O3
    a5 = 10 * (P_O3 - O3_aromatics_G + O3_aromatics_D) / P_O3
    a6 = 10 * (P_O3 - O3_ovocs_G + O3_ovocs_D) / P_O3

    O3_NOx_10 = float(re[2].get()["Conc"]["O3"])
    O3_VOCs_10 = float(re[3].get()["Conc"]["O3"])
    O3_NOx_20 = float(re[7].get()["Conc"]["O3"])
    O3_VOCs_20 = float(re[8].get()["Conc"]["O3"])
    O3_NOx_30 = float(re[9].get()["Conc"]["O3"])
    O3_VOCs_30 = float(re[10].get()["Conc"]["O3"])
    # O3_NOxVOCs_10 = float(re[11].get()["Conc"]["O3"])
    # O3_NOxVOCs_20 = float(re[12].get()["Conc"]["O3"])
    # O3_NOxVOCs_30 = float(re[13].get()["Conc"]["O3"])

    O3_NOx_40 = float(re[11].get()["Conc"]["O3"])
    O3_VOCs_40 = float(re[12].get()["Conc"]["O3"])

    b1 = float(re[13].get()["Conc"]["O3"])
    b2 = float(re[14].get()["Conc"]["O3"])
    b3 = float(re[15].get()["Conc"]["O3"])
    b4 = float(re[16].get()["Conc"]["O3"])
    b5 = float(re[17].get()["Conc"]["O3"])
    b6 = float(re[18].get()["Conc"]["O3"])
    b7 = float(re[19].get()["Conc"]["O3"])
    b8 = float(re[20].get()["Conc"]["O3"])
    b9 = float(re[21].get()["Conc"]["O3"])
    b10 = float(re[22].get()["Conc"]["O3"])
    b11 = float(re[23].get()["Conc"]["O3"])
    b12 = float(re[24].get()["Conc"]["O3"])

    M = float(re[0].get()["Met"]["M"]) * 1e-9
    RO2 = float((re[0].get()["Conc"]["XO2"] + re[0].get()["Conc"]["XO2N"] + re[0].get()["Conc"]["MEO2"] +
                 re[0].get()["Conc"]["TO2"])) * M
    OH = float(re[0].get()["Conc"]["OH"]) * M
    HO2 = float(re[0].get()["Conc"]["HO2"]) * M
    HONO = float(re[0].get()["Conc"]["HONO"]) * M

    k = re[0].get()["Chem"]["k"][0]
    J = [k[8], k[73], k[74], k[0], k[35], k[24], k[14], k[13]]

    save_result = re[0].get()["Conc"]
    for result in re[1:]:
        temp = result.get()["Conc"]
        for i, j in temp.items():
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
    R5 = [T] + [round(i, 5) for i in
                [O3_NOx_10, O3_NOx_20, O3_NOx_30, O3_NOx_40, O3_VOCs_10, O3_VOCs_20, O3_VOCs_30, O3_VOCs_40]]
    # R6 = [T] + [round(i, 5) for i in [O3_NOxVOCs_10, O3_NOxVOCs_20, O3_NOxVOCs_30]]
    R6 = [T] + [round(i, 5) for i in [b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, b11, b12]]
    R7 = [T] + [round(i, 8) for i in J]

    return R1, R2, R3, R4, R5, R6, R7


def initialize_update(data_list, arg2, location, iHold=0, vocs_cut=-1, nox_cut=-1):
    freeze_support()
    kdil, bkgdconc, jcorr, O3col, albedo, LinkSteps, FixNOx = arg2
    voc = {"FORM", "ALD2", "PAN", "ALDX", "PANX", "NTR", "ETOH", "CH4", "MEOH", "MEPX", "FACD", "ETHA", "ROOH",
           "AACD", "PACD", "PAR", "ETH", "OLE", "IOLE", "ISOP", "ISPD", "TERP", "TOL", "XYL", "CRES", "OPEN", "MGLY"}
    MIN, SEC, UTC = 0, 0, 8
    ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)", "CB05_AllRxns")
    BkgdConc = {"DEFAULT": bkgdconc}
    ModelOptions = {"Verbose": 0, "EndPointsOnly": 1, "LinkSteps": LinkSteps, "Repeat": 1, "IntTime": 3600,
                    "SavePath": "DoNotSave", "FixNOx": FixNOx}

    CPU, re, args_list = len(data_list), [], []
    pool = Pool(CPU)
    for i in range(CPU):  # 计算所有🤔的情况
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
        args = F0AM_ModelCore_read(Met, ChemFiles)
        args_list.append(args)
        args2 = (InitConc, BkgdConc, ModelOptions, kdil, *args)
        re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=(args2,)))
    pool.close()
    pool.join()

    result_list = [{i: j[-1] for i, j in item.get()["Conc"].items()} for item in re]
    O3 = []
    for hour in range(24):
        pool = Pool(CPU - 1)
        data_hour = [data_[0].iloc[[hour]] for data_ in data_list]
        T_list, re = [], []
        for day in range(1, CPU):  # 计算所有🤔的24小时更新情况
            result, data = result_list[day - 1], data_hour[day - 1]
            _, time, climate = data_list[day]
            time = {"year": time["Y"], "month": time["M"], "day": time["D"], "hour": time["H"][hour], "min": MIN,
                    "sec": SEC, "UTC": UTC}
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
                args2 = (data2, BkgdConc, ModelOptions, kdil, args_list[day][0][hour], *args_list[day][1:])
                re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=(args2,)))

            elif nox_cut and not vocs_cut:
                data2 = deepcopy(data)
                for i in data_keys:
                    if i in {"NO2", "NO"}:
                        data2[i] *= (1 - nox_cut)
                for i in temp:
                    data2[i] = result[i]
                args2 = (data2, BkgdConc, ModelOptions, kdil, args_list[day][0][hour], *args_list[day][1:])
                re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=(args2,)))

            else:
                data2 = deepcopy(data)
                for i in data_keys:
                    if i in voc:
                        data2[i] *= (1 - vocs_cut)
                    if i in {"NO2", "NO"}:
                        data2[i] *= (1 - nox_cut)
                for i in temp:
                    data2[i] = result[i]
                args2 = (data2, BkgdConc, ModelOptions, kdil, args_list[day][0][hour], *args_list[day][1:])
                re.append(pool.apply_async(func=F0AM_ModelCore_calculate, args=(args2,)))

            T = str(time["year"]) + "-" + str(time["month"]).rjust(2, "0") + "-" + \
                str(time["day"]).rjust(2, "0") + " " + str(time["hour"]).rjust(2, "0") + ":00:00"
            T_list.append(T)
        pool.close()
        pool.join()
        result_list = [item.get()["Conc"] for item in re]
        temp = [float(k["O3"]) for k in result_list]
        O3.append([{"dateTime": t, "value": o3} for t, o3 in zip(T_list, temp)])

    O3 = list(map(list, zip(*O3)))
    return_result = {str(day): O3[day] for day in range(CPU - 1)}

    return return_result
