from pandas import read_csv, DataFrame, Series
from numpy import array, gradient, unravel_index, argmax, arange, polyfit
from datetime import datetime
from os import sep
from os.path import exists
from sys import exit
from tool.sun_position import sun_position
from core.data_run import data_run
from copy import deepcopy
from json import loads
from tool.data_average import do_mean, calculate_noxvoc
from CB05.CB05_transfrom import transfrom
from scipy.interpolate import interp1d, interp2d

# 此是线上运行的OBM模型，其中数据处理，模型设置部分封装成了类；这样做的主要原因是为了规避多线程计算中会出现的变量共享
# 的问题。当后端传入多个站点数据时，每个站点的数据与设置需要最大程度的隔绝。将通用的数据处理与模型设置封装为类，实例属性
# 与实例方法时，可以有效达到此效果。此不是线上模型入口，OBM_grpc.py才是模型的入口和出口；相对于OBM_EKMA_1day.py不会重复注释


main_path = "/Users/xingyuwang/Desktop/OBM_EKMA"  # 模型运行路径，服务器设置为 dirname(__file__)
log_file = main_path + sep + "log.txt"  # 日志保存路径
compound_name = read_csv(main_path + sep + "comparison_table.csv", header=None)  # 读取对照表


class Do_simulation:
    tem_summer = [26.1, 26, 25.9, 25.4, 25, 25.1, 25.2, 25.9, 27.7, 28.4, 28.7, 28.2,  # 类属性，能被所有实例共享
                  28, 26.2, 26.7, 27.3, 27.4, 27.2, 26.6, 26.6, 26.4, 26.5, 26.5, 26.5]
    tem_winter = [6.7, 6.4, 6.1, 5.7, 6, 5.9, 5.6, 6.1, 6.5, 7, 7.3, 7.6,
                  7.7, 8, 8.3, 8.5, 8.6, 8.2, 8, 7.7, 7.6, 7.6, 7.6, 7.1]
    hum_summer = [95.2, 93.1, 93.3, 94.2, 95.6, 96.7, 99.2, 95.1, 81.3, 78.5, 77, 79.5,
                  81.3, 95.1, 94.4, 90.6, 90.8, 90.4, 94.2, 96.8, 99.4, 99.8, 98.6, 98]
    hum_winter = [74.7, 76.4, 76.8, 77.3, 75.6, 73.6, 75.6, 72.6, 70.1, 69.1, 68.6, 65.2,
                  66.2, 64.6, 61.6, 59.7, 59.8, 61.5, 64.2, 65.9, 66.9, 68.6, 69.3, 71.2]
    threshold = {"C5H8": 5, "HCHO": 50, "CH3CHO": 50, "CH3CL": 10, "VINCL": 10, "CH2CL2": 10, "CH2CLCHCL2": 10,
                 "CHCL2CHCL2": 10}

    def __init__(self, rec_str):  # 初始化实例
        try:
            self.data = DataFrame(rec_str["data"]).set_index("DATETIME")  # 初始化data为DataFrame，并设置DATETIME列为索引
        except Exception:
            raise KeyError("Check your data!")
        try:
            self.climate = [float(rec_str["p"]), float(rec_str["t"]), float(rec_str["h"])]  # 初始化气压，温度，湿度
            self.control = [float(rec_str["kdil"]), float(rec_str["bkgdconc"]), float(rec_str["jcorr"]),
                            # 稀释速率，背景浓度系数，光解速率校正系数
                            float(rec_str["o3col"]), float(rec_str["albedo"]), float(rec_str["linksteps"]),
                            # 臭氧总量，反射率，迭代控制参数
                            float(rec_str["fixnox"])]  # NOx校正系数
            self.location = {"latitude": float(rec_str["latitude"]), "longitude": float(rec_str["longitude"]),  # 经纬度，海拔
                             "altitude": float(rec_str["altitude"])}
            self.iHold = int(rec_str["ihold"])  # ihold参数
            self.I_ARRAY = rec_str["i_array"]  # VOCs情景
            self.J_ARRAY = rec_str["j_array"]  # NOx情景
        except KeyError:
            raise KeyError("Check your parameter!")
        if not self.data.__contains__("10102-44-0") or not self.data.__contains__("10102-43-9"):  # 判断是否包含NO与NO2
            raise KeyError("Absence of NO, or NO2!")
        self.YEAR = 2020  # 默认年月日
        self.MONTH = 6
        self.DAY = 25
        self.voc_nox_mean = ([], [])  # 初始化vocs_nox_mean

    def do_process(self):  # 实例方法
        comparison_dict = {compound_name.iloc[i, 0]: compound_name.iloc[i, 1] for i in range(compound_name.shape[0])}
        self.voc_nox_mean = calculate_noxvoc(deepcopy(self.data), comparison_dict)
        self.data = do_mean(self.data)
        self.data = transfrom(self.data)
        self.data.dropna(thresh=15, axis=1, inplace=True)
        drop_columns = list(set(self.data.columns) - set(comparison_dict.keys()))
        self.data.drop(drop_columns, axis=1, inplace=True)
        self.data.rename(columns={i: comparison_dict[i] for i in self.data.columns}, inplace=True)
        data_time = self.data.index.to_list()
        self.YEAR = int(data_time[0][:4])
        self.MONTH = int(data_time[0][5:7])
        self.DAY = int(data_time[0][8:10])
        HOUR = [int(i[-5:-3]) for i in data_time]
        HOUR_lost = list(set(range(24)) - set(HOUR))
        self.data.set_index(Series(HOUR), inplace=True)
        for i in HOUR_lost:
            self.data.loc[i] = float("nan")
        self.data.sort_index(inplace=True)
        M, N = self.data.shape
        if self.data.isna().sum().sum() > M * N * 0.4:
            log_write(log_file, "Data missing by more than 40% and procedure interrupted!\n")
            raise ValueError("Data missing by more than 40%!")
        self.data.interpolate(limit_direction="both", inplace=True)
        self.data[self.data < 0] = 0
        toppb = {"NO": 1.339, "NO2": 2.054, "O3": 2.143, "CO": 0.00125, "SO2": 3.392}  # 后端传入的NOx，O3，CO，SO2单位转换
        toppb_name = set(toppb.keys()) & set(self.data.columns)
        for name in toppb_name:
            self.data[name] = self.data[name] / toppb[name]

    def do_simulation(self):  # 我有预见到这模型可以运行，但终究会变成屎山，维护难度加大，可以考虑拆分功能，找个时间写写注释吧
        M, N = self.data.shape
        # extra rule
        for i in self.data.columns:
            if i not in Do_simulation.threshold.keys() and i not in {"NO", "NO2", "O3", "CO", "T", "P", "H", "PAR",
                                                                     "NR"}:
                self.data.loc[self.data[i] > 30, i] = 30
            elif i in Do_simulation.threshold.keys():
                self.data.loc[self.data[i] > Do_simulation.threshold[i], i] = Do_simulation.threshold[i]

        # extra rule2
        PRESSURE = [1001] * M
        if 6 < self.MONTH <= 10:
            TEMPERATURE = Do_simulation.tem_summer
            HUMIDITY = Do_simulation.hum_summer
        elif self.MONTH < 3 or self.MONTH > 11:
            TEMPERATURE = Do_simulation.tem_winter
            HUMIDITY = Do_simulation.hum_winter
        else:
            TEMPERATURE = [(i + j) / 2 for i, j in zip(Do_simulation.tem_summer, Do_simulation.tem_winter)]
            HUMIDITY = [(i + j) / 2 for i, j in zip(Do_simulation.hum_summer, Do_simulation.hum_winter)]
        if "T" in self.data.columns:  # 如果监测数据data中有T，且输入T为-1，则用监测数据。如果输入T不为-1，用输入T代表温度
            TEMPERATURE = self.data["T"].tolist() if self.climate[1] == -1 else [self.climate[1]] * M
        if "P" in self.data.columns:
            PRESSURE = (self.data["P"] * 10).tolist() if self.climate[0] == -1 else [self.climate[0]] * M
        if "H" in self.data.columns:
            HUMIDITY = self.data["H"].tolist() if self.climate[2] == -1 else [self.climate[2]] * M

        # CB05 model
        columns_set = set(self.data.columns)
        voc_name = columns_set - {"T", "P", "H", "O3", "SO2", "CO", "NO", "NO2", "PAR", "OLE", "TOL", "XYL", "FORM",
                                  "ALD2",
                                  "ETH", "ISOP", "MEOH", "ETOH", "NR", "ETHA", "IOLE", "ALDX", "TERP", "MGLY", "ISPD",
                                  "AACD"}
        """
        iole = {"CPENT2ENE", "TBUT2ENE", "CBUT2ENE", "TPENT2ENE"} & columns_set
        ole = {"PENT1ENE", "C3H6", "HEX1ENE", "C4H6", "STYRENE", "C5H8", "BUT1ENE"} & columns_set
        tol = {"TOLUENE", "EBENZ", "IPBENZ", "PBENZ"} & columns_set
        xyl = {"OXYL", "PETHTOL", "METHTOL", "TM124B", "OETHTOL", "TM135B", "TM123B", "PXYL", "MXYL"} & columns_set
        mgly = {"BENZAL", "MACR"} & columns_set
        aldx = {"ACR", "BENZAL", "MACR", "C3H7CHO", "C4H9CHO", "C4ALDB", "C2H5CHO", "MXYLAL"} & columns_set
        par = columns_set - (iole | ole | tol | xyl | mgly | aldx | {"SO2", "O3", "CO", "NO", "NO2", "NO3", "HONO",
                                                            "CH4", "HCHO", "HCOOH", "C2H2", "C2H4", "T", "P", "H"})
        etha, ispd, eth, isop, ald2, etoh, meoh, form = {"C2H6"} & columns_set, {"MACR"} & columns_set, {"C2H4"} & columns_set,\
        {"C5H8"} & columns_set, {"CH3CHO"} & columns_set, {"C2H5OH"} & columns_set, {"CH3OH"} & columns_set, {"HCHO"} & columns_set
        # RO2: XO2 XO2N MEO2 TO2
        # olefin: iole ole eth isop terp
        # aromatics: xyl tol mgly open
        # ovocs: ald2 aldx form etoh meoh facd rooh aacd pacd cres
        # alkanes: par
        CB05_species = ["IOLE", "OLE", "TOL", "XYL", "MGLY", "ALDX", "PAR",
                        "ETHA", "ISPD", "ETH", "ISOP", "ALD2", "ETOH", "MEOH", "FORM"]
        CB05_species_set = [iole, ole, tol, xyl, mgly, aldx, par, etha,
                            ispd, eth, isop, ald2, etoh, meoh, form]
        for i, j in zip(CB05_species, CB05_species_set):
            self.data[i] = self.data[list(j)].sum(axis=1)
        """
        # preparation for model
        HOUR, MIN, SEC, UTC = self.data.index.to_list(), 0, 0, 8
        time = {"year": self.YEAR, "month": self.MONTH, "day": self.DAY, "hour": HOUR, "min": MIN, "sec": SEC,
                "UTC": UTC}
        sun = sun_position(time, self.location)
        Met = {"P": PRESSURE, "T": [i + 273.15 for i in TEMPERATURE], "RH": HUMIDITY, "SZA": sun["zenith"], "kdil":
            self.control[0], "jcorr": self.control[2], "ALT": self.location["altitude"], "O3col": self.control[3],
               "albedo": self.control[4]}
        J = {i for i in columns_set if i[0] == "J"}
        Met.update({i: self.data[i].tolist() for i in J})
        ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)",
                     "CB05_AllRxns")  # ("MCMv331_K(Met)","MCMv331_J(Met,0)","mcm_subset2")
        BkgdConc = {"DEFAULT": self.control[1]}
        ModelOptions = {"Verbose": 0, "EndPointsOnly": 1, "LinkSteps": self.control[5], "Repeat": 1, "IntTime": 3600,
                        "SavePath": "DoNotSave", "FixNOx": self.control[6], "TimeStamp": HOUR}

        ioa, O3_Max = data_run(Met, deepcopy(self.data), ChemFiles, BkgdConc, ModelOptions,
                               self.I_ARRAY, self.J_ARRAY, self.iHold)  # type -> np.ndarray

        O3_Max = array(O3_Max).reshape((len(self.I_ARRAY), len(self.J_ARRAY))).round(3)
        y_value = round(self.data[["NO2", "NO"]].sum(axis=1).mean(), 3)
        x_value = round(self.data[list(voc_name)].sum(axis=1).mean(), 3)
        re = {str(i): O3_Max[:, i].tolist() for i in range(O3_Max.shape[0])}  # 将O3_Max转化为字典re，字典的值为数组
        result = {}
        result.update({"data": re})  # 添加进result，此变量的str为发送给后端的变量
        result.update({"ioa": str(ioa)})  # 添加相符指数IOA
        result.update({"y_value": str(y_value), "x_value": str(x_value)})  # 添加点的横纵坐标
        result.update({"y": self.voc_nox_mean[0], "x": self.voc_nox_mean[1]})  # 添加散点的横纵坐标
        a, b = gradient2(x_value * array(self.J_ARRAY), y_value * array(self.I_ARRAY), O3_Max)  # 求脊线的a，b值，y=ax+b
        result.update({"a": round(a, 2), "b": round(b, 2)})  # 添加a，b值进入result

        return result


