from numpy import zeros, power, exp
from re import findall
from os import getcwd, sep
from scipy.sparse import dok_matrix


def calculate_k(K, J, Met, n: int):
    PATH = getcwd()
    file = PATH + sep + "MCMv331" + sep + "k.txt"
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
            raise SyntaxError(f"mcm_subset_gud: in {file}, {l} is not correct Python syntax!")
    return k


def calculate_f(Cnames: list, m: int):
    PATH = getcwd()
    file, file2 = PATH + sep + "MCMv331" + sep + "f.txt", PATH + sep + "MCMv331" + sep + "R_.txt"
    Rnames_list = []
    with open(file2, encoding="utf-8") as f:
        for l in f:
            Rnames_list.append(l.strip().split(" "))
    Cnames_dict = {i: Cnames.index(i) for i in Cnames}
    f = dok_matrix((m, len(Cnames)))#shape -> (nRx,nSp)
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
    PATH = getcwd()
    file = PATH + sep + "MCMv331" + sep + "R.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            Rnames = [l.strip() for l in f]
    except:
        raise FileExistsError(f"{file} is not exists!")
    return Rnames


def get_Gnames():
    PATH = getcwd()
    file = PATH + sep + "MCMv331" + sep + "G.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            Gnames = [change7(l) for l in f]
    except:
        raise FileExistsError(f"{file} is not exists!")
    return Gnames


def get_RO2ToAdd():
    PATH = getcwd()
    file = PATH + sep + "MCMv331" + sep + "RO2ToAdd.txt"
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
    PATH = getcwd()
    file = PATH + sep + "MCMv331" + sep + "SpeciesToAdd.txt"
    try:
        with open(file, "r", encoding="utf-8") as f:
            temp = [change6(l) for l in f]
        re = []
        for i in temp:
            re += i
    except:
        raise FileExistsError(f"{file} not exists!")

    return re