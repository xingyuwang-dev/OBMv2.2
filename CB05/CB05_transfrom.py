from pandas import read_csv, DataFrame, concat
from numpy import nan_to_num
from os.path import dirname
from os import sep

# 该脚本会被最外层的脚本调用，用于将监测物种转化为模型物种，读取CB05_transfrom.csv中的矩阵计算模型物种浓度
# CB05_transfrom.csv来源于matlab的FOAM文件加下有关CB05机理的一个pdf


file = dirname(__file__) + sep + "CB05_transfrom.csv"


def transfrom(data):
    data_cas = list(data.columns)  # 读取监测物种cas号
    trans_matrix = read_csv(file)  # 读取csv文件
    columns = trans_matrix.columns  # 读取模型物种名称
    trans_cas = trans_matrix["CAS"].to_list()  # 读取csv中cas号
    data_cas = list(set(data_cas) & set(trans_cas))  # 计算监测物种与模型物种的交集
    loc = [trans_cas.index(i) for i in data_cas]  # 获取交集中每个元素在csv中位置
    trans_matrix = trans_matrix.iloc[loc, 2:].to_numpy()  # 提取csv中的包含交集中物质的转换子矩阵
    data_matrix = nan_to_num(data[data_cas].to_numpy())  # 提取监测物种的物种浓度矩阵

    CB05_model_species = data_matrix @ trans_matrix  # 转换子矩阵*物种浓度矩阵得到模型物种浓度矩阵，
    data_CB05 = DataFrame(CB05_model_species, columns=columns[2:], index=data.index)  # 将模型物种浓度转为为DataFrame类型
    data = concat([data, data_CB05], axis=1, join="inner")  # 将模型物种浓度拼接在监测物种浓度后面

    return data
