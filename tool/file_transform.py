from pandas import read_csv, read_excel  # read_csv: 读取csv或txt类型数据，read_excel：读取xls或xlsx类型数据
from os.path import dirname, sep


# 该脚本用于现在的OBM软件，作用是将平台导入的数据进行处理，删除flag列，将物种名称按照name_to_cas.csv表转化为cas号
# 线上版本不调用该脚本。


def file_transform(file:str):
    transform_data = read_csv(dirname(__file__) + sep + "name_to_cas.csv")  # 读取csv为DataFrame格式
    # 将DataFrame转化为字典格式，这里需要提出的是字典使用｜=方法在python3.8开始
    transform_dict = {transform_data.iloc[i, 1]: transform_data.iloc[i, 2] for i in range(transform_data.shape[0])}
    transform_dict |= {transform_data.iloc[i, 0]: transform_data.iloc[i, 2] for i in range(transform_data.shape[0])}

    file_type = file.split(".")[-1]  # 判断输入文件类型
    if file_type == "txt" or file_type == "csv":
        try:
            data = read_csv(file)  # 如果为txt或csv调用read_csv
        except UnicodeDecodeError:
            data = read_csv(file, encoding="gbk")  # 如果报错则可能编码方式错误，则用gbk编码重新打开
    else:
        data = read_excel(file, engine="openpyxl")
    flag = [i for i in data.columns if "flag" in i]
    data.drop(flag, axis=1, inplace=True)  # 删除表头为flag的列
    data.rename(columns={i: transform_dict.get(i, i) for i in data.columns}, inplace=True)  # 替换表头为cas号
    data.to_csv("".join(file.split(".")[:-1]) + "_.csv", index=False)  # 保存替换表头与删除flag列后的文件
    return "".join(file.split(".")[:-1]) + "_.csv"
