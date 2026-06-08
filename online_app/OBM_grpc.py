from concurrent import futures
from online_app import OBM_EKMA_1day_grpc
import OBM_RIR_grpc
import time
import grpc
import receiver_pb2
import receiver_pb2_grpc
from json import loads
import uuid
import platform
import hashlib
from sys import exit

#  😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊😊


# 此为OBM模型线上版本的接口，即从此接受后端传来的数据，从此发送模拟后的结果到后端
# Receiver类名Receiver 与其下方法名 Fitting不要更改，因为这两个名称与import的receiver_pb2与receiver_pb2_grpc相关联
# ，这两个不是通过pip安装的第三方库，而是利用grpc与protobuf制作的数据传输方法。详细制作方法请查阅网络。
# 其定义了后端发送给OBM微服务的数据格式A，也定义了OBM微服务发送给后端的数据格式B！！！
# 为了方便所有线上平台微服务的通用性，与可扩展性，A与B均为字符串类型；即所有接收与发送的数据均为字符串，而不是数组，整型，浮点之类
# 为了解析数据，所有字符串均为JSON字符串类型，因为其与前后端交互较好，也能与python的字典类型直接对应
# 后端会将请求(包含数据和参数)打包成JSON字符串，OBM解析请求后进行计算，后将结果打包为python字典，再转化为python的字符串类型进行发送


_HOST = '[::]'  # 代表了OBM微服务监听的主机，[::]表示为本机
_PORT = 8769  # 监听的端口，需与后端进行协商，OBM一般为8769，PMF为8768，无人机为8766
MAX_MESSAGE_LENGTH = 6 * 1024 * 1024  # 最大接受数据长度，6M


class Receiver(receiver_pb2_grpc.ReceiverServicer):  # 此类名不可随意更改，应与receiver_pb2_grpc及receiver.proto保持一致

    def Fitting(self, request, context):  # 此函数名不可随意更改，应与receiver_pb2_grpc及receiver.proto保持一致
        model = int(loads(request.send_string)["model"])  # 先解析是需要计算EKMA还是RIR，1:EKMA，2:RIR
        if model == 1:
            value_return = OBM_EKMA_1day_grpc.start_simulation(request.send_string)  # 调用EKMA模块计算得到结果
        if model == 2:
            value_return = OBM_RIR_grpc.start_simulation(request.send_string)  # 调用RIR模块计算得到结果

        return receiver_pb2.receive_parameter(receive_string=str(value_return))  # 将dict转化为str后返回后端


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=30),  # 最大线程数，此客理解为同时计算的站点数
                         options=[('grpc.max_send_message_length', MAX_MESSAGE_LENGTH),
                                  ('grpc.max_receive_message_length', MAX_MESSAGE_LENGTH)])
    receiver_pb2_grpc.add_ReceiverServicer_to_server(Receiver(), server)

    server.add_insecure_port('{0}:{1}'.format(_HOST, _PORT))  # 添加监听主机与端口

    server.start()  # 启动微服务
    try:
        while True:
            time.sleep(60 * 60 * 24)
    except KeyboardInterrupt:
        server.stop(0)


def macid():  # 获得电脑，服务器的标识符
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    mac = "@".join([mac[i:i + 2] for i in range(0, 11, 2)])
    return mac


if __name__ == '__main__':
    string = "Laughing Out Loud " + macid() + platform.uname().release
    obj = hashlib.md5()
    obj.update(string.encode("utf-8"))
    if obj.hexdigest() != "a8f28f60be4667589a3d3d07afd9ab84":  # 将计算得到的hash值obj.hexdigest()与设定的hash值进行比对，不成功就退出程序
        print(obj.hexdigest() + ": hashed value is not correct")
        exit()
    serve()
