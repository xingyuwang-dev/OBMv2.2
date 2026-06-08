# OBM Python 版本

本项目是大气化学箱式模型 OBM 的 Python 版本，由原 Matlab/F0AM 思路迁移而来。仓库同时保留了三类使用形态：

- `offline_test/`：线下开发与测试入口，包含 EKMA 与 RIR 两条流程。
- `online_app/`：Linux 服务器线上 gRPC 服务入口，后端通过 JSON 字符串请求模型计算。
- `desktop_app/`：Windows/桌面版 PyQt6 图形界面入口。

## 目录说明

| 路径 | 作用 |
| --- | --- |
| `core/` | 模型核心层：化学机理初始化、EKMA/RIR 计算编排、F0AM 核心求解、ODE/Jacobian 与数密度/湿度等核心物理量。 |
| `CB05/` | CB05 化学机理、反应、速率常数与物种转换。 |
| `MCMv331/` | MCM v3.3.1 化学机理相关 Python 模块。当前主要保留，计算上默认多使用 CB05。 |
| `tool/` | 非核心工具函数：IOA、数据平均、文件转换、进度显示、路径/hash/娱乐辅助等。 |
| `photolysis/` | 光解速率计算与查表插值。 |
| `post_process/` | EKMA、臭氧生成速率、OH 反应活性、光解速率等绘图。 |
| `offline_test/` | 本地脚本式测试入口。 |
| `online_app/` | gRPC 服务端与客户端测试脚本。 |
| `desktop_app/` | PyQt6 桌面界面与桌面版 EKMA/RIR 包装。 |
| `media/` | 桌面程序使用的图片资源。 |

## 主要入口

### 线下测试

- EKMA：`offline_test/OBM_EKMA_1day.py`
- RIR：`offline_test/OBM_RIR.py`

这两个脚本当前仍包含本地硬编码路径，例如桌面目录下的输入数据、转换表、输出目录。运行前需要按实际机器修改脚本顶部的 `main_path`、`data_file`、`compound_name_file` 等配置。

### 线上服务

- 服务端：`online_app/OBM_grpc.py`
- 测试客户端：`online_app/OBM_grpc_client.py`

gRPC 服务默认监听 `8769` 端口。请求与响应都以字符串形式传输，字符串内容一般为 JSON。请求字段 `model` 用于分流：

- `model == 1`：调用 EKMA。
- `model == 2`：调用 RIR。

### 桌面程序

- UI 入口：`desktop_app/UI.py`
- 桌面版 EKMA 包装：`desktop_app/OBM_EKMA_1day2.py`
- 桌面版 RIR 包装：`desktop_app/OBM_RIR2.py`

桌面程序依赖 PyQt6。图片资源位于 `media/`。

## 运行前依赖

仓库没有锁定依赖文件。根据静态导入关系，主要依赖包括：

- 基础数值与数据：`numpy`、`pandas`、`scipy`
- 绘图：`matplotlib`、`pylab`
- 高性能求解：`jitcode`、`symengine`
- 线上服务：`grpcio`
- 桌面界面：`PyQt6`
- 可选/辅助：`pyaudio`、`pygame`、`diffeqpy`、`numba`

若要运行模型，请在目标环境中按实际入口补齐依赖，并注意 `core/solver.so`、`core/solver2.so`、`core/solver.pyd` 与 `core/solver2.pyd` 与运行平台、Python 版本、机理设置是否匹配。

## 核心计算流程

EKMA 主链路：

1. 入口脚本读取监测数据与物种转换表。
2. `tool.data_average` 进行日平均与 VOCs/NOx 均值计算。
3. `CB05.CB05_transfrom` 将监测物种映射为 CB05 模型物种。
4. `core.data_run` 构造 NOx/VOCs 情景矩阵。
5. `core.F0AM_ModelCore2` 先初始化化学机理，再逐情景积分。
6. `core.jit_solver.solver3` 调用已编译求解器。
7. `post_process.plot` 绘制 EKMA 图。

RIR 主链路：

1. 入口脚本读取监测数据与转换表。
2. `core.RIR_data_process` 完成单日或单小时数据处理。
3. `core.RIR_data_run2.initialize` 进行预热并写入中间 `result.json`。
4. `core.RIR_data_run2.update` 构造削减情景并计算 RIR、臭氧生成/消耗、OH 活性等结果。
5. `post_process.plot_ozone`、`plot_OH`、`plot_photolysis` 输出图件。

更完整的调用关系见 [ARCHITECTURE.md](ARCHITECTURE.md)，英文版见 [ARCHITECTURE_EN.md](ARCHITECTURE_EN.md)，核心化学反应方程见 [CHEMICAL_REACTIONS.md](CHEMICAL_REACTIONS.md)。

## 本次已修复/调整的问题

- 修复 `core/F0AM_ModelCore.py`、`core/F0AM_ModelCore2.py` 对 `InitializeChemistry` 的包内导入路径。
- 修复 `core/InitializeChemistry.py` 中 `dict_keys.index()` 的 Python 运行时错误。
- 修复 `online_app/` 中 gRPC 模块的包内导入兼容性。
- 补齐缺失的 `online_app/receiver_pb2.py`，提供当前服务所需的 `send_parameters` 与 `receive_parameter` 字符串消息。
- 修复桌面 UI 对 `media/` 图片资源与 RIR 模块的路径引用。
- 修复 EKMA 收尾音效对 `tool/ffVII_victory.wav` 的路径引用。
- 将核心求解与机理初始化相关文件从 `tool/` 移动到 `core/`：`AddSpecies.py`、`CovertHumidity.py`、`NumberDensity.py`、`dydt_eval.py`、`Jac_eval.py`、`ode15s.py`、`jit_solver.py`、`julia_solver.py` 以及求解器动态库。

## 注意事项

- `offline_test/` 与 `online_app/` 中仍有历史硬编码路径，部署前需要配置为目标环境路径。
- gRPC 线上入口包含服务器硬件 hash 校验逻辑，迁移服务器时需要按 `tool/hash.py` 说明更新校验值。
- MCM 机理体量很大，当前求解器与性能设计主要面向 CB05；切换 MCM 前需要重新评估求解器构建与运行耗时。
- `core/julia_solver.py` 属于实验性求解器；`tool/funny.py` 等属于娱乐辅助功能，不是主流程必需。
