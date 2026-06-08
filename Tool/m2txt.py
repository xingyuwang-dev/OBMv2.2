from re import findall
from os import sep
from os.path import dirname


# 该脚本是用来处理matlab的m脚本文件，即化学机理文件的；其主要目标是将单个化学机理文件拆分成不同txt以供python读取；
# 利用change函数提取反应速率常数为k.txt，利用change2函数提取反应方程式为R.txt，利用change4函数提取每个反应的反应物
# 为G.txt，利用change5函数提取反应系数为f.txt，利用change6函数提取反应方程的反应物与生成物R_.txt，利用change3函数提取需要
# 添加的反应物种为SpeciesToAdd.txt


PATH = dirname(__file__) + sep + "/MCMv331"
code_file = PATH + sep + "mcm_subset_gud.m"
k_file = PATH + sep + "k_.txt"
R_file = PATH + sep + "R_2.txt"
G_file = PATH + sep + "G_2.txt"
f_file = PATH + sep + "f.txt"
R_file_ = PATH + sep + "R_.txt"
#RO2ToAdd_file = PATH + sep + "RO2ToAdd.txt"


def change(string):
    tem=string.replace(";","").replace("\n","")  # 删除"；"，删除换行符
    tem=tem.split(" ")[2]
    tem=tem.replace(".*","*")  # 将matlab中的乘法.*替换为python的numpy的乘法*
    tem=tem.replace("./","/")  # 将matlab中的除法.*变为python的除法/
    #tem=tem.replace("exp","np.exp")
    tem = tem.replace(".^", "**")  # 将matlab的乘方.^变为python的乘方**
    tem=f"{tem}\n"  # 添加换行符在结尾
    return tem


def change2(string):
    tem=findall(r"'(.+)'", string)[0]+"\n"  # 匹配一个或多个任意字符
    return tem


def change3(string):
    tem=string.replace("...","")  # 删除...
    tem=tem.replace("; ",",")  # 将；替换为，
    return tem


def change4(string):
    tem=findall(r"'([0-9A-Z]+)'",string)  # 所有的相连的数字和大写字母，用于匹配物种名称
    tem=" ".join(tem)+"\n"
    return tem


def change5(string):
    tem=findall(r"([+-]*\d*[.\d]+?);",string)  # 所有整数，小数字，负数，用于匹配反应方程式的系数
    tem=" ".join(tem)+"\n"
    return tem


def change6(string):
    tem=findall(r"f([A-Z]+[\dA-Z]*)\(i\)=",string)  # 所有的大写字母开头，带有0个或多个大写字母或数字，匹配所有物种名称
    tem=" ".join(tem)+"\n"
    return tem


def main():

    #R_f = open(R_file, "w", encoding="utf-8")
    #k_f = open(k_file, "w", encoding="utf-8")
    #G_f = open(G_file, "w", encoding="utf-8")
    #f_f = open(f_file, "w", encoding="utf-8")
    R_f_ = open(R_file_, "w", encoding="utf-8")
   # STA_f = open(RO2ToAdd_file, 'w', encoding='utf-8')
    with open(code_file,'r',encoding='utf-8',errors='ignore') as f:
        for l in range(22):
            k=f.readline()
           # if 404 < l < 487:
           #     try:
           #         STA_f.write(change3(k))
           #     except:
           #         print(k)

        count=0
        for l in f:
            #if l[0:2]=="Rn":
            #    try:
            #        R_f.write(change2(l))
            #    except:
            #        print(count)
            #if l[0]=="k":
            #    if "^" in l:
            #        print(count)
            #    try:
             #       k_f.write(change(l))
            #    except:
            #        print(count)
            #if l[0]=="G":
            #    try:
            #        G_f.write(change4(l))
            #    except:
            #        print(count)
            #if l[0]=="f":
            #    try:
            #        f_f.write(change5(l))
            #    except:
            #        print(count)
                #count=count+1
            if l[0]=="f":
                try:
                    R_f_.write(change6(l))
                except:
                    print(count)
            count=count+1
    #k_f.close()
    #R_f.close()
    #G_f.close()
    R_f_.close()
    #STA_f.close()

if __name__=="__main__":
    main()