from json import dumps
from pandas import read_csv
import grpc
try:
    from online_app import receiver_pb2, receiver_pb2_grpc
except ImportError:
    import receiver_pb2
    import receiver_pb2_grpc

# 此脚本为测试OBM_grpc.py是否正常工作的脚本，即模拟后端发送数据给OBM_grpc.py
# 在此可以详细了解后端发送的请求包含哪些东西


data = read_csv('/Users/xingyuwang/Desktop/OBM_EKMA/data_monitored.csv')  # 读取数据，DataFrame格式
data = data.to_dict(orient="list")  # 将数据按列转化为字典，每个value为一个数组
# with open("/Users/xingyuwang/Desktop/rir.txt") as f:
#    data = f.readlines()[0]

_HOST = 'localhost'  # 本机
_PORT = 8769  # 端口
MAX_MESSAGE_LENGTH = 6 * 1024 * 1024  # 最大数据发送量

# data=pd.read_csv('/Users/xingyuwang/Desktop/data.csv',encoding='utf-8',header=None)
# data=np.array(data)
# data=data.tolist()
# data=data.to_dict('list')
send_parameters = {"model": 1,  # 表示要运行哪个模块的参数，1:EKMA模块，2:RIR模块
                   "longitude": 120,  # 经度，默认120，纬度，默认30，海报，默认30
                   "latitude": 30,
                   "altitude": 30,
                   "i_array": [0.1, 0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2, 2.5],  # vocs情景，默认0.1到2.5，0.3为间隔
                   "j_array": [0.1, 0.4, 0.7, 1.0, 1.3, 1.6, 1.9, 2.2, 2.5],  # nox情景，默认0.1到2.5，0.3为间隔
                   "kdil": 1 / 86400,  # 稀释速率
                   "jcorr": 1,  # 光解速率校正系数
                   "p": 1001,  # 气压
                   "t": 20,  # 温度
                   "h": 75,  # 湿度
                   "bkgdconc": 1,  # 背景浓度系数
                   "data": data,  # 监测数据
                   "init": 0,  # 模型预热控制参数，只对RIR模块有效，1:预热模式，0:更新模式，2:情景削减模式
                   "ihold": 0,  # ihold
                   "random_id": "XMCJZ20220823",  # 不是随机ID，站点，因为RIR在预热与更新模式需要存储中间数据，需要用站点ID区分
                   "nox_cut": -1,  # 只对情景削减模式有效，表示nox削减比例
                   "vocs_cut": -1,  # 只对情景削减模式有效，表示vocs削减比例
                   "o3col": 300,  # 臭氧总量
                   "albedo": 0.3,  # 反射率
                   "linksteps": 1,  # 迭代控制参数
                   "fixnox": 0}  # NOx校正参数


def run():
    channel = grpc.insecure_channel('{0}:{1}'.format(_HOST, _PORT),
                                    options=(('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                                             ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)))

    stub = receiver_pb2_grpc.ReceiverStub(channel)
    response = stub.Fitting(receiver_pb2.send_parameters(send_string=dumps(send_parameters, ensure_ascii=False)))
    return eval(response.receive_string)


if __name__ == '__main__':
    result = run()
    # I_ARRAY=[0.1,0.4,0.7,1.0,1.3,1.6,1.9,2.2,2.5]
    # J_ARRAY=[0.1,0.4,0.7,1.0,1.3,1.6,1.9,2.2,2.5]
    # nox=float(result["y_value"])
    # vocs=float(result["x_value"])
    # plot_EKMA([vocs,nox],DataFrame(result["data"]).to_numpy(),I_ARRAY,J_ARRAY)
    print(result)
