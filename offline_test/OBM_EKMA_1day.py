from pandas import read_csv, Series, to_datetime
from numpy import arange, savetxt, array
from datetime import datetime, timedelta
from os import makedirs, sep
from os.path import exists, dirname
from sys import exit
from tool.sun_position import sun_position
from core.data_run import data_run
from copy import deepcopy
from post_process.plot import plot_EKMA
from tool.data_average import do_mean, calculate_noxvoc
from tool.victory import victory
from CB05.CB05_transfrom import transfrom
from tool.file_transform import file_transform

# 此为线下开发，测试时运行的OBM模型的EKMA模块入口，非线上版本，非OBM软件版本
# 后缀1day表明其处理数据的基础为1天，输入为多天的话会将数据平均到一天
# 线上版本和OBM软件版本是基于此入口再次封装而成的，主体逻辑与结构不会有太大的变化；线上加入了类作为多线程计算中防止共享变量的技术，
# 软件则利用UI.py进行传参。
# 详情请阅读注释，有关模型输入参数设置参考matlab软件的F0AM_ModelCore里面的文档


DATE = (datetime.now() + timedelta(days=-1)).strftime("%Y/%m/%d")  # 此日期用来生成前一天的日期，将其作为结果的保存路径
LONGITUDE, LATITUDE, ALTITUDE = 121.43, 28.68, 30  # 默认经纬度与海拔
I_ARRAY, J_ARRAY = arange(0.1, 3.7, 0.3), arange(0.1, 3.7, 0.3)  # 默认VOCs情景，NOx情景

main_path = "/Users/xingyuwang/Desktop/OBM_EKMA/"  # 主路径，读取数据来源，保存数据位置
data_file = main_path + sep + "202351-531VOCs小时数据（已剔检出限低值）(3)_.csv"  # 监测数据
compound_name_file = main_path + sep + "comparison_table.csv"  # 主路径下存放的转换表
save_path = main_path + sep + DATE  # 保存路径
log_file = main_path + sep + "log.txt"  # 日志保存路径
# 监测数据可能没有温度，湿度，气压等数据
tem_summer = [26.1, 26, 25.9, 25.4, 25, 25.1, 25.2, 25.9, 27.7, 28.4, 28.7, 28.2,  # 默认夏天温度，来源于浙江
              28, 26.2, 26.7, 27.3, 27.4, 27.2, 26.6, 26.6, 26.4, 26.5, 26.5, 26.5]
tem_winter = [6.7, 6.4, 6.1, 5.7, 6, 5.9, 5.6, 6.1, 6.5, 7, 7.3, 7.6,  # 默认冬天温度，来源于～
              7.7, 8, 8.3, 8.5, 8.6, 8.2, 8, 7.7, 7.6, 7.6, 7.6, 7.1]
hum_summer = [95.2, 93.1, 93.3, 94.2, 95.6, 96.7, 99.2, 95.1, 81.3, 78.5, 77, 79.5,  # 默认夏天湿度，来源～
              81.3, 95.1, 94.4, 90.6, 90.8, 90.4, 94.2, 96.8, 99.4, 99.8, 98.6, 98]
hum_winter = [74.7, 76.4, 76.8, 77.3, 75.6, 73.6, 75.6, 72.6, 70.1, 69.1, 68.6, 65.2,  # 默认冬天湿度，来源～
              66.2, 64.6, 61.6, 59.7, 59.8, 61.5, 64.2, 65.9, 66.9, 68.6, 69.3, 71.2]
compound_name = read_csv(compound_name_file, header=None)  # 读取转换表

if not exists(save_path):  # 如果保存路径不存在，创建
    makedirs(save_path)


