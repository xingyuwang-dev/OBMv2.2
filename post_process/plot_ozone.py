import matplotlib.pyplot as plt
from pandas import read_csv
from os import sep
from os.path import dirname
from sys import platform
import pylab  # 不要删除这个，可能会出错

plt.rcParams["axes.unicode_minus"] = False

if platform == "darwin":
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else:
    plt.rcParams["font.family"] = "Times New Roman"

plt.rcParams["mathtext.fontset"] = "stix"


# 此脚本用在现在与OBM软件，完成RIR模型之后用来绘制O3生成速率的脚本。data为O3生成速率的表，path为保存路径，pic为图片名称


def plot_ozone(data, path=dirname(__file__), pic="ozone_generation.png"):
    data = read_csv(data)  # 读取O3生成速率为DataFrame
    font_size = 20  # 全局字体大小

    pic_file = path + sep + pic  # 图片保存绝对路径
    plt.figure(figsize=(10, 6))  # 图片size，下面为图例名称
    labels = ['HO$_{2}$+NO', 'RO$_{2}$+NO', u'O$_{3}$ Photolysis', 'O$_{3}$+OH', 'O$_{3}$+HO$_{2}$', 'NO$_{2}$+OH',
              u'O$_{3}$+olefin']
    colors = [(0.461, 0.062, 1.), (0.257, 0.373, 0.982), (0.053, 0.646, 0.939),  # 堆叠图的颜色
              (0.237, 0.916, 0.837), (0.520, 1., 0.696), (0.763, 0.916, 0.547), (1., 0.315, 0.159)]
    xticks_ = ['0:00', '3:00', '6:00', '9:00', '12:00', '15:00', '18:00', '21:00', '24:00']  # x的刻度名称
    plt.xticks(range(0, 25, 3), xticks_,
               fontsize=font_size - 5)
    y_min = min(data.iloc[:, 5:].sum(axis=1))
    y_max = max(data.iloc[:, 3] + data.iloc[:, 4])
    y_max = int(y_max / 10) * 10 + 10
    y_min = int(y_min / 10) * 10 - 10
    plt.yticks(range(y_min, y_max + 1, 5), fontsize=font_size - 5)
    plt.stackplot(data.iloc[:, 0], data.iloc[:, 3], data.iloc[:, 4], labels=labels[:2], colors=colors[:2])  # 堆叠图上部分
    plt.stackplot(data.iloc[:, 0], data.iloc[:, 5], data.iloc[:, 6],  # 堆叠图下部分
                  data.iloc[:, 7], data.iloc[:, 8], data.iloc[:, 9],
                  labels=labels[2:], colors=colors[2:])
    plt.plot(data.iloc[:, 0], data.iloc[:, 1] + data.iloc[:, 2], linewidth=3, color='red',
             label="Net O$_{3}$ production rate")
    plt.ylim((y_min, y_max))
    plt.legend(loc="upper right", fontsize=font_size - 10, frameon=False)
    plt.ylabel('Rate of O$_{3}$ production and depletion (${ppb/h}$)', fontsize=font_size - 8)
    plt.xlabel('Time', fontsize=font_size - 5)
    plt.savefig(pic_file, dpi=600, bbox_inches="tight", facecolor="white", transparent=False)
