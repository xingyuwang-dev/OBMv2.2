from pandas import to_numeric
from warnings import simplefilter
simplefilter("ignore")


# 该脚本包含了两个函数，do_mean与calculate_nocvoc，前者作用是计算输入监测物种，按天的平均值，即将多天数据平均到一天
# 后者是计算按天的vocs与nox的浓度值


def do_mean(data):
    data = data.apply(to_numeric, errors="coerce")  # 将data中的非数值类型转化为nan
    try:
        data = data.reset_index()  # 重设索引
    except:
        pass
    data["special"] = data.iloc[:, 0].apply(lambda x: x[11: 13])  # 生成新的special列，每列包含了表示日期的中的小时
    temp = data.drop("index", axis=1)  # 删除index列
    data2 = temp.groupby("special").mean()  # 按照小时进行分组，之后不同组对应位置平均
    loc = int(data.iloc[:, 1:].shape[0]/2)  # 获取data中对于中间位置的时间
    data2.index = data.iloc[loc, 0][:10] + " " + data2.index + ":00"  # 将改时间赋予给data2

    return data2


def calculate_noxvoc(data, comparison_dict):
    vocnox = set(comparison_dict.keys())  # 获取对照表的cas值转化为set
    data = data.apply(to_numeric, errors="coerce")
    try:
        data = data.reset_index()
    except:
        pass
    data["special"] = data.iloc[:, 0].apply(lambda x: x[:10])
    temp = data.drop("index", axis=1)
    data2 = temp.groupby("special").mean()
    voc_name = list(vocnox & set(data.columns) - {"a01001", "a01006", "a01002", "10028-15-6", "7446-09-5", "630-08-0",
                                                  "10102-43-9", "10102-44-0"})
    nox_name = ["10102-44-0", "10102-43-9"]

    voc_mean = data2[voc_name].sum(axis=1).round(3).to_list()
    nox_mean = data2[nox_name].sum(axis=1).round(3).to_list()

    return voc_mean, nox_mean
