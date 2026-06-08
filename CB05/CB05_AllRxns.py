from numpy import zeros, exp  # zeros：生成任意形状与维度的全0数组，exp：针对任意形状与维度计算e次方
from re import findall  # 正则表达式的匹配方式
from os import sep  # 代表windows的路径符号 \ 与 Linux与Mac的 /
from os.path import dirname  # 寻找该脚本运行路径
from scipy.sparse import dok_matrix  # dok_matrix型稀疏数组，与一般numpy数组有所不同


# 该脚本主要用于计算机理中的反应速率常数k，稀疏矩阵f，获得反应名称Rnames，获得反应物名称Gnames
# 该脚本会读取所在路径下的f.txt,G.txt,k.txt,R.txt,R_.txt,SpeciesToADD.txt文本文件
# 这些文本文件是利用Tool文件夹的m2txt.py逐个生成得到的，来源于CB05_ALLRxns.m化学机理(CB05)文件。因为
# python不能读取与运行m文件，所以将其转化拆分为许多txt文件后再运行。当化学机理改变时，应该运行Tool下m2txt.py
# 生成新的txt文件。MCMv331文件夹下包含了MCM机理，细分为两套mcm_subset2.m(添加了CL有关反应)与mcm_subset_gud.m。
# 因为两套机理的处理方式类似，因此不会再次解释MCMv331下mcm_subset2.py与mcm_subset_gud.py

def calculate_k(K: dict, J: dict, Met: dict, n):
    file = dirname(__file__) + sep + "k.txt"  # 读取脚本所处路径下的k.txt，里面保存了每个反应的反应速率计算方法
    m = len(Met["T"])
    for i in K.keys():  # 获取K值，exec可以运行str类型的python语句
        exec(f"{i} = K['{i}']")
    for i in J.keys():  # 获取J值
        exec(f"{i} = J['{i}']")
    for i in Met.keys():  # 获取Met中包含的变量
        exec(f"{i} = Met['{i}'].reshape(1, -1)[0]")
    with open(file, "r", encoding="utf-8") as f:  # eval计算反应速率常数，可以计算str类型的python表达式
        try:
            k = zeros((m, n))
            for i, l in enumerate(f):
                k[:, i] = eval(l.strip())
        except:  # 如果上面发生错误，则报下面的错误
            raise SyntaxError(f"CB05_AllRxnx: in {file}, {l} is not correct Python syntax!")
    return k


def calculate_f(Cnames: list, m: int):  # 计算稀疏矩阵
    file, file2 = dirname(__file__) + sep + "f.txt", dirname(__file__) + sep + "R_.txt"  # 读取f.txt与R_.txt
    Rnames_list = []
    with open(file2, encoding="utf-8") as f:
        for l in f:
            Rnames_list.append(l.strip().split(" "))
    Cnames_dict = {i: Cnames.index(i) for i in Cnames}
    f = dok_matrix((m, len(Cnames)))#shape -> (nRx,nSp)
    i = 0
    with open(file, "r", encoding="utf-8") as f_:
        for l in f_:
            tem = l.strip().split(" ")
            for index, j in enumerate(tem):
                if "+" in j or "-" in j:
                    f[i, Cnames_dict[Rnames_list[i][index]]] += float(j)
                else:
                    f[i, Cnames_dict[Rnames_list[i][index]]] = float(j)
            i += 1

    return f.tolil()


def get_Rnames():  # 获得每个反应的反应方程式，没啥用
    file = dirname(__file__) + sep + "R.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            Rnames = [l.strip() for l in f]
    except:
        raise FileNotFoundError(f"{file} not found!")
    return Rnames


def get_Gnames(): # 获取每个反应的反应物
    file = dirname(__file__) + sep + "G.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            Gnames = [change7(l) for l in f]
    except:
        raise FileNotFoundError(f"{file} not found!")
    return Gnames


def get_RO2ToAdd():
    return []


def change6(string: str):  # 正则表达式，用于提取物质的名称
    tem = findall(r"'([\dA-Z]+)'", string)
    return tem


def change7(string: str):  # 如果某个反应反应物只有1个，则添加一个ONE作为反应物，无实际意义，用于占位和方便计算
    tem = string.strip().split(" ")
    if len(tem) < 2:
        tem.append("ONE")
    return tem


def get_SpeciesToAdd():  # 返回化学机理中涉及到的所有物质
    #SpeciesToAdd = ["NO", "NO2", "NO3", "N2O5", "HNO3", "HONO", "PNA", "O3P", "O1D", "O3", "OH", "HO2", "H2", "CO",
    #                "CH4", "MEO2", "FORM", "NTR", "ALD2", "ALDX", "PAR", "ROOH", "XO2", "MEPX", "MEOH", "C2O3", "CXO3",
    #                "PAN", "PANX", "PACD", "AACD", "FACD", "XO2N", "ROR", "ETH", "OLE", "IOLE", "ISOP", "ISPD", "MGLY",
    #                "TOL", "CRES", "TO2", "OPEN", "CRO", "XYL", "TERP", "ETOH", "ETHA", "H2O2", "HCO3", "SO2", "SULF"]
    file = dirname(__file__) + sep + "SpeciesToAdd.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            temp = [change6(l) for l in f]
        re = []
        for i in temp:
            re += i
    except:
        raise FileNotFoundError(f"{file} not found!")

    return re