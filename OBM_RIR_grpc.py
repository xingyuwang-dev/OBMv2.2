from pandas import read_csv, DataFrame
from datetime import datetime
from os.path import exists, dirname
from os import sep, makedirs, getpid, getppid
from json import loads
from RIR_data_process import data_processed
from RIR_data_run2 import initialize, update, initialize_update
from Tool.data_split import do_split
from copy import deepcopy
from sys import exit


# 此为线上运行OBM模型的RIR模块，相对于OBM_RIR.py增加了情景削减模式


main_path = "/Users/xingyuwang/Desktop/OBM_RIR"  # 在线上版本和OBM软件会被替换为dirname(__file__)，采用相对路径！！！
compound_name_file = main_path + sep + "comparison_table.csv"
log_file = main_path + sep + "init_log.txt"
log_file2 = main_path + sep + "update_log.txt"
compound_name = read_csv(compound_name_file, header=None)


class Do_simulation:
    head0 = ["Time", "RO2", "OH", "HO2", "HONO"]
    head1 = ["Time", "O3_G", "O3_G", "HO2+NO", "RO2+NO", "O3_photolysis", "O3+OH", "O3+HO2", "NO2+OH", "O3+olefin"]
    head2 = ["Time", "CO_10", "NOx_10", "VOCs_10", "olefin_10", "aromatics_10", "ovocs_10"]
    head3 = ["Time", "SO2", "Aromatics", "Alkanes", "Alkenes", "NO2", "HNO3", "NO", "HO2NO2", "HONO", "HO2", "CO", "CH4", "OVOCs"]
    head4 = ["Time", "NOx(-10%)", "NOx(-20%)", "NOx(-30%)", "VOCs(-10%)", "VOCs(-20%)", "VOCs(-30%)"]
    head5 = ["Time", "VOCs_NOx_10", "VOCs_NOx_20", "VOCs_NOx_30"]
    head6 = ["Time", "J_O1D", "J_HCHO_R", "J_HCHO_M", "J_NO2", "J_H2O2", "J_HONO", "J_NO3_b", "J_NO3_a"]

    def __init__(self, rec_str: dict):
        try:
            self.data = DataFrame(rec_str["data"]).set_index("DATETIME")
        except KeyError:
            raise KeyError("Check your data!")
        try:
            self.init = int(rec_str["init"])
            self.climate = [float(rec_str["p"]), float(rec_str["t"]), float(rec_str["h"])]
            self.climate2 = {}
            self.control = [float(rec_str["kdil"]), float(rec_str["bkgdconc"]), float(rec_str["jcorr"]),
                            float(rec_str["o3col"]), float(rec_str["albedo"]), float(rec_str["linksteps"]),
                            float(rec_str["fixnox"])]
            self.location = {"latitude": float(rec_str["latitude"]), "longitude": float(rec_str["longitude"]),
                             "altitude": float(rec_str["altitude"])}
            self.save_path = main_path + sep + "json_file" + sep + str(rec_str["random_id"])  # 根据id确定不同站点的中间变量保存路径
            self.iHold = int(rec_str["ihold"])
            if self.init == 2:  # 当init==2，表明是情景削减模式，需要指定VOCs与NOx削减比例
                self.vocs_cut = float(rec_str["vocs_cut"])
                self.nox_cut = float(rec_str["nox_cut"])
        except KeyError:
            raise KeyError("Check your parameter!")
        self.time = 0
        try:
            makedirs(self.save_path)
        except FileExistsError:
            pass
        if not self.data.__contains__("10102-44-0") or not self.data.__contains__("10102-43-9"):
            raise KeyError("Absence of NO, or NO2!")

    def do_simulation(self):
        if self.init == 1:  # 如果处于预热模式，调用data_processed处理数据后，调用initialize初始化
            data2, self.time, self.climate2 = data_processed(self.data, compound_name, self.climate)
            initialize(data2, self.time, self.climate2, self.location, self.control, self.save_path, self.iHold)

            return "initialization done!"  # 返回后端的字符串
        elif self.init == 0:  # 如果处于更新模式
            check_file(self.save_path + sep + "result.json")  # 查看是否有预热模式生成的result.json存在
            for i in range(self.data.shape[0]):  # 循环，先处理数据，后调用update更新，update会更新result.json
                data2, self.time, self.climate2 = data_processed(self.data.iloc[[i]], compound_name, self.climate)
                result = update(data2, self.time, self.climate2, self.location, self.control, self.save_path, self.iHold, True)

                result0 = [{i: j for i, j in zip(Do_simulation.head0, result[0])}]
                result1 = [{i: j for i, j in zip(Do_simulation.head1, result[1])}]
                result2 = [{i: j for i, j in zip(Do_simulation.head2, result[2])}]
                result3 = [{i: j for i, j in zip(Do_simulation.head3, result[3])}]
                result4 = [{i: j for i, j in zip(Do_simulation.head4, result[4])}]
                result5 = [{i: j for i, j in zip(Do_simulation.head5, result[5])}]
                result6 = [{i: j for i, j in zip(Do_simulation.head6, result[6])}]

                re_tmp = {"r0": result0, "r1": result1, "r2": result2,
                          "r3": result3, "r4": result4, "r5": result5,
                          "r6": result6}
                if i == 0:  # 将结果转化为类似于JSON字符串的字典
                    re = deepcopy(re_tmp)
                else:
                    for j in re_tmp.keys():
                        re[j] += re_tmp[j]

            return re
        else:  # 如果处于情景削减模式，先调用do_split将数据按照日期拆分，对每个日期的数据调用data_process处理，之后用initilize_update进行并行处理
            data_list = do_split(self.data, compound_name, self.climate)
            result = initialize_update(data_list, self.control, self.location, self.iHold, self.vocs_cut, self.nox_cut)

            return result


def check_file(file):
    if not exists(file):
        log_write(log_file, f"{file} not exists! exit!\n")
        exit()


def log_write(log_file, msg):
    with open(log_file, "ab", buffering=0) as f:
        f.write((datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + msg).encode("utf-8"))
        f.close()


def start_simulation(receive_string: str):
    receive_dict = loads(receive_string)
    init = receive_dict["init"]
    mn = receive_dict["random_id"]
    check_file(compound_name_file)
    print(datetime.now(), " 当前进程ID:", getpid(), " 当前进程主进程ID:", getppid(), "mn:", mn, flush=True)
    start_time = datetime.now()

    if init == 1:  # 预热
        log_write(log_file, mn+"RIR initialize starting @(o･ｪ･o)@\n")

        simulation = Do_simulation(loads(receive_string))
        re = simulation.do_simulation()

        log_write(log_file, mn+"RIR initialize ending, " + f"Total cost time: {(datetime.now() - start_time).seconds}s @(｡･o･)@.\n")
    else:
        log_write(log_file2, mn+"RIR update starting @(o･ｪ･o)@\n")

        if init == 0:  # 更新 or 数据补齐
            simulation = Do_simulation(loads(receive_string))
            re = simulation.do_simulation()

            log_write(log_file2, mn + "RIR update ending, " + f"Total cost time: {(datetime.now() - start_time).seconds}s @(｡･o･)@.\n")
        else:  # 多天RIR实时，情景削减模式
            simulation = Do_simulation(loads(receive_string))
            re = simulation.do_simulation()

    return re