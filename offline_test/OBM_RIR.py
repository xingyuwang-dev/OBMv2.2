from pandas import read_csv, to_datetime
from datetime import datetime, timedelta
from os import makedirs, sep
from os.path import exists
from sys import exit
from core.RIR_data_process import data_processed
from core.RIR_data_run2 import initialize, update
from tool.data_average import do_mean
import csv
from post_process import plot_ozone, plot_OH, plot_photolysis
from tool.file_transform import file_transform


# 此脚本为现在开发，测试所用的OBM模型的RIR模块线下版本，所有与RIR有关的计算从此开始
# __main__表明其为一个程序主入口，可以线下单独运行。和线上版本与OBM软件版本在逻辑与结构上有较大的相似性
# 需要解释的是RIR模块和EKMA模块一样都需要预热，预热主要的作用是先跑一遍模型，将监测数据中没有的，而模型包含的物种的浓度数据添加到监测数据中
# EKMA模块的预热方法data_run.py，RIR的预热方法放在RIR_data_run.py下
# 由于RIR模块包含三种运行方式，1:预热模式，2:更新模式，3:情景削减模式，因此将数据处理方法单独拆分为RIR_data_process.py
# 此只介绍1与2，情景削减模式在RIR模块线上版本会进行介绍。1:当init==1(每天0:30分)，进行预热，将预热数据按照站点编号保存到json_file文件夹
# 2:当init==0(每小时10分)，进行更新，并且更新(不创建)json_file文件夹下保存的中间结果。注意预热与更新是先后运行的，更新发现不到json_file下对应文件就会退出


def main(T_=0, init=False):
    arg1, arg2 = [P, T, H], [kdil, bkgdconc, jcorr, 300, 0.3, 1, 0]
    data = read_csv(data_file_, header=0, index_col=0)  # 读取数据为DataFrame格式，设置列名为表头，索引为第一列
    data.index = to_datetime(data.index)  # 将索引转化为时间格式
    data.index = map(lambda x: x.strftime("%Y/%m/%d %H/%M"), data.index)  # 将索引转化为特定字符串格式
    data = do_mean(data)  # 计算日平均值
    compound_name = read_csv(compound_name_file, header=None)  # 读取对照表
    if init:  # 预热模式，调用数据处理方法
        data2, time, climate = data_processed(data, compound_name, arg1)
    else:  # 非预热模式，对数据的第T_行调用数据处理方法，表示第T_个小时的数据；注意入口处对main的循环！！！
        data = data.iloc[[T_]]
        data2, time, climate = data_processed(data, compound_name, arg1)
    location = {"latitude": LATITUDE, "longitude": LONGITUDE, "altitude": ALTITUDE}
    if init:  # 调用RIR_data_run下的initialize方法进行预热，此方法专用于预热
        initialize(data2, time, climate, location, arg2, save_path)
    else:  # 调用RIR_data_run下的update方法进行更新，此方法专用于更新
        result = update(data2, time, climate, location, arg2, save_path)

    if init:  # head$n表示了那7张RIR输出的表的表头，预热模式写入表头
        head1 = ["Time", "RO2", "OH", "HO2", "HONO"]
        head2 = ["Time", "O3_G", "O3_D", "HO2+NO", "RO2+NO", "O3_photolysis", "O3+OH", "O3+HO2", "NO2+OH", "O3+olefin"]
        head3 = ["Time", "CO_10", "NOx_10", "VOCs_10", "olefin_10", "aromatics_10", "ovocs_10"]
        head4 = ["Time", "SO2", "Aromatics", "Alkanes", "Alkenes", "NO2", "HNO3", "NO", "HO2NO2", "HONO", "HO2", "CO",
                 "CH4", "OVOCs"]
        head5 = ["Time", "NOx(-10%)", "NOx(-20%)", "NOx(-30%)", "NOx(-40%)", "VOCs(-10%)", "VOCs(-20%)", "VOCs(-30%)",
                 "VOCs(-40%)"]
        # head6 = ["Time", "VOCs_NOx_10", "VOCs_NOx_20", "VOCs_NOx_30"]  # 此是正常默认的设置
        head6 = ["Time", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "b10", "b11", "b12"]  # 注意，此是为了专门跑程玉立的需求
        head7 = ["Time", "J_O1D", "J_HCHO_R", "J_HCHO_M", "J_NO2", "J_H2O2", "J_HONO", "J_NO3_b", "J_NO3_a"]

        write_csv(data_file1, head1)
        write_csv(data_file2, head2)
        write_csv(data_file3, head3)
        write_csv(data_file6, head4)
        write_csv(data_file5, head5)
        write_csv(data_file8, head6)
        write_csv(data_file7, head7)

    else:  # 更新模式写入数据，每小时写入一行，a+表示为追加写入模式
        write_csv(data_file1, result[0], "a+")
        write_csv(data_file2, result[1], "a+")
        write_csv(data_file3, result[2], "a+")
        write_csv(data_file6, result[3], "a+")
        write_csv(data_file5, result[4], "a+")
        write_csv(data_file8, result[5], "a+")
        write_csv(data_file7, result[6], "a+")


