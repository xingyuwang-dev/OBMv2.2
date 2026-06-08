from pandas import read_csv, Series, to_datetime
from numpy import arange, savetxt, array
from datetime import datetime,timedelta
from os import makedirs,sep
from os.path import exists,dirname
from sys import exit
from tool.sun_position import sun_position
from data_run import data_run
from copy import deepcopy
from tool.plot import plot_EKMA
from tool.data_average import do_mean, calculate_noxvoc
from tool.victory import victory
from CB05.CB05_transfrom import transfrom
from functools import partial
from tool.file_transform import file_transform


# 此为OBM模型的软件版本的EKMA模块，主要区别为 不是模型的入口，入口位于UI.py，由其调用并传参


DATE=(datetime.now()+timedelta(days=-1)).strftime("%Y/%m/%d")

main_path=dirname(__file__)
#data_file=main_path+sep+"data2.csv"
compound_name_file=main_path+sep+"comparison_table.csv"
#save_path_=main_path+sep+DATE
log_file=main_path+sep+"log.txt"

tem_summer = [26.1, 26, 25.9, 25.4, 25, 25.1, 25.2, 25.9, 27.7, 28.4, 28.7, 28.2,
              28, 26.2, 26.7, 27.3, 27.4, 27.2, 26.6, 26.6, 26.4, 26.5, 26.5, 26.5]
tem_winter = [6.7, 6.4, 6.1, 5.7, 6, 5.9, 5.6, 6.1, 6.5, 7, 7.3, 7.6,
              7.7, 8, 8.3, 8.5, 8.6, 8.2, 8, 7.7, 7.6, 7.6, 7.6, 7.1]
hum_summer = [95.2, 93.1, 93.3, 94.2, 95.6, 96.7, 99.2, 95.1, 81.3, 78.5, 77, 79.5,
              81.3, 95.1, 94.4, 90.6, 90.8, 90.4, 94.2, 96.8, 99.4, 99.8, 98.6, 98]
hum_winter = [74.7, 76.4, 76.8, 77.3, 75.6, 73.6, 75.6, 72.6, 70.1, 69.1, 68.6, 65.2,
              66.2, 64.6, 61.6, 59.7, 59.8, 61.5, 64.2, 65.9, 66.9, 68.6, 69.3, 71.2]
compound_name=read_csv(compound_name_file, header=None)


def main():
    comparison_dict = {compound_name.iloc[i, 0]: compound_name.iloc[i, 1] for i in range(compound_name.shape[0])}
    data=read_csv(data_file,header=0,index_col=0)
    data.index=to_datetime(data.index)
    data.index=map(lambda x: x.strftime("%Y/%m/%d %H/%M"), data.index)
    voc_mean, nox_mean = calculate_noxvoc(data, comparison_dict)
    data=do_mean(data)
    data=transfrom(data)
    data[data<0]=0

    data.dropna(thresh=15, axis=1, inplace=True)
    drop_columns = list(set(data.columns) - set(comparison_dict.keys()))
    data.drop(drop_columns, axis=1, inplace=True)
    data.rename(columns={i: comparison_dict[i] for i in data.columns}, inplace=True)
    data_time=data.index.to_list()
    YEAR=int(data_time[0][:4])
    MONTH=int(data_time[0][5:7])
    DAY=int(data_time[0][8:10])
    HOUR = [int(i[-5:-3]) for i in data_time]
    HOUR_lost = list(set(range(24)) - set(HOUR))
    data.set_index(Series(HOUR), inplace=True)
    for i in HOUR_lost:
        data.loc[i] = float("nan")
    data.sort_index(inplace=True)

    M,N=data.shape
    if data.isna().sum().sum() > M*N*0.4:
        log_write(log_file,"Data is missing more than 40% and procedure interrupted!\n")
        exit()
    data.interpolate(limit_direction="both",inplace=True)

    #extra rule
    threshold={"C5H8":5,"HCHO":50,"CH3CHO":50,"CH3CL":10,"VINCL":10,"CH2CL2":10,"CH2CLCHCL2":10,"CHCL2CHCL2":10}
    for i in data.columns:
        if i not in threshold.keys() and i not in {"NO","NO2","O3","CO","T","P","H","PAR"}:
            data.loc[data[i]>30,i]=30
        if i in threshold.keys():
            data.loc[data[i]>threshold[i],i]=threshold[i]

    #extra rule2
    PRESSURE=[1001]*M
    if 6<MONTH<=10:
        TEMPERATURE=tem_summer
        HUMIDITY=hum_summer
    elif MONTH<3 or MONTH>11:
        TEMPERATURE=tem_winter
        HUMIDITY=hum_winter
    else:
        TEMPERATURE=[(i+j)/2 for i,j in zip(tem_summer,tem_winter)]
        HUMIDITY=[(i+j)/2 for i,j in zip(hum_summer,hum_winter)]
    if "T" in data.columns:
        TEMPERATURE = data["T"].tolist() if temperature == -1 else [temperature]*M
    if "P" in data.columns:
        PRESSURE = (data["P"]*10).tolist() if pressure == -1 else [pressure]*M
    if "H" in data.columns:
        HUMIDITY = data["H"].tolist() if humidity == -1 else [humidity]*M

    #CB05 model
    columns_set = set(data.columns)
    voc_name = columns_set - {"T", "P", "H", "O3", "SO2", "CO", "NO", "NO2", "PAR", "OLE", "TOL", "XYL", "FORM", "ALD2",
                              "ETH", "ISOP", "MEOH", "ETOH", "NR", "ETHA", "IOLE", "ALDX", "TERP", "MGLY", "ISPD", "AACD"}
    #preparation for model
    HOUR, MIN, SEC, UTC = data.index.to_list(), 0 , 0, 8
    time={"year":YEAR,"month":MONTH,"day":DAY,"hour":HOUR,"min":MIN,"sec":SEC,"UTC":UTC}
    location={"latitude":LATITUDE,"longitude":LONGITUDE,"altitude":ALTITUDE}
    sun=sun_position(time,location)
    Met={"P":PRESSURE,"T":[i+273.15 for i in TEMPERATURE],"RH":HUMIDITY,"SZA":sun["zenith"],"kdil":kdil,
         "jcorr":jcorr,"ALT":location["altitude"],"O3col": o3col, "albedo": albedo}
    J = {i for i in columns_set if i[0] == "J"}
    Met.update({i: data[i].tolist() for i in J})
    ChemFiles=("CB05_K(Met)","CB05_J(Met,2)","CB05_AllRxns")#("MCMv331_K(Met)","MCMv331_J(Met,0)","mcm_subset2")#
    BkgdConc={"DEFAULT":bkgdconc}
    ModelOptions={"Verbose":0,"EndPointsOnly":0,"LinkSteps":linksteps,"Repeat":1,"IntTime":3600,"SavePath":"DoNotSave",
                  "FixNOx":fixnox,"TimeStamp":HOUR}
    ioa, O3_Max=data_run(Met,deepcopy(data),ChemFiles,BkgdConc,ModelOptions,I_ARRAY,J_ARRAY,ihold)#type -> np.ndarray
    O3_Max=array(O3_Max).reshape((len(I_ARRAY),len(J_ARRAY))).round(3)

    data.to_csv(save_path+sep+"data_processed.csv",index=False)
    savetxt(save_path+sep+f"O3_Max_{ioa}.csv",O3_Max,fmt="%.3f",delimiter=",")
    nox_mean.append(data[["NO", "NO2"]].sum(axis=1).mean())
    voc_mean.append(data[list(voc_name)].sum(axis=1).mean())
    plot_EKMA([voc_mean, nox_mean], O3_Max, I_ARRAY, J_ARRAY, save_path, plot_ridges=ridge, single=single, move=move)


