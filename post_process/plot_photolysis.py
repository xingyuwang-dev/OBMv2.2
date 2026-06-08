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


# 此图为RIR模拟结束后绘制光解速率的脚本，不需要过度关注


def plot_photolysis(data, path=dirname(__file__), pic="photolysis_rate.png"):
    data = read_csv(data)
    font_size = 15

    pic_file = path + sep + pic
    title = data.columns[1:]
    colors = [(0.461, 0.062, 1), (0.296, 0.315, 0.987), (0.178, 0.484, 0.968),
              (0.025, 0.735, 0.916), (0.151, 0.853, 0.872), (0.276, 0.939, 0.820),
              (0.394, 0.986, 0.763), (0.520, 1, 0.696)]

    plt.figure(figsize=(12, 6))
    plt.axis("tight")
    plt.subplots_adjust(hspace=0.25, wspace=0.2)
    plt.suptitle('Photolysis Rate (${s^{-1}}$)', fontsize=font_size)
    plt.subplot(2, 4, 1)
    plt.plot(range(0, 24), data.iloc[:, 1], color=colors[0], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"], fontsize=font_size - 4)
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[0], fontsize=font_size - 5)

    plt.subplot(2, 4, 2)
    plt.plot(range(0, 24), data.iloc[:, 2], color=colors[1], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[1], fontsize=font_size - 5)

    plt.subplot(2, 4, 3)
    plt.plot(range(0, 24), data.iloc[:, 3], color=colors[2], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[2], fontsize=font_size - 5)

    plt.subplot(2, 4, 4)
    plt.plot(range(0, 24), data.iloc[:, 4], color=colors[3], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[3], fontsize=font_size - 5)

    plt.subplot(2, 4, 5)
    plt.plot(range(0, 24), data.iloc[:, 5], color=colors[4], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[4], fontsize=font_size - 5)

    plt.subplot(2, 4, 6)
    plt.plot(range(0, 24), data.iloc[:, 6], color=colors[5], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[5], fontsize=font_size - 5)

    plt.subplot(2, 4, 7)
    plt.plot(range(0, 24), data.iloc[:, 7], color=colors[6], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[6], fontsize=font_size - 5)

    plt.subplot(2, 4, 8)
    plt.plot(range(0, 24), data.iloc[:, 8], color=colors[7], linewidth=2)
    plt.xticks([0, 12, 23], ["0:00", "12:00", "23:00"])
    plt.ticklabel_format(style='sci', scilimits=(0, 0), axis='y')
    plt.xlabel(title[7], fontsize=font_size - 5)

    plt.savefig(pic_file, dpi=600, bbox_inches="tight", facecolor="white", transparent=False)
