from core.RIR_data_process import data_processed
from warnings import simplefilter
simplefilter("ignore")


# 此脚本的目的是将输入的多天监测数据拆分为一天一天的，针对每天调用data_process.py脚本进行处理；
# 会被RIR模块调用，但RIR模块的运行模式是实时计算多天的削减情景时会调用，其他情况下不回调用该模块；
# 使用该模块的原因是为了处理数据成合适形式以方便多进程计算多天RIR削减情景

def do_split(data, compound_name, arg1):
    try:
        data = data.reset_index()
    except:
        pass
    data["special"] = data.iloc[:, 0].apply(lambda x: x[8: 10])  # 将每行的日期赋值给special列
    result = []
    data2 = data.groupby(["special"], sort=False)  # 将data拆分成不同的天
    for _, items in data2:  # 每天数据用data_process.py脚本处理
        items.index = items.iloc[:, 0]
        result.append(data_processed(items, compound_name, arg1))# [(data,time,climate),]
    return result