def check_file(file):
    if not exists(file):
        log_write(log_file,f"{file} not exists! exit!\n")
        exit()


def log_write(log_file,msg):
    with open(log_file,"ab",buffering=0) as f:
        f.write((datetime.now().strftime("%Y-%m-%d %H:%M:%S ")+msg).encode("utf-8"))
        f.close()


def if_do(send_dict, key, value, fun=str):  # 此函数用来检查并设置UI传递的参数，用于一个偏函数
    if send_dict[key] != "":  # 如果不为空
        if key == "I_ARRAY" or key == "J_ARRAY":  # 如果是情景参数，返回一个数组
            par = list(map(float, send_dict[key].split(":")))
            return arange(par[0], par[2], par[1])
        if fun != str:  # 如果不是str类型，返回fun类型
            return fun(send_dict[key])
        else:  # 是str类型
            return send_dict[key]
    else:  # 否者返回value
        return value


# nuitka --standalone --show-memory --show-process --nofollow-imports --follow-import-to=utils,src --output-dir=out
def EKMA_start(send_dict):
    global data_file, LONGITUDE, LATITUDE, ALTITUDE, kdil, jcorr, bkgdconc, o3col, save_path
    global albedo, linksteps, fixnox, I_ARRAY, J_ARRAY, ihold, temperature, pressure, humidity, single, ridge, move
    check_parameter = partial(if_do, send_dict)  # 设置偏函数check_parameter
    data_file = check_parameter("data", "")  # 检查路径
    save_path = check_parameter("save_path", main_path + sep + DATE)  # 检查保存路径
    LONGITUDE = check_parameter("longtitude", 121.43, float)  # 检查 经纬度 海报
    LATITUDE = check_parameter("latitude", 28.68, float)
    ALTITUDE = check_parameter("altitude", 30, float)
    temperature = check_parameter("temperature", -1, float)  # 检查温度，气压，湿度
    pressure = check_parameter("pressure", -1, float)
    humidity = check_parameter("humidity", -1, float)
    kdil = check_parameter("kdil", 1/86400, float)  # 检查稀释速率，光解速率校正系数，背景浓度系数
    jcorr = check_parameter("jcorr", 1, int)
    bkgdconc = check_parameter("bkgdconc", 1, float)
    o3col = check_parameter("o3col", 300, int)  # 检查臭氧总量，反射率，ihold
    albedo = check_parameter("albedo", 0.3, float)
    ihold = check_parameter("ihold", 1, int)
    linksteps = check_parameter("linksteps", 1, int)  # 检查linksteps，fixnox，single
    fixnox = check_parameter("fixnox", 0, int)
    single = send_dict["single"]
    ridge = send_dict["ridge"]
    move = check_parameter("move", 0, float)  # 检查 move，vocs与nox情景
    I_ARRAY = check_parameter("I_ARRAY", arange(0.1, 2.5, 0.3))
    J_ARRAY = check_parameter("J_ARRAY", arange(0.1, 2.5, 0.3))

    if not exists(save_path):
        makedirs(save_path)

    start_time=datetime.now()
    check_file(main_path)
    check_file(data_file)
    data_file = file_transform(data_file)
    check_file(compound_name_file)
    log_write(log_file,"EKMA starting\n")
    main()
    log_write(log_file,"EKMA ending\n")
    end_time=datetime.now()
    cost_seconds=(end_time-start_time).seconds
    log_write(log_file,f"Total cost time: {cost_seconds}s.\n")
    victory(dirname(__file__)+sep+"tool"+sep+"ffVII_victory.wav")
    return "1"  # 返回UI "1"
