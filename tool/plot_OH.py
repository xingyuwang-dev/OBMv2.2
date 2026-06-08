import matplotlib.pyplot as plt
from pandas import read_csv
from os import sep
from os.path import dirname
from sys import platform
import pylab  # 不要删除这个，可能会出错
plt.rcParams["axes.unicode_minus"] = False


if platform == "darwin":  # 判断是否处理mac电脑，因为mac电脑可能没有相应的字体
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
else:
    plt.rcParams["font.family"] = "Times New Roman"

plt.rcParams["mathtext.fontset"] = "stix"  # 全局数字的字体


# data为OH反应活性数据，path为保存路径，pic为图片名称


def plot_OH(data, path=dirname(__file__), pic="OH_reactivity.png"):
    data = read_csv(data, index_col=0)  # 读取数据为DataFrame
    font_size = 15  # 全局字体大小

    pic_file = path + sep + pic  # 图片保存绝对路径
    plt.figure(figsize=(12, 6))

    colors = [(0.461, 0.062, 1), (0.81, 0.884, 0.516), (0.178, 0.484, 0.968),  # 采用颜色rbg值
              (0.520, 1, 0.696), (0.025, 0.735, 0.916), (0.486, 0.733, .0),
              (1., 1., 0.780), (0.969, 0.882, 0.929), (0.769, 0.592, 0.698),
              (1, 0.692, 0.373), (1, 0.843, 0.), (1, 0.373, 0.19),
              (0.855, 0.439, 0.839)]
    labels = ['SO$_{2}$', 'Alkenes', 'NO', 'HO$_{2}$', 'CH$_{4}$', 'Aromatics',  # 图例名称
              'NO$_{2}$', 'HO$_{2}$NO$_{2}$', 'CO', 'Alkanes', 'HNO$_{3}$', 'HONO', 'OVOCs']
    SO2 = data['SO2']
    Alkenes = data['Alkenes']
    NO = data['NO']
    HO2 = data['HO2']
    CH4 = data['CH4']
    Aromatics = data['Aromatics']
    NO2 = data['NO2']
    HO2NO2 = data['HO2NO2']
    CO = data['CO']
    Alkanes = data['Alkanes']
    HNO3 = data['HNO3']
    HONO = data['HONO']
    OVOCs = data['OVOCs']
    plt.stackplot(range(0, 24), SO2, Alkenes, NO, HO2, CH4, Aromatics,  # 绘制面积堆叠图
                  NO2, HO2NO2, CO, Alkanes, HNO3, HONO, OVOCs, labels=labels, colors=colors)
    xticks = ['0:00', '3:00', '6:00', '9:00', '12:00', '15:00', '18:00', '21:00', '24:00']  # x刻度
    plt.xticks(range(0, 25, 3), xticks, fontsize=font_size)
    y_max = data.sum(axis=1).max()
    y_max = int(y_max / 5) * 5 + 11  # 设置刻度y的最大值
    plt.yticks(ticks=range(-10, int(y_max) + 1, 5), fontsize=font_size)
    plt.ylim((0, y_max))
    plt.legend(loc="upper right", fontsize=font_size-5, ncol=3, frameon=False)  # 设置图例
    plt.ylabel(u'OH reactivity (${s^{-1}}$)', fontsize=font_size-3)  # y轴名称
    plt.xlabel('Time', fontsize=font_size)  # x轴名称
    plt.savefig(pic_file, dpi=600, bbox_inches="tight", facecolor="white", transparent=False)
