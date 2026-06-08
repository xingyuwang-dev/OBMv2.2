#from F0AM_ModelCore import F0AM_ModelCore
from core.F0AM_ModelCore2 import F0AM_ModelCore_read, F0AM_ModelCore_calculate
from copy import deepcopy
from multiprocessing import Pool, cpu_count, freeze_support
from tool.IOA import calculate_IOA


# 该模块被EKMA模块调用，是介于EKMA模块与F0AM_ModelCore模型的中间层，用于调用后者；其工作方式为接受必要的参数，如气象，监测物质浓度，
# 需要调用的机理，背景浓度控制，VOCs情景，NOx情景，迭代控制参数。
# 这些参数位于data_run函数的前面几个，然后multi_process参数控制是否采用多进程进行计算，在这里的话就是利用多个CPU同时计算不同的情景；
# 可以通过CPU参数控制调用的CPU个数，默认为电脑或服务器的CPU数，CPU数量需要小于等于情景数。
# data_run具体运行方式：先调用F0AM_ModelCore模块预热数据，将模拟得到的结果中，不包含在原始监测数据中的数据添加到原始数据中。之后通过
# get_InitConc函数计算不同的情景的NOx与VOCs浓度，将情景添加到进程池；计算之后将结果保存为O3_Max中，调用get_one函数计算距离原始情景最近
# 的情景，用此情景的模拟臭氧浓度与原始的臭氧浓度计算IOA指数


J_name = {f"J{i}" for i in range(30)}  # 可能输入模型的光解速率名称


def columns(columns, iHold):  # 该函数用于添加控制符iHold，在F0AM_ModelCore模型中为Holdme参数
    return [0 if i in {"O3", "NO", "NO2", "CO"} else iHold for i in columns]


def data_run(Met, data, ChemFiles ,BkgdConc, ModelOptions, I_ARRAY, J_ARRAY, iHold=0, multi_process=True, CPU=cpu_count()):
    freeze_support()  # 不要删，有一些奇妙的作用
    kdil = Met["kdil"]
    if multi_process:
        CPU = CPU if CPU < len(I_ARRAY)*len(J_ARRAY) else len(I_ARRAY)*len(J_ARRAY)
        pool = Pool(CPU)

    data_init = deepcopy(data)  # 深度复制，pandas方法为df.copy(deep=True)，为什么不用pandas的？当时没想到
    data_columns = data.columns
    data.columns = [data_columns, columns(data_columns, iHold)]
    data_init.columns = [data_columns, columns(data_init, 1)]  # 将data的表头变为两行，即一行列名，一行iHold

    args = F0AM_ModelCore_read(Met, ChemFiles)  # 预热
    args2 = (data_init, BkgdConc, ModelOptions, kdil, *args)
    result = F0AM_ModelCore_calculate(args2)["Conc"]
    other_vocs = set(result.keys()) - set(data_columns) - {"HNO3"}  # 不包含在原始数据中的物质，为什么减去 "HNO3"，不要问！
    for i in other_vocs:  # 替换
        data[(i, iHold)] = result[i]

    O3_Max, re = [], []
    O3_i_j, count = [], 0
    location = get_one(I_ARRAY, J_ARRAY)  # 最接近原始情景的位置，此位置表示在I_ARRAY和J_ARRAY构成数组中的位置
    for i in I_ARRAY:
        for j in J_ARRAY:
            InitConc = get_InitConc(deepcopy(data), i, j)  # 同上
            args2 = (InitConc, BkgdConc, ModelOptions, kdil, *args)  # 多进程需要的参数，Pool里面的函数只接受元组作为参数
            if multi_process:
                re.append(pool.apply_async(F0AM_ModelCore_calculate, args=(args2,)))  # 异步处理多进程，将进程添加到进程池
            else:
                result = F0AM_ModelCore_calculate(args2)  # 非多线程运行模式，直接传递参数
                O3_Max.append(max(result["Conc"]["O3"]))
                if count == location:
                    O3_i_j = result["Conc"]["O3"]
            count += 1
            """
            InitConc = get_InitConc(deepcopy(data), i, j)
            arg = (deepcopy(Met), InitConc, deepcopy(ChemFiles), deepcopy(BkgdConc), deepcopy(ModelOptions), True)
            if multi_process:
                re.append(pool.apply_async(func=F0AM_ModelCore, args=(arg, )))
            else:
                result = F0AM_ModelCore(arg)
                O3_Max.append(max(result["Conc"]["O3"]))
                if count == location:
                    O3_i_j = result["Conc"]["O3"]
            count += 1
            """

    if multi_process:
        pool.close()  # 进程池的close不是关闭的意思，是不再接受任何新进程
        pool.join()  # join不是加入，是等待所有作业完成后退出，有效的清理进程池
        for result in re:
            O3_Max.append(max(result.get()["Conc"]["O3"]))  # 多进程
        O3_i_j = re[location].get()["Conc"]["O3"]

    ioa = calculate_IOA(O3_i_j, data["O3"].values)

    return ioa, O3_Max


def get_InitConc(data, i, j):
    COLUMNS = list({i[0] for i in data.columns} - J_name - {"NO", "NO2", "SO2", "P", "T", "H"})
    data[["NO", "NO2"]] = data[["NO", "NO2"]] * i
    data[COLUMNS] = data[COLUMNS] * j

    return data


def get_one(i_array, j_array):
    for index, i in enumerate(i_array):
        if i<=1 and 1<i_array[index+1]:
            I = index
    for index, j in enumerate(j_array):
        if j<=1 and 1<j_array[index+1]:
            J = index

    return I * len(j_array) + J + 1