def check_file(file):
    if not exists(file):
        log_write(log_file, f"{file} not exists! exit!\n")
        exit()


def log_write(log_file, msg):
    with open(log_file, "a+") as f:
        f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + msg)


def write_csv(path, data, model="w"):  # 写csv的函数
    with open(path, model, encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(data)


DATE = (datetime.now() + timedelta(days=-1)).strftime("%Y/%m/%d")  # 和EKMA模块线下版本一样的作用，用来表明存放结果的路径
LONGITUDE, LATITUDE, ALTITUDE = 121.43, 28.68, 30
P, T, H, kdil, bkgdconc, jcorr = -1, -1, -1, 1 / 86400, 1, 1

main_path = "/Users/xingyuwang/Desktop/OBM_RIR"
data_file = main_path + sep + "6月OBM输入数据.xlsx"  # 更新数据
data_file_ = main_path + sep + "6月OBM输入数据.xlsx"  # 预热数据
compound_name_file = main_path + sep + "comparison_table.csv"
save_path = main_path + sep + DATE  # 保存路径
log_file = main_path + sep + "init_log.txt"  # 预热模式的log文件
log_file2 = main_path + sep + "update_log.txt"  # 更新模式的log文件

data_file1 = save_path + sep + "free_radical_concentration.csv"  # 自由基浓度
data_file2 = save_path + sep + "rate_of_ozone_generation.csv"  # 臭氧生成速率
data_file3 = save_path + sep + "RIR.csv"  # RIR
data_file6 = save_path + sep + "reactivity_of_OH_reaction.csv"  # OH反应活性
data_file5 = save_path + sep + "VOCssub_or_NOxsub.csv"  # VOCs与NOx单一削减
data_file8 = save_path + sep + "VOCssub_and_NOxsub.csv"  # VOCs与NOx协同削减
data_file7 = save_path + sep + "photolysis_rate.csv"  # 光解速率

if not exists(save_path):
    makedirs(save_path)

check_file(main_path)
check_file(data_file)
check_file(data_file_)
data_file = file_transform(data_file)  # 转换数据文件为csv，在此过程中会剔出Flag标，将中文表头转换为cas号
data_file_ = file_transform(data_file_)
check_file(compound_name_file)

if __name__ == "__main__":
    start_time = datetime.now()
    init = True  # 预热模式
    log_write(log_file, "RIR initialize starting\n")  # 写预热日志
    main(0, init)  # 预热
    log_write(log_file, "RIR initialize ending\n")  # 写预热日志
    init = False  # 更新
    log_write(log_file2, "RIR update starting\n")  # 写更新日志
    for i in range(24):  # 循环调用main，更新每个小时结果。 为什么要循环？为了兼容线上版本的一个小时才有一条数据的情况！
        main(i, init)
    log_write(log_file2, "RIR update ending\n")  # 写更新日志

    plot_ozone.plot_ozone(data_file2, save_path)  # 画臭氧生成速率图
    plot_OH.plot_OH(data_file6, save_path)  # 画OH反应活性图
    plot_photolysis.plot_photolysis(data_file7, save_path)  # 画光解速率图

    end_time = datetime.now()
    cost_seconds = (end_time - start_time).seconds
    log_write(log_file2, f"Total cost time: {cost_seconds}s.\n")
