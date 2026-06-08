from jitcode import jitcode, y
from symengine import Symbol
from os.path import exists, dirname
from os import sep
from numpy import array, concatenate
from sys import platform


# 此脚本为整个模型的核心中的核心，最重要的求解器！！！不建议在没有完全理解之前进行任何修改
# 对于计算速度的追求，弃用了之前dydt_eval.py与Jac_eval.py脚本，采用新的jitcode库来实现计算速度的要求
# 该脚本不会对任何单独求解器语句解释，以防止不必要的修改导致的错误。为何会这么构造fun与solver3请参考
# dydt_eval.py以及matlab脚本文件中的dydt_eval.m，以及阅读jitcode的相关文档！Python在计算
# 上天然比较慢，而jitcode库采用了先编译后运行的方式，调用利用c生成动态链接库大大提高了计算速度
# ；但这样存在着两个个较大的缺陷，现在还没有解决。1: 求解器的固定性，这个含义就是该脚本生成或调用的
# 动态链接库其只能处理特定情况下的求解情况；因为模型中不断传递的Holdme这个参数要求某些物种在求解
# 时间中不变，而每个物种变与不变存在很大的可能性；每种可能性都需要不同的求解器去计算。为了简化OBM
# ，该版本只考虑两种可能性：a)所有vocs不变，b)所有vocs变化。因此才会用两个.so或两个.pyd。可以
# 尝试用C++的相关库解决，可以使用Julia的相关库解决，但如果使用python调用这些语言，即混合编程也
# 是比较复杂的一个地方。2: 针对MCM机理编译失败，CB05是一个具有100+大小的常微分方程组，编译时间
# 较短，而MCM是一个具有3000+大小的常微分方程组，利用笔记本编译失败，利用台式机编译一天失败；这也
# 为什么该OBM模型中内置了MCM的相关机理却没有运行该机理的原因。如果采用传统的dydt_eval.py与
# Jac_eval.py脚本运行的话，MCM机理下单核单个情景需要1个小时才能运行完成！


if platform != "win32":
    name = ".so"  # 应用于Linux与Mac
else:
    name = ".pyd"  # 需要在windows平台先安装有关软件后再生成，并且要保证生成与运行pyd的python版本一致


# jitcode求解器是基于scipy.integrate.ode与scipy.integrate.solve_ivp
# 其通过f来构造常微分方程组，在构造过程中能够传入可迭代符号参数param，因此多参数需要合并为单参数
# 先将其编译为C的动态链接库.so，之后调用.so设置参数的值，构造过程在单进程下进行，先构造再运行！当机理改变，iHold改变，应该重新构建求解器
def get_param(N):
    return [Symbol(f"p{i}") for i in range(N)]


def solver3(t_, conc_init_step, arg, solver="solver"):
    arg1 = concatenate([arg[0], arg[6], arg[-5]])
    param = get_param(len(arg1))
    file = dirname(__file__) + sep + solver + name
    if not exists(file):
        ode = jitcode(fun(arg[1], arg[2], arg[3], arg[-6], len(arg1), len(arg[0])), control_pars=param)
        ode.set_integrator("Radau")
        ode.save_compiled(file)

    ode = jitcode(control_pars=param, module_location=file, n=len(conc_init_step))
    ode.set_integrator("Radau")
    ode.set_parameters(arg1)
    ode.set_initial_value(conc_init_step)
    re = ode.integrate(t_).reshape(1, -1)

    return t_, re


def fun(f_, iG, iRO2, iHold, len_param, len_k):
    Y = array([y(i) for i in range(f_.shape[1])])
    param = get_param(len_param)

    k = param[:len_k]
    conc_bkgd = param[len_k:-1]
    kdil = param[-1]
    Y[1] = sum(Y[iRO2])
    G = Y[iG[:, 0]] * Y[iG[:, 1]]
    rates = k * G
    dydt = rates @ f_.toarray()
    dilrate = -kdil * (Y - conc_bkgd)
    dydt += dilrate
    dydt[iHold] = 0

    return dydt