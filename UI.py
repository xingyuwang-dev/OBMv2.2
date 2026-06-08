from sys import exit, argv  # 引入exit， argv函数。exit用于退出python程序，argv判断输入参数
from PyQt6.QtWidgets import QApplication, QPushButton, QCheckBox, \
    QMessageBox, QFileDialog, QLineEdit, QGridLayout, QLabel, QFrame, QSplashScreen, QVBoxLayout  # 构成UI界面的基本组件
# from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
# from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtGui import QPainter, QPixmap, QMovie  # 构成UI界面的基本组件
from PyQt6.QtCore import Qt, QRect, QTimer, QThread, QObject, pyqtSignal, QSettings, QDir  # Do not using fucking sub-class of QThread
from os.path import dirname, sep  # dirname可以获得python运行的绝对路径
from time import sleep
import uuid  # 获取UUID
import platform  # 获取平台类型
import hashlib  # 将组合的字符串计算hash值


send_dict, Width, Height = {}, 1440, 900  # 传递的参数，主界面宽度，主界面高度


class Example(QFrame):

    def __init__(self):
        super().__init__()
        self.win2 = Example2()
        self.WIDTH = 960
        self.HEIGHT = 600
        self.initUI()

    def initUI(self):
        #self.setToolTip("Maybe, Maybe not")

        btn = QPushButton("DATA")
        btn.setToolTip("DATA is the King!")
        btn.resize(btn.sizeHint())
        btn.clicked.connect(self.select_file)
        self.ftn = QLineEdit()
        self.ftn.resize(350, 30)
        self.ftn.setStyleSheet("background:rgba(255,255,255,0.1)")
        qss = "color:rgb(255,255,255);qproperty-alignment:AlignHCenter;background:rgba(255,255,255,0.1)"
        qss2 = "border-width: 1px;background:rgba(255,255,255,0.2);border-radius:5px;qproperty-alignment:AlignCenter;"
        qss3 = "color:rgb(181,126,220);font-weight:bold;background:rgba(255,255,255,0.3)"

        Parameter = QLabel("PARAMETERS")
        Parameter.setMaximumHeight(btn.height()-10)
        Parameter.setStyleSheet(qss2)
        Parameter.setToolTip("To control the Model, all parameters have default values, so you don't have to set them all")
        Longitude = QLabel("Longitude")
        self.Longitude_input = QLineEdit()
        self.Longitude_input.setPlaceholderText("120.00")
        self.Longitude_input.setStyleSheet(qss)
        Latitude = QLabel("Latitude")
        self.Latitude_input = QLineEdit()
        self.Latitude_input.setPlaceholderText("30.00")
        self.Latitude_input.setStyleSheet(qss)
        Altitude = QLabel("Altitude")
        self.Altitude_input = QLineEdit()
        self.Altitude_input.setPlaceholderText("30.00")
        self.Altitude_input.setStyleSheet(qss)
        Temperature = QLabel("Temperature")
        self.Temperature_input = QLineEdit()
        self.Temperature_input.setPlaceholderText("Default")
        self.Temperature_input.setStyleSheet(qss)
        Pressure = QLabel("Pressure")
        self.Pressure_input = QLineEdit()
        self.Pressure_input.setPlaceholderText("Default")
        self.Pressure_input.setStyleSheet(qss)
        Humidity = QLabel("Humidity")
        self.Humidity_input = QLineEdit()
        self.Humidity_input.setPlaceholderText("Default")
        self.Humidity_input.setStyleSheet(qss)
        Kdil = QLabel("Kdil")
        Kdil.setToolTip("Dilution rate")
        self.Kdil_input = QLineEdit()
        self.Kdil_input.setPlaceholderText("1/86400")
        self.Kdil_input.setStyleSheet(qss)
        Jcorr = QLabel("Jcorr")
        Jcorr.setToolTip("Photolysis rate correction factor")
        self.Jcorr_input = QLineEdit()
        self.Jcorr_input.setPlaceholderText("0~1:1")
        self.Jcorr_input.setStyleSheet(qss)
        Bkgdconc = QLabel("Bkgdconc")
        Bkgdconc.setToolTip("Background concentration factor")
        self.Bkgdconc_input = QLineEdit()
        self.Bkgdconc_input.setPlaceholderText("0~1:1")
        self.Bkgdconc_input.setStyleSheet(qss)
        O3col = QLabel("O3col")
        O3col.setToolTip("Overhead ozone column, DU")
        self.O3col_input = QLineEdit()
        self.O3col_input.setPlaceholderText("300")
        self.O3col_input.setStyleSheet(qss)
        Albedo = QLabel("Albedo")
        Albedo.setToolTip("Surface reflectance, unitless (range 0-1)")
        self.Albedo_input = QLineEdit()
        self.Albedo_input.setPlaceholderText("0~1:0.3")
        self.Albedo_input.setStyleSheet(qss)
        IHold = QLabel("IHold")
        IHold.setToolTip("This is a scalar flag, specifying how constrains are handled for each model step, 0 or 1")
        self.IHold_input = QLineEdit()
        self.IHold_input.setPlaceholderText("1")
        self.IHold_input.setStyleSheet(qss)
        Linksteps = QLabel("Linksteps")
        Linksteps.setToolTip("Flag for using end concentrations from one step to initialize the next step, 0 or 1")
        self.Linksteps_input = QLineEdit()
        self.Linksteps_input.setPlaceholderText("1")
        self.Linksteps_input.setStyleSheet(qss)
        FixNox = QLabel("FixNOx")
        FixNox.setToolTip("Flag for scaling total NOx to constrains, 0 or 1")
        self.FixNox_input = QLineEdit()
        self.FixNox_input.setPlaceholderText("0")
        self.FixNox_input.setStyleSheet(qss)
        EKMA = QLabel("For EKMA module")
        EKMA.setStyleSheet(qss2)
        NOx = QLabel("NOx")
        NOx.setToolTip("NOx cut scenario settings")
        self.NOx_input = QLineEdit()
        self.NOx_input.setPlaceholderText("start:interval:end")
        self.NOx_input.setStyleSheet(qss)
        VOCs = QLabel("VOCs")
        VOCs.setToolTip("It looks like the previous one")
        self.VOCs_input = QLineEdit()
        self.VOCs_input.setPlaceholderText("start:interval:end")
        self.VOCs_input.setStyleSheet(qss)
        self.check3 = QCheckBox()
        self.check3.setText("Single Point")
        self.check3.setToolTip("Only one point in EKMA figure")
        self.check4 = QCheckBox()
        self.check4.setText("Ridge")
        self.check4.setToolTip("If plot the ridge line")
        move_ridge = QLabel("Move")
        move_ridge.setToolTip("To move ridge, up or down(-)")
        self.move_ridge_input = QLineEdit()
        self.move_ridge_input.setPlaceholderText("0")
        self.move_ridge_input.setStyleSheet(qss)
        RIR = QLabel("For RIR module")
        RIR.setStyleSheet(qss2)
        Init = QPushButton("DATA(-1)")
        Init.setToolTip("For initialization, and this is usually the previous day's data, so -1(~_~)")
        Init.clicked.connect(self.select_file2)
        self.ftn2 = QLineEdit()
        self.ftn2.resize(350, 30)
        self.ftn2.setStyleSheet("background:rgba(255,255,255,0.1)")
        Model = QLabel("MODEL")
        Model.setStyleSheet(qss2)
        self.check = QCheckBox()
        self.check.setText("EKMA")
        self.check2 = QCheckBox()
        self.check2.setText("RIR")
        save = QPushButton("SAVE PATH")
        save.clicked.connect(self.select_path)
        self.ftn3 = QLineEdit()
        self.ftn3.resize(350, 30)
        self.ftn3.setStyleSheet("background:rgba(255,255,255,0.1)")

        self.obtn = QPushButton("Just Run!")
        self.obtn.setStyleSheet(qss3)
        self.obtn.clicked.connect(self.do_simulation)
        self.obtn.resize(self.obtn.sizeHint())
        qbtn = QPushButton("Quit")
        qbtn.setStyleSheet(qss3)
        qbtn.clicked.connect(QApplication.instance().quit)
        qbtn.resize(qbtn.sizeHint())

        grid = QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(btn, 1, 0)
        grid.addWidget(self.ftn, 1, 1, 1, 3)
        grid.addWidget(Parameter, 2, 0)
        grid.addWidget(Longitude, 3, 1)
        grid.addWidget(self.Longitude_input, 3, 2)
        grid.addWidget(Latitude, 3, 3)
        grid.addWidget(self.Latitude_input, 3, 4)
        grid.addWidget(Altitude, 3, 5)
        grid.addWidget(self.Altitude_input, 3, 6)
        grid.addWidget(Temperature, 4, 1)
        grid.addWidget(self.Temperature_input, 4, 2)
        grid.addWidget(Pressure, 4, 3)
        grid.addWidget(self.Pressure_input, 4, 4)
        grid.addWidget(Humidity, 4, 5)
        grid.addWidget(self.Humidity_input, 4, 6)
        grid.addWidget(Kdil, 5, 1)
        grid.addWidget(self.Kdil_input, 5, 2)
        grid.addWidget(Jcorr, 5, 3)
        grid.addWidget(self.Jcorr_input, 5, 4)
        grid.addWidget(Bkgdconc, 5, 5)
        grid.addWidget(self.Bkgdconc_input, 5, 6)
        grid.addWidget(O3col, 6, 1)
        grid.addWidget(self.O3col_input, 6, 2)
        grid.addWidget(Albedo, 6, 3)
        grid.addWidget(self.Albedo_input, 6, 4)
        grid.addWidget(IHold, 6, 5)
        grid.addWidget(self.IHold_input, 6, 6)
        grid.addWidget(Linksteps, 7, 1)
        grid.addWidget(self.Linksteps_input, 7, 2)
        grid.addWidget(FixNox, 7, 3)
        grid.addWidget(self.FixNox_input, 7, 4)
        grid.addWidget(EKMA, 8, 2)
        grid.addWidget(NOx, 8, 3)
        grid.addWidget(self.NOx_input, 8, 4)
        grid.addWidget(VOCs, 8, 5)
        grid.addWidget(self.VOCs_input, 8, 6)
        grid.addWidget(self.check3, 9, 3)
        grid.addWidget(self.check4, 9, 4)
        grid.addWidget(move_ridge, 9, 5)
        grid.addWidget(self.move_ridge_input, 9, 6)
        grid.addWidget(RIR, 10, 2)
        grid.addWidget(Init, 10, 3)
        grid.addWidget(self.ftn2, 10, 4, 1, 3)
        grid.addWidget(Model, 11, 0)
        grid.addWidget(self.check, 11, 1)
        grid.addWidget(self.check2, 11, 2)
        grid.addWidget(save, 12, 0)
        grid.addWidget(self.ftn3, 12, 1, 1, 3)
        grid.addWidget(self.obtn, 13, 7)
        grid.addWidget(qbtn, 13, 8)
        self.setLayout(grid)

        self.setGeometry(100, 100, self.WIDTH, self.HEIGHT)
        self.setWindowTitle("OBM v2.2")

    def paintEvent(self, event):  # 当继承于Widget时，重载此方法设置
        painter = QPainter(self)
        painter.drawRect(self.rect())
        pixmap = QPixmap(dirname(__file__) + sep + "poster_mars_front_c.jpg")
        painter.drawPixmap(self.rect(), pixmap)

    def closeEvent(self, event) -> None:  # 关闭QWidget会产生QCloseEvent事件
        reply = QMessageBox.question(self, "Message",
                                     "Are you sure to quit?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
            #self.win2.close()
            exit(0)
        else:
            event.ignore()

    def keyPressEvent(self, e):  # 鼠标点击事件
        if e.key() == Qt.Key.Key_Escape.value:
            self.close()

    def select_file(self):  # 选择文件函数1
        settings = QSettings("MySoft", "MyApp")
        lastfile = settings.value("lastfile", QDir().homePath())
        filename, _ = QFileDialog.getOpenFileNames(self, "Select DATA", lastfile,
                                                   "All Files(*);;""*.xls;;*.xlsx;;*.csv;;*.txt")
        if filename:
            self.ftn.setText(filename[0])
            settings.setValue("lastfile", filename[0])

    def select_file2(self):  # 选择文件函数2
        settings = QSettings("MySoft", "MyApp")
        lastfile2 = settings.value("lastfile2", QDir().homePath())
        filename, _ = QFileDialog.getOpenFileNames(self, "Select DATA", lastfile2,
                                                   "All Files(*);;""*.xls;;*.xlsx;;*.csv;;*.txt")
        if filename:
            self.ftn2.setText(filename[0])
            settings.setValue("lastfile2", filename[0])

    def select_path(self):  # 选择文件夹函数
        settings = QSettings("MySoft", "MyApp")
        lastDir = settings.value("lastDir", QDir().homePath())
        filename = QFileDialog.getExistingDirectory(self, "Select save path", lastDir)

        if filename:
            self.ftn3.setText(filename)
            settings.setValue("lastDir", filename)

    def do_simulation(self):  # OBM模型调用函数
        self.simulation_thread = QThread()
        self.simulation = Worker()
        self.simulation.moveToThread(self.simulation_thread)
        self.win2.show()

        if not self.check.isChecked() and not self.check2.isChecked():
            self.check.setChecked(True)

        global send_dict
        send_dict |= {"data": self.ftn.text(), "longtitude": self.Longitude_input.text(),
                      "latitude": self.Latitude_input.text(), "altitude": self.Altitude_input.text(),
                      "temperature": self.Temperature_input.text(), "pressure": self.Pressure_input.text(),
                      "humidity": self.Humidity_input.text(), "kdil": self.Kdil_input.text(),
                      "jcorr": self.Jcorr_input.text(), "bkgdconc": self.Bkgdconc_input.text(),
                      "o3col": self.O3col_input.text(), "albedo": self.Albedo_input.text(),
                      "save_path": self.ftn3.text()}
        send_dict |= {"ihold": self.IHold_input.text(), "linksteps": self.Linksteps_input.text(),
                      "fixnox": self.FixNox_input.text(), "I_ARRAY": self.NOx_input.text(), "J_ARRAY": self.VOCs_input.text(),
                      "data2": self.ftn2.text(), "EKMA": self.check.isChecked(), "RIR": self.check2.isChecked(),
                      "single": self.check3.isChecked(), "ridge": self.check4.isChecked(), "move": self.move_ridge_input.text()}

        self.simulation_thread.started.connect(self.simulation.do_work)  # 直接用lambda传参给子线程会出现奇怪的子页面卡顿
        self.simulation_thread.start()
        self.simulation.signal.connect(self.reaction)
        print(send_dict)

    def mousePressEvent(self, e):  # 接受鼠标点击事件插槽
        x_loc = e.pos().x()
        y_loc = e.pos().y()
        if y_loc < 10:
            if self.frameGeometry().width() - x_loc < 10:
                from tool.funny import the_python
                the_python()
            elif 10 < self.frameGeometry().width() - x_loc <= 20:
                import webbrowser
                webbrowser.open("https://eyes.nasa.gov/apps/orrery/#/home")
                webbrowser.open("https://murray-lab.caltech.edu/CTX/V01/SceneView/MurrayLabCTXmosaic.html")
            elif 20 < self.frameGeometry().width() - x_loc <= 30:
                from tool.funny import the_hanabi
                the_hanabi()

    def reaction(self, signal):  # 接受OBM线程返回的结果，判断是否运行成功
        self.simulation_thread.quit()
        self.win2.close()
        if signal != "1":
            QMessageBox.critical(self, "Error", signal)
        else:
            from random import randint
            if randint(0, 1000) == 42:  # The final answer!!!
                pass  # Do some interesting things, because it's final answer
            else:
                QMessageBox.information(self, "Result", "Success!")


class Example2(QFrame):  # 该类是用于设置进度条界面

    def __init__(self):
        super().__init__()
        self.WIDTH = 600  # 宽度
        self.HEIGHT = 400  # 高度
        self.initUI()  # 调用initUI函数

    def initUI(self):  # 进度条页面初始化函数
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setStyleSheet("background-color: rgba(70, 130, 180, 0.7);")
        pix = QPixmap(dirname(__file__) + sep + "beyond.jpeg")
        gif = QMovie(dirname(__file__) + sep + "go.gif")
        label = QLabel(self)
        label.setPixmap(pix)
        label.setScaledContents(True)
        label.setGeometry(QRect(150, 25, 300, 250))
        label2 = QLabel(self)
        label2.setMovie(gif)
        label2.setScaledContents(True)
        label2.setGeometry(QRect(300, 300, 120, 90))
        gif.start()

        self.label_info = QLabel("", self)
        self.label_info.setGeometry(50, 300, 300, 30)
        self.label_info.setStyleSheet("color:rgb(255,255,255);font-weight:bold;font-size:20px;background:rgba(255,255,255,0)")

        left = int((Width - 600) / 2)
        up = int((Height - 400) / 2)
        self.setGeometry(left, up, self.WIDTH, self.HEIGHT)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
    def show(self):  # 进度条页面显示时调用的函数
        self.label_info.setText("Starting...")
        super(Example2, self).show()
        self.set_loader()

    def set_loader(self):
        self.timer = QTimer()
        self.timer.singleShot(2000, lambda: self.label_info.setText("Calculating..."))

    def close(self) -> bool:  # 进度条页面关闭时会调用的函数
        self.timer.singleShot(0, lambda: self.label_info.setText("Ending..."))
        self.timer.singleShot(1000, super(Example2, self).close)
        self.timer.stop()
        return True


"""
    def set_loader(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_set_part)
        self.timer.start(100)

    def process_set_part(self):
        self.progressBar.setStyleSheet("QProgressBar{border:2px;border-radius: 5px; background-color: #FFFFFF;"
                                       "text-align: center; color: rgb(70, 130, 180)}"
                                       "QProgressBar::chunk {background:QLinearGradient(x1:0,y1:0,x2:2,y2:0,"
                                       "stop:0 #666699,stop:1 #DB7093);};")
        if self.progressBar.value() >= 1:
            self.label_info.setText("Calculating...")
        if self.progressBar.value() == 100:
            self.label_info.setText("Done")
            sleep(3)
            self.window().close()
            self.timer.stop()
        self.progressBar.setValue(self.progressBar.value() + 1)
"""


class SplashScreen(QSplashScreen):  # 该类用于程序启动界面

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        Label = QLabel(self)
        Label.setText("<font color=red>E<font><font color=black>X<font><font color=red>PEC<font>")
        Label.setStyleSheet("qproperty-alignment:AlignHCenter;font-weight:bold;font-size:100px")
        Label2 = QLabel("T E C H N O L O G Y", self)
        Label2.setStyleSheet("color:rgb(255,0,0);qproperty-alignment:AlignHCenter;font-weight:bold;font-size:35px")
        Label3 = QLabel("welcome to use the tool", self)
        Label3.setStyleSheet("color:rgb(255,255,255);qproperty-alignment:AlignHCenter;font-size:30px;")
        Label4 = QLabel("Version 2.2 Now Loading...", self)
        Label4.setStyleSheet("color:rgb(255,255,255);qproperty-alignment:AlignHCenter;font-size:20px")
        Label4.adjustSize()
        Label5 = QLabel("Copyright © 2015 - 2023 Data Application and Research Group, All Rights Reserved", self)
        Label5.setStyleSheet("color:rgb(255,255,255);qproperty-alignment:AlignHCenter;font-size:10px")
        Label5.adjustSize()
        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        vbox.addWidget(Label)
        vbox.addWidget(Label2)
        vbox.addWidget(Label3)
        #Label.move(100, 200)#Label2.fontMetrics().boundingRect(Label.text()).width()
        Label4.move(10, 700)
        Label5.move(10, 735)
        vbox.setContentsMargins(0, 200, 0, 350)
        self.setLayout(vbox)

    def mousePressEvent(self, event):
        pass


class Worker(QObject):  # 该类是用来调用OBM模型的类

    signal = pyqtSignal(str)  # 该信号用来返回string类型的值

    def __init__(self):
        super().__init__()

    def do_work(self):
        global send_dict
        try:
            if send_dict["EKMA"]:
                from OBM_EKMA_1day2 import EKMA_start
                symbol = EKMA_start(send_dict)
            if send_dict["RIR"]:
                from OBM_RIR2 import RIR_start
                symbol = RIR_start(send_dict)
            self.signal.emit(symbol)
        except Exception as e:
            self.signal.emit(str(e))


def main():  # 该函数用于调用程序启动页面，调用程序主页面，程序的入口
    app = QApplication(argv)
    size = QApplication.primaryScreen().geometry()
    global Width, Height
    Width, Height = size.width(), size.height()
    splash = SplashScreen()
    width, height = 500, 750
    splash.setPixmap(QPixmap(dirname(__file__) + sep + "ice.jpeg").scaled(width, height))
    #splash.showMessage("")
    screen = QApplication.primaryScreen().geometry()
    left = int((screen.width() - width) / 2)
    up = int((screen.height() - height) / 2)
    splash.setGeometry(left, up, width, height)
    splash.show()
    sleep(5)
    win = Example()
    splash.finish(win)
    win.show()
    exit(app.exec())


def macid():
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    mac = "@".join([mac[i:i+2] for i in range(0, 11, 2)])
    string = "Laughing Out Loud " + mac + platform.uname().release
    obj = hashlib.md5()
    obj.update(string.encode("utf-8"))
    return obj.hexdigest()


if __name__ == "__main__":  # 程序入口，程序执行从此开始，首先调用macid函数计算哈希值(hash value)是否等于程序内部的hash值
    if macid() != "a8f28f60be4667589a3d3d07afd9ab84":  # 该哈希值需要运算hash.py文件后得到，不同电脑不一样
        exit(0)  # 如果程序运行时计算得到hash值与预设的hash值不一样，则直接退出程序
    main()  # 运行main()函数
