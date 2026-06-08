import matplotlib.pyplot as plt
from os import sep
from os.path import dirname
from scipy.interpolate import interp1d, interp2d
from numpy import arange, argmax, gradient, poly1d, polyfit, array, unravel_index
import pylab  # 不要删除这个，可能会出错
plt.rcParams["axes.unicode_minus"] = False
#plot EKMA
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["mathtext.fontset"] = "stix"


# 该脚本为现在运行与OBM软件运行，EKMA模型结束后调用的脚本，作用是EKMA曲线；传入参数data2为EKMA曲线的结果，data1为需要在图上的打点
# I_ARRAY与J_ARRAY为模拟情景，path为保存图片位置，默认为该脚本路径，pic为图片名称，默认为EKMA.png; plot_ridges为是否需要画
# 脊线的参数，single为是否只画一个点的参数，move为上下移动脊线距离的参数


def plot_EKMA(data1, data2, I_ARRAY, J_ARRAY, path=dirname(__file__), pic="EKMA.png", plot_ridges=True, single=False, move=0):
    pic_file = path + sep + pic  # 图片保存的绝对路径
    vocs = data1[0]  # 获取需要打点的x坐标
    nox = data1[1]  # 获取需要打点的y坐标

    x = vocs[-1] * array(J_ARRAY)
    y = nox[-1] * array(I_ARRAY)
    x_new, y_new = arange(0, len(x) - 0.75, 0.25), arange(0, len(y) - 0.75, 0.25)
    x_n, y_n = range(len(x)), range(len(y))
    z = interp2d(x_n, y_n, data2, kind="cubic")(x_new, y_new)  # 将EKMA曲线插值得更细，使得画图更好看
    x = interp1d(x_n, x, kind="cubic")(x_new)  # 插值EKMA的x值
    y = interp1d(y_n, y, kind="cubic")(y_new)  # 插值EKMA的y值
    x_min, x_max = int(x[0]), int(x[-1]/10)*10  # 设置x，y轴的间隔与最大最小值
    y_min, y_max = int(y[0]), int(y[-1]/10)*10
    if x_max < 50:
        x_interval = 5
    elif x_max < 100:
        x_interval = 10
    elif x_max < 200:
        x_interval = 20
    else:
        x_interval = 40
    if y_max < 50:
        y_interval = 5
    elif y_max < 100:
        y_interval = 10
    elif y_max < 200:
        y_interval = 20
    else:
        y_interval = 40

    font_size = 15  # 图片尺寸
    plt.rcParams["font.sans-serif"] = "Times New Roman"  # 全局字体族
    plt.rcParams["font.weight"] = "bold"  # 全局粗体
    ax = plt.subplot()
    fig = ax.contourf(x, y, z, levels=11, cmap="rainbow")  # 画EKMA等高线图，线条数11，色系为彩虹色
    color_bar = plt.colorbar(fig, pad=0.01, spacing="proportional")  # 画colorbar
    color_bar.set_label(label="ρ(O$_{3}$)×10$^{-9}$", fontsize=font_size-5, weight="bold")  # colorbar名称，字体大小，粗体
    if plot_ridges:  # 这个脊线的水有点深
        xx, yy = gradient2(x, y, z, 100, 1)  # 调用gradient2函数计算梯度，得到表示梯度变化的一系列点
        zz = polyfit(xx, yy, deg=1)  # 通过点的坐标拟合一条直线
        yy = poly1d(zz)(xx) + move+7  # 计算直线的y值
        plt.plot(xx, yy, linewidth=2, c="red")  # 通过直线的x，y值画出脊线
    ax.xaxis.set_major_locator(plt.MultipleLocator(x_interval))  # 设置x轴刻度
    ax.yaxis.set_major_locator(plt.MultipleLocator(y_interval))  # 设置y轴刻度
    ax.set_xlabel("ψ(VOCs)×10$^{-9}$", fontsize=font_size-5, weight="bold", labelpad=0.01)  # 设置x轴名称，大小，粗体，距离
    ax.set_ylabel("ψ(NOx)×10$^{-9}$", fontsize=font_size-5, weight="bold", labelpad=0.01)  # ～
    ax.set_title("EKMA", fontsize=font_size, weight="bold")  # 设置图片名称
    if single is False:  # 如果single为False
        ax.scatter(vocs, nox, s=font_size, c="red")  # 在图上添加很多点
    if len(vocs) > 2:
        color = "red" if single else "lime"
        ax.scatter(vocs[-1], nox[-1], s=font_size+5, c=color)  # lime
    ax.set_ylim(y[0], y[-1])  # 设置x轴最大值
    ax.set_xlim(x[0], x[-1])  # 设置y轴最大值
    plt.savefig(pic_file, dpi=600, bbox_inches="tight", facecolor="white", transparent=False)  # 保存图片，分辨率600，紧凑，背景为白色，不透明


def gradient2(x, y, data, times=1000, eta=1e-1):  # GD(梯度下降法)，x：x值，y：y值，data：z值，迭代次数最大1000次，学习率eta
    data_grad_x, data_grad_y = gradient(data)  # 计算data的x与y方向梯度
    y_loc, x_loc = unravel_index(argmax(data), data.shape)  # 计算最大值的索引
    x_, y_ = x[x_loc], y[y_loc]  # 从值最大处开始进行梯度下降
    re_x, re_y = [x_], [y_]  # 保存每次下降之后的点位置
    fit_x = interp2d(x, y, data_grad_x, kind="linear")  # 初始化x方向梯度的插值器
    fit_y = interp2d(x, y, data_grad_y, kind="linear")  # 初始化y方向梯度的插值器
    for i in range(times):  # 迭代
        if x_ < -10 or y_ < -10:  # 如果x或y小于-10，则认为超过了图之外，结束循环
            break
        x_2, y_2 = x_, y_
        x_ = x_2 - eta * (fit_x(x_2, y_2))  # 更新x_，梯度下降法的具体理论请查阅相关资料
        y_ = y_2 - eta * (fit_y(x_2, y_2))  # 更新y_
        re_x.append(float(x_))
        re_y.append(float(y_))

    return re_x, re_y