def check_file(file):
    if not exists(file):
        log_write(log_file, f"{file} not exists! exit!\n")
        exit()


def log_write(log_file, msg):
    with open(log_file, "ab", buffering=0) as f:
        f.write((datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + msg).encode("utf-8"))
        f.close()


"""
def error_decoration(func):
    def wrapper(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except Exception:
            sign="="*60+"\n"
            with open(log_file, "a+") as f:
                f.write(f"{sign}异常时间: >>>\t"+datetime.now().strftime("%Y-%m-%d:%M")+f">>>异常函数: \t{func.__name__}\n"+\
                        f"异常信息: \t{Exception}")
            exit()
    return wrapper
"""


def gradient2(x, y, data, times=1000, eta=1e-1):  # BGD  # 参考Tool/plot_EKMA.py注释

    x_new, y_new = arange(0, len(x) - 0.75, 0.25), arange(0, len(y) - 0.75, 0.25)
    x_n, y_n = range(len(x)), range(len(y))
    z = interp2d(x_n, y_n, data, kind="cubic")(x_new, y_new)
    x = interp1d(x_n, x, kind="cubic")(x_new)
    y = interp1d(y_n, y, kind="cubic")(y_new)

    data_grad_x, data_grad_y = gradient(z)
    y_loc, x_loc = unravel_index(argmax(z), z.shape)
    x_, y_ = x[x_loc], y[y_loc]
    re_x, re_y = [x_], [y_]
    fit_x = interp2d(x, y, data_grad_x, kind="linear")
    fit_y = interp2d(x, y, data_grad_y, kind="linear")
    for i in range(times):
        if x_ < -5 or y_ < -5:
            break
        x_2, y_2 = x_, y_
        x_ = x_2 - eta * (fit_x(x_2, y_2))
        y_ = y_2 - eta * (fit_y(x_2, y_2))
        re_x.append(float(x_))
        re_y.append(float(y_) + 5)

    re = polyfit(re_x, re_y, deg=1)

    return re


def start_simulation(receive_string: str):
    # check_file(compound_name_file)

    start_time = datetime.now()
    log_write(log_file, "EKMA starting @(o･ｪ･o)@ @(o･ｪ･o)@ @(o･ｪ･o)@\n")

    simulation = Do_simulation(loads(receive_string))  # 实例化一个情景
    simulation.do_process()  # 调用该情景的do_process方法，处理该实例本身的数据
    re = simulation.do_simulation()  # 调用该情景的do_simulation方法，模拟该情景

    log_write(log_file,
              f"EKMA ending, Total cost time: {(datetime.now() - start_time).seconds}s @(｡･o･)@ @(｡･o･)@ @(｡･o･)@.\n")

    return re