def main():  # 将两列的转换表转换为字典，第一列数据为key，第二列数据为value
    comparison_dict = {compound_name.iloc[i, 0]: compound_name.iloc[i, 1] for i in range(compound_name.shape[0])}
    data = read_csv(data_file, header=0, index_col=0)  # 读取监测数据，设置列名为表头，索引为第一列
    data.index = to_datetime(data.index)  # 将监测数据索引转换为时间格式
    data.index = map(lambda x: x.strftime("%Y/%m/%d %H/%M"), data.index)  # 对data的索引应用时间格式
    voc_mean, nox_mean = calculate_noxvoc(data, comparison_dict)  # 计算每天的vocs与nox的平均值，可能返回多天
    data = do_mean(data)  # 将数据平均到一天
    data = transfrom(data)  # 计算模型物种并添加到data中
    data[data < 0] = 0  # 0值规约

    data.dropna(thresh=15, axis=1, inplace=True)  # 删除nan多于thresh的列
    drop_columns = list(set(data.columns) - set(comparison_dict.keys()))  # 需要删除的列名，因为这些列不在对照表中
    data.drop(drop_columns, axis=1, inplace=True)
    data.rename(columns={i: comparison_dict[i] for i in data.columns}, inplace=True)  # 替换列名为对照表中的第二列
    data_time = data.index.to_list()  # 提取索引为时间
    YEAR = int(data_time[0][:4])
    MONTH = int(data_time[0][5:7])
    DAY = int(data_time[0][8:10])
    HOUR = [int(i[-5:-3]) for i in data_time]
    HOUR_lost = list(set(range(24)) - set(HOUR))  # 判断缺失的小时值
    data.set_index(Series(HOUR), inplace=True)  # 设置索引为小时值
    for i in HOUR_lost:  # 将data中缺失的小时的所有值用nan补上
        data.loc[i] = float("nan")
    data.sort_index(inplace=True)  # 将data用索引进行排序

    M, N = data.shape
    if data.isna().sum().sum() > M * N * 0.4:  # 判断如果现有的nan值大于40%，则写入日志这一情况，并中断程序
        log_write(log_file, "Data is missing more than 40% and procedure interrupted!\n")
        exit()
    data.interpolate(limit_direction="both", inplace=True)  # 插值nan

    # extra rule  # 此rule用来规约监测得到的浓度过大的情况
    threshold = {"C5H8": 5, "HCHO": 50, "CH3CHO": 50, "CH3CL": 10, "VINCL": 10, "CH2CL2": 10, "CH2CLCHCL2": 10,
                 "CHCL2CHCL2": 10}
    for i in data.columns:
        if i not in threshold.keys() and i not in {"NO", "NO2", "O3", "CO", "T", "P", "H", "PAR"}:
            data.loc[data[i] > 30, i] = 30
        if i in threshold.keys():
            data.loc[data[i] > threshold[i], i] = threshold[i]

    # extra rule2  # 此rule用来计算温度T，湿度H，气压P
    PRESSURE = [1001] * M  # 气压
    if 6 < MONTH <= 10:  # 如果在6～10月间，默认为夏季
        TEMPERATURE = tem_summer
        HUMIDITY = hum_summer
    elif MONTH < 3 or MONTH > 11:  # 如果在11～3月间，默认为冬季
        TEMPERATURE = tem_winter
        HUMIDITY = hum_winter
    else:  # 否则为春季或秋季，用夏季与冬季平均值替代
        TEMPERATURE = [(i + j) / 2 for i, j in zip(tem_summer, tem_winter)]
        HUMIDITY = [(i + j) / 2 for i, j in zip(hum_summer, hum_winter)]
    if "T" in data.columns:  # 但如果T存在于监测数据中
        TEMPERATURE = data["T"].tolist()
    if "P" in data.columns:  # 如果P存在于监测数据中
        PRESSURE = (data["P"] * 10).tolist()
    if "H" in data.columns:  # 如果H存在于监测数据中
        HUMIDITY = data["H"].tolist()

    # CB05 model
    columns_set = set(data.columns)  # 所有的列名  # voc
    voc_name = columns_set - {"T", "P", "H", "O3", "SO2", "CO", "NO", "NO2", "PAR", "OLE", "TOL", "XYL", "FORM", "ALD2",
                              "ETH", "ISOP", "MEOH", "ETOH", "NR", "ETHA", "IOLE", "ALDX", "TERP", "MGLY", "ISPD",
                              "AACD"}
    # preparation for model
    HOUR, MIN, SEC, UTC = data.index.to_list(), 0, 0, 8  # 设置输入到模型的时间参数，小时，分钟，秒，时区
    time = {"year": YEAR, "month": MONTH, "day": DAY, "hour": HOUR, "min": MIN, "sec": SEC, "UTC": UTC}  # 时间字典
    location = {"latitude": LATITUDE, "longitude": LONGITUDE, "altitude": ALTITUDE}  # 位置字典
    sun = sun_position(time, location)  # 太阳天顶角
    Met = {"P": PRESSURE, "T": [i + 273.15 for i in TEMPERATURE], "RH": HUMIDITY, "SZA": sun["zenith"],
           "kdil": 1 / 86400,  # 气象参数
           "jcorr": 1, "ALT": location["altitude"], "O3col": 300, "albedo": 0.5}
    J = {i for i in columns_set if i[0] == "J"}  # 是否有光解速率在监测数据中
    Met.update({i: data[i].tolist() for i in J})  # 如果有将光解速率添加到Met中
    ChemFiles = ("CB05_K(Met)", "CB05_J(Met,2)", "CB05_AllRxns")  # ("MCMv331_K(Met)","MCMv331_J(Met,0)","mcm_subset2")#
    BkgdConc = {"DEFAULT": 1}  # 背景浓度参数  # 模型运行方式
    ModelOptions = {"Verbose": 0, "EndPointsOnly": 0, "LinkSteps": 1, "Repeat": 1, "IntTime": 3600,
                    "SavePath": "DoNotSave",
                    "FixNOx": 0, "TimeStamp": HOUR}
    ioa, O3_Max = data_run(Met, deepcopy(data), ChemFiles, BkgdConc, ModelOptions, I_ARRAY, J_ARRAY,
                           0)  # type -> np.ndarray
    O3_Max = array(O3_Max).reshape((len(I_ARRAY), len(J_ARRAY))).round(3)  # 计算得到的O3_Max，日最大臭氧浓度，reshape为特定形状

    data.to_csv(save_path + sep + "data_processed.csv", index=False)  # 保存利用转换表与模型物种计算，插值与平均后的data数据
    savetxt(save_path + sep + f"O3_Max_{ioa}.csv", O3_Max, fmt="%.3f", delimiter=",")  # 保存O3_Max
    nox_mean.append(data[["NO", "NO2"]].sum(axis=1).mean())  # 将输入模型的数据计算的NOx添加到nox_mean
    voc_mean.append(data[list(voc_name)].sum(axis=1).mean())  # 将输入模型的数据计算的VOCs添加到voc_mean
    plot_EKMA([voc_mean, nox_mean], O3_Max, I_ARRAY, J_ARRAY, save_path, plot_ridges=True)  # 绘制EKMA，保存


