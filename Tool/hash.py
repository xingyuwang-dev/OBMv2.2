import uuid
import platform
import hashlib


# 该脚本很重要，其主要目的是计算整个OBM模型所处电脑或服务器的hash值
# 通过运行这个脚本，会得到一串hash值，将这个值嵌入到OBM软件与线上运行的相应地方可以得到校对电脑是否变化的目的
# 因此可以达到防止分发的作用。一般是程序的主入口出会有与该脚本类似的函数存在进行hash值校对，OBM软件的主入口
# 位于UI.py的最下面部分，线上运行的模型的主入口位于OBM_grpc.py的下面，可以查看与修改相应的地方。
# 该脚本不被任何其他模块，函数，脚本调用。其是单独运行的。因此在线上进行打包的时候该脚本需要单独被打包成一个
# 可执行文件，在具体部署到其他服务器上时，将这个可执行文件复制到目标服务器运行之后会得到一串hash值，之后将
# 这hash值替换OBM_grpc.py下相应地方的hash值。再将OBM模型打包，因为每台服务器的hash值不一样，而且打包
# 后的文件很难被反编译，修改源码；在每次运行时都会核对实时计算的hash值是否与编入的hash值一样，因此
# 可以达到隐藏源码与防分发的目标


def macid():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    mac = "@".join([mac[i:i+2] for i in range(0, 11, 2)])
    return mac


string = "Laughing Out Loud " + macid() + platform.uname().release
obj = hashlib.md5()
obj.update(string.encode("utf-8"))
print(obj.hexdigest())
