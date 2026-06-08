from scipy.integrate import ode, solve_ivp
from Tool.dydt_eval import dydt_eval
from Tool.Jac_eval import Jac_eval


# 该脚本已弃用，但依然可以使用

#t_out,c_out=ode15s(odefun,tspan,y0,options)
#其中tspan=[t0 tf]求微分方程组 y'=f(t,y) 从t0到tf的积分，初始条件为y0. 解数组y中的每一行都与
#列向量t中返回的值相对应. ode23s求解器只能解算质量矩阵为常量的问题, ode15s和ode23t可以解算具有奇异质量
#矩阵的问题(ODE). 还使用有options(使用odeset函数创建的参数)定义的积分设置
#class scipy.integrate.ode(f,jac=None)数值积分器的通用接口类
#使用(可选)jac=df/dy求解方程组y'(t)=f(t,y)
#注意：前两个参数f(t,y,...)与所使用的系统定义函数中的参数顺序相反scipy.integrate.odeint
#参数：
#f:可调用f(t,y,*f_args)
#Right-hand微分方程的一侧，t是一个矢量，y.shape -> (n,), f_args通过调用设置set_f_params(*args),应该返回一个标量，数组或列表（非元组）
#jac:可调用jac(t,y,*jac_args),可选
#Right-hand侧的雅可比行列式，jac[i,j]=d f[i]/d y[i],jac_通过调用set_jac_params(*args)来设置


def solver(t, conc_init_step, arg, t_e=[]):
    if len(t_e) == 0:
        t_e = [t]
    re = []
    y0 = conc_init_step
    t0 = 0
    ode15s = ode(dydt_eval, Jac_eval)
    ode15s.set_integrator("vode", method="bdf", order=15, nsteps=1000)
    ode15s.set_initial_value(y0, t0)
    ode15s.set_f_params(arg)
    ode15s.set_jac_params(arg)
    for ti in t_e:
        re.append(ode15s.integrate(ti))
    if not ode15s.successful():
        print("ode15s_solver failed, check your data and ode or Jac")

    return t0 + t, re


def solver2(t_, conc_init_step, arg, t_e=[]):  # 25% faster#dydt_eval和Jac_eval会反复被调用16次#??
    if len(t_e) == 0:
        t_e =[t_]
    y0 = conc_init_step
    t0 = 0
    radau = solve_ivp(dydt_eval, (t0, t_), y0, t_eval=t_e, max_step=1000, method="Radau", args=(arg, ), jac=Jac_eval)
    if not radau.success:
        print("ode15s_solver2 failed, check your data and ode or Jac")

    return t0 + t_, radau.y.T


#def f(t, y, arg1):
#    return dydt_eval(t, y, arg1)


#def jac(t, y, arg1):
#    return Jac_eval(t, y, arg1)