def check_file(file):  # 检查文件是否存在的函数，如果不存在写入log，退出程序
    if not exists(file):
        log_write(log_file, f"{file} not exists! exit!\n")
        exit()


def log_write(log_file, msg):  # 写入log的函数
    with open(log_file, "ab", buffering=0) as f:  # "ab"表示以二进制追加写入，buffering=0表示不缓冲
        f.write((datetime.now().strftime("%Y-%m-%d %H:%M:%S ") + msg).encode("utf-8"))
        f.close()


if __name__ == "__main__":
    start_time = datetime.now()  # 开始时间
    check_file(main_path)  # 检查主路径
    check_file(data_file)  # 检查数据文件
    data_file = file_transform(data_file)  # 转换数据文件为csv，在此过程中会剔出Flag标，将中文表头转换为cas号
    check_file(compound_name_file)  # 检查转换表
    log_write(log_file, "EKMA starting\n")  # 写入log开始时间
    main()  # 运行EKMA模块
    log_write(log_file, "EKMA ending\n")  # 写入log结束时间
    end_time = datetime.now()
    cost_seconds = (end_time - start_time).seconds
    log_write(log_file, f"Total cost time: {cost_seconds}s.\n")  # 写入log总花费时间
    victory(dirname(__file__) + sep + "tool" + sep + "ffVII_victory.wav")  # 庆祝🎉
