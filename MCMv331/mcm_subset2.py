from numpy import zeros, power, exp
from re import findall
from os import sep
from os.path import dirname
from scipy.sparse import dok_matrix


def calculate_k(K, J, Met, n: int):
    file = dirname(__file__) + sep + "k_2.txt"
    for i in K.keys():
        exec(f"{i} = K['{i}']")
    for i in J.keys():
        exec(f"{i} = J['{i}']")
    for i in Met.keys():
        exec(f"{i} = Met['{i}'].reshape(1, -1)[0]")
    m = len(Met["T"])
    with open(file, "r", encoding="utf-8") as f:
        try:
            k = zeros((m, n))
            for i, l in enumerate(f):
                k[:, i] = eval(l.strip())
        except:
            raise SyntaxError(f"mcm_subset2: in {file}, {l} is not correct Python syntax! line{i}")
    return k


def calculate_f(Cnames: list, m: int):
    file, file2 = dirname(__file__) + sep + "f_2.txt", dirname(__file__) + sep + "R_2_.txt"
    Rnames_list = []
    with open(file2, encoding="utf-8") as f:
        for l in f:
            Rnames_list.append(l.strip().split(" "))
    Cnames_dict = {i: Cnames.index(i) for i in Cnames}
    f = dok_matrix((m, len(Cnames)))  # shape -> (nRx,nSp)
    i = 0
    with open(file, "r", encoding="utf-8") as f_:
        try:
            for l in f_:
                tem = l.strip().split(" ")
                for index, j in enumerate(tem):
                    if "+" in j or "-" in j:
                        f[i, Cnames_dict[Rnames_list[i][index]]] += float(j)
                    else:
                        f[i, Cnames_dict[Rnames_list[i][index]]] = float(j)
                i += 1
        except:
            print(i)

    return f.tolil()


def get_Rnames():
    file = dirname(__file__) + sep + "R_2.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            Rnames = [l.strip() for l in f]
    except:
        raise FileExistsError(f"{file} is not exists!")
    return Rnames


def get_Gnames():
    file = dirname(__file__) + sep + "G_2.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            Gnames = [change7(l) for l in f]
    except:
        raise FileExistsError(f"{file} is not exists!")
    return Gnames


def get_RO2ToAdd():
    file = dirname(__file__) + sep + "RO2ToAdd_2.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            temp = [change6(l) for l in f]
        re = []
        for i in temp:
            re += i
    except:
        raise FileExistsError(f"{file} not exists!")

    return re


def change6(string):
    tem = findall(r"'([\dA-Z]+)'", string)
    return tem


def change7(string):
    tem = string.strip().split(" ")
    if len(tem) < 2:
        tem.append("ONE")
    return tem


def get_SpeciesToAdd():
    file = dirname(__file__) + sep + "SpeciesToAdd_2.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            temp = [change6(l) for l in f]
        re = []
        for i in temp:
            re += i
    except:
        raise FileExistsError(f"{file} not exists!")

    return re
