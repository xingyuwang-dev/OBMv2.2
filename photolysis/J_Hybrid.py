from scipy.io import loadmat  # 加载.mat文件使用
from os import sep  # 代表windows的路径符号 \ 与 Linux与Mac的 /
from os.path import dirname
from scipy.interpolate import RegularGridInterpolator  # 常规栅格插值器，可以处理不同维度
from numpy import arange, load, hstack  # arang：生成一个数组，load：加载.npz文件，hstack：水平拼接数组


# function J=J_Hybrid(SZA,ALT,O3col,albedo)
# Interpolation hybrid J-values to desired SZA, altitude, O3column and albedo.
# The J-values found in Jhybrid.mat were derived using a combination of TUV solar spectra
# and custom-compiled quantum yields (QY) ad cross sections (CS).
#
# Clear-sky TUVv5.2 solar spectra were calculated with the following inputs:
# SZA 0:5:90 degrees
# Altitudes 0:1:15 km
# O3 column 100:50:600 DU
# ground Alt 0 km
# AOD 0.235
# For more detailed info on TUV setup, see TUV ActinicFlux.m and TUV_WriteInputFile_ActinicFlux.m.
#
# QY and CS information was taken from IUPAC and/or JPL recommendations as documented in
# PhotoDataSources.xlsx. For more info the calculation, see J_BottomUp.m


# 该脚本会被CB05模块与MCMv331模块下的计算光解速率的部分调用，J_Hybrid与J_Hybrid_new函数接受4个参数，返回一个字典
# 其中就是每个光解速率的名称与数值。需要指出的是，该脚本以及该模型的很多脚本的函数都是根据参数的长度返回相应长度的结果。如果
# 参数是一个1小时长度，也就是一个值，结果也只会返回一个小时的；如果是24小时长度，也就是24个值，结果会返回24个小时的；这是
# 根据numpy，scipy，pandas等数值计算库的特点来决定的，因此对于输入参数的长度不需要太过在意。J_Hybrid与J_Hybrid_new函数
# 的区别在于前者读取的是Photolysis下的HybridJvalues.mat数据，后者读取转换之后的HybridJvalues.npz。现在CB05使用的
# 是后者。.mat文件与.npz文件中的数据是一样的，构造方式为一个五维数组。一个物种维度加四个参数维度，这四个维度对应了
# SZA(太阳天顶角度)，ALB(地表反射率)，O3C(臭氧总量)，ALT(海报高度)四个参数。J_Hybrid_new函数的作用相当于
# 在一个给定四维空间中，空间中有很多固定间距的点，每个点都有一个值，然后你输入一个任意位置的点，
# 利用插值算法得到输入点的值。


def J_Hybrid(SZA, ALT, O3col, albedo):
    # try:
    #    SZA = array(SZA)
    #    ALT = array(ALT)
    #    O3col = array(O3col)
    #    albedo = array(albedo)
    # except:
    #    raise ValueError("J_Hybrid: Invalid Met, cannot transform to ndarray")

    J_name = ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J11", "J12",
              "J13", "J14", "J15", "J16", "J17", "J18", "J19", "J20", "J21", "J22",
              "J23", "J24", "J31", "J32", "J33", "J34", "J35", "J41", "J51", "J52",
              "J53", "J54", "J55", "J56", "J57", "Jn1", "Jn2", "Jn3", "Jn4", "Jn5",
              "Jn6", "Jn8", "Jn9", "Jn10", "Jn11", "Jn12", "Jn13", "Jn14", "Jn15", "Jn16",
              "Jn17", "Jn18", "Jn19", "Jn20", "Jn21", "Jn22", "Jn23", "Jn24", "Jn25", "Jn26",
              "Jn27", "Jn28", "Jn29", "Jn30", "Jn31", "Jn32", "Jn33", "Jn34", "Jn35", "Jn36"]
    SZA[SZA > 90] = 90  # SZA.shape -> (x,1)
    data_file = dirname(__file__) + sep + "HybridJvalues.mat"
    data = loadmat(data_file)
    J = {}
    # SZA_, ALB_, O3C_, ALT_, data["SZAhybrid"], data["ALBhybrid"], data["O3Chybrid"], data["ALThybrid"],
    J_ = data["Jhybrid"]
    SZA_, ALB_, O3C_, ALT_ = arange(0, 95, 5), arange(0, 1.2, 0.2), arange(100, 650, 50), arange(0, 16000, 1000)
    # The shape of SZA_, ALB_, O3C_, ALT_ -> (19,6,11,16), the shape of element in J_ -> (19,6,11,16)
    pts = hstack((SZA, albedo, O3col, ALT))
    for index, j in enumerate(J_name):
        J_target = J_[0, 0][index]
        interp = RegularGridInterpolator((SZA_, ALB_, O3C_, ALT_), J_target)
        J.update({j: interp(pts)})

    return J


def J_Hybrid_new(SZA, ALT, O3col, albedo):
    # try:
    #    SZA = array(SZA)
    #    ALT = array(ALT)
    #    O3col = array(O3col)
    #    albedo = array(albedo)
    # except:
    #    raise ValueError("J_Hybrid: Invalid Met, cannot transform to ndarray")

    SZA[SZA > 90] = 90  # SZA.shape -> (x,1)  # 浮点计算可能些微超过90度，将大于90度规整为90度
    data_file = dirname(__file__) + sep + "HybridJvalues.npz"  # 读取五维空间中的数据点
    data = load(data_file)  # 加载数据点的值
    # 下面一句代表每个四维空间中数据点的坐标
    SZA_, ALB_, O3C_, ALT_ = arange(0, 95, 5), arange(0, 1.2, 0.2), arange(100, 650, 50), arange(0, 16000, 1000)
    J_name = ["J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8", "J11", "J12",  # 物种维度的名称
              "J13", "J14", "J15", "J16", "J17", "J18", "J19", "J20", "J21", "J22",
              "J23", "J24", "J31", "J32", "J33", "J34", "J35", "J41", "J51", "J52",
              "J53", "J54", "J55", "J56", "J57", "Jn1", "Jn2", "Jn3", "Jn4", "Jn5",
              "Jn6", "Jn8", "Jn9", "Jn10", "Jn11", "Jn12", "Jn13", "Jn14", "Jn15", "Jn16",
              "Jn17", "Jn18", "Jn19", "Jn20", "Jn21", "Jn22", "Jn23", "Jn24", "Jn25", "Jn26",
              "Jn27", "Jn28", "Jn29", "Jn30", "Jn31", "Jn32", "Jn33", "Jn34", "Jn35", "Jn36"]
    J = {}
    pts = hstack((SZA, albedo, O3col, ALT))  # 代表输入点的坐标，输入点可能只有一个，可能有多个
    for index, j in enumerate(J_name):  # 根据每个光解物种的名称讯号
        interp = RegularGridInterpolator((SZA_, ALB_, O3C_, ALT_), data[j])  # 利用四维空间的坐标和值初始化插值器
        J.update({j: interp(pts)})  # 利用插值器与输入点坐标pts计算得到输入点的值，不断的添加到J字典

    return J
