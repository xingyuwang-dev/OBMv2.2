from pandas import read_csv, to_datetime
from datetime import datetime, timedelta
from os import makedirs, sep
from os.path import exists, dirname
from sys import exit
from core.RIR_data_process import data_processed
from core.RIR_data_run2 import initialize, update
from tool.data_average import do_mean
import csv
from post_process import plot_ozone, plot_OH, plot_photolysis
from functools import partial
from tool.file_transform import file_transform


# 此为OBM软件的RIR模块，不是程序的主入口，入口位于UI.py
# 此结构与语句与OBM_RIR.py类似，因此相同地方不再解释


def main(T=0, init=False):
    arg1, arg2 = [pressure, temperature, humidity], [kdil, bkgdconc, jcorr, o3col, albedo, linksteps, fixnox]
    data = read_csv(data_file_, header=0, index_col=0)
    data.index = to_datetime(data.index)
    data.index = map(lambda x: x.strftime("%Y/%m/%d %H/%M"), data.index)
    data = do_mean(data)
    compound_name = read_csv(compound_name_file, header=None)
    if init:
        data2, time, climate = data_processed(data, compound_name, arg1)
    else:
        data = data.iloc[[T]]
        data2, time, climate = data_processed(data, compound_name, arg1)
    location = {"latitude": LATITUDE, "longitude": LONGITUDE, "altitude": ALTITUDE}
    if init:
        initialize(data2, time, climate, location, arg2, save_path, ihold)
    else:
        result = update(data2, time, climate, location, arg2, save_path, ihold)

    if init:
        head1 = ["Time", "RO2", "OH", "HO2", "HONO"]
        head2 = ["Time", "O3_G", "O3_D", "HO2+NO", "RO2+NO", "O3_photolysis", "O3+OH", "O3+HO2", "NO2+OH", "O3+olefin"]
        head3 = ["Time", "CO_10", "NOx_10", "VOCs_10", "olefin_10", "aromatics_10", "ovocs_10"]
        head4 = ["Time", "SO2", "Aromatics", "Alkanes", "Alkenes", "NO2", "HNO3", "NO", "HO2NO2", "HONO", "HO2", "CO",
                 "CH4", "OVOCs"]
        head5 = ["Time", "NOx(-10%)", "NOx(-20%)", "NOx(-30%)", "VOCs(-10%)", "VOCs(-20%)", "VOCs(-30%)"]
        head6 = ["Time", "VOCs_NOx_10", "VOCs_NOx_20", "VOCs_NOx_30"]
        head7 = ["Time", "J_O1D", "J_HCHO_R", "J_HCHO_M", "J_NO2", "J_H2O2", "J_HONO", "J_NO3_b", "J_NO3_a"]

        write_csv(save_path + sep + data_file1, head1)
        write_csv(save_path + sep + data_file2, head2)
        write_csv(save_path + sep + data_file3, head3)
        write_csv(save_path + sep + data_file6, head4)
        write_csv(save_path + sep + data_file5, head5)
        write_csv(save_path + sep + data_file8, head6)
        write_csv(save_path + sep + data_file7, head7)

    else:
        write_csv(save_path + sep + data_file1, result[0], "a+")
        write_csv(save_path + sep + data_file2, result[1], "a+")
        write_csv(save_path + sep + data_file3, result[2], "a+")
        write_csv(save_path + sep + data_file6, result[3], "a+")
        write_csv(save_path + sep + data_file5, result[4], "a+")
        write_csv(save_path + sep + data_file8, result[5], "a+")
        write_csv(save_path + sep + data_file7, result[6], "a+")


def check_file(file):
    if not exists(file):
        log_write(log_file, f"{file} not exists! exit!\n")
        exit()


def log_write(log_file, msg):
    with open(log_file, "a+") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + msg)


def write_csv(path, data, model="w"):
    with open(path, model, encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(data)


DATE = (datetime.now() + timedelta(days=-1)).strftime("%Y/%m/%d")

main_path = dirname(__file__)
# data_file = main_path + sep + "data2.csv"
# data_file_ = main_path + sep + "data2.csv"
compound_name_file = main_path + sep + "comparison_table.csv"
# save_path_ = main_path + sep + DATE
log_file = main_path + sep + "init_log.txt"
log_file2 = main_path + sep + "update_log.txt"

data_file1 = "free_radical_concentration.csv"
data_file2 = "rate_of_ozone_generation.csv"
data_file3 = "RIR.csv"
data_file6 = "reactivity_of_OH_reaction.csv"
data_file5 = "VOCssub_or_NOxsub.csv"
data_file8 = "VOCssub_and_NOxsub.csv"
data_file7 = "photolysis_rate.csv"

check_file(main_path)
check_file(compound_name_file)


def if_do(send_dict, key, value, fun=str):  # 此函数会应用于一个偏函数，用于检验RIR模块所需得到参数
    if send_dict[key] != "":  # 如果为""
        if fun != str:  # 如果不为str，对send_dict[key]应用fun函数
            return fun(send_dict[key])
        else:
            return send_dict[key]
    else:
        return value


def RIR_start(send_dict):
    global data_file, data_file_, LONGITUDE, LATITUDE, ALTITUDE, kdil, jcorr, bkgdconc, o3col
    global save_path, albedo, linksteps, fixnox, ihold, temperature, pressure, humidity
    check_parameter = partial(if_do, send_dict)
    data_file = check_parameter("data", "")  # 参考OBM_EKMA_1day2.py
    data_file_ = check_parameter("data2", "")
    check_file(data_file)
    check_file(data_file_)
    data_file = file_transform(data_file)
    data_file_ = file_transform(data_file_)
    save_path = check_parameter("save_path", main_path + sep + DATE)
    LONGITUDE = check_parameter("longtitude", 121.43, float)
    LATITUDE = check_parameter("latitude", 28.68, float)
    ALTITUDE = check_parameter("altitude", 30, float)
    temperature = check_parameter("temperature", -1, float)
    pressure = check_parameter("pressure", -1, float)
    humidity = check_parameter("humidity", -1, float)
    kdil = check_parameter("kdil", 1 / 86400, float)
    jcorr = check_parameter("jcorr", 1, float)
    bkgdconc = check_parameter("bkgdconc", 1, float)
    o3col = check_parameter("o3col", 300, int)
    albedo = check_parameter("albedo", 0.3, float)
    ihold = check_parameter("ihold", 1, int)
    linksteps = check_parameter("linksteps", 1, int)
    fixnox = check_parameter("fixnox", 0, int)

    if not exists(save_path):
        makedirs(save_path)

    start_time = datetime.now()
    init = True
    log_write(log_file, "RIR initialize starting\n")
    main(0, init)
    log_write(log_file, "RIR initialize ending\n")
    init = False
    log_write(log_file2, "RIR update starting\n")
    for i in range(24):
        main(i, init)
    log_write(log_file2, "RIR update ending\n")

    plot_ozone.plot_ozone(save_path + sep + data_file2, save_path)
    plot_OH.plot_OH(save_path + sep + data_file6, save_path)
    plot_photolysis.plot_photolysis(save_path + sep + data_file7, save_path)

    end_time = datetime.now()
    cost_seconds = (end_time - start_time).seconds
    log_write(log_file2, f"Total cost time: {cost_seconds}s.\n")
    return "1"
