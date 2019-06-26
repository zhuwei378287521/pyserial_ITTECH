import sys
import time

import serial
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer, QThread
from ui_demo_1 import Ui_Form
from threading import Thread


class Pyqt5_Serial(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(Pyqt5_Serial, self).__init__()
        self.setupUi(self)
        self.init()
        self.setWindowTitle("串口小助手")
        self.ser = serial.Serial()
        self.port_check()

        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.threadSend = Thread(target=self.data_send_person,
                                 args=(['SYSTem:REMote', 'VOLTAGE 0', 'OUTPUT 1', 'VOLTAGE 12', ],))
        self.threadRece = Thread(target=self.print_receive_data_pop)
        self.threadSend.setDaemon(True)
        self.threadRece.setDaemon(True)

        self.receive_data_person = []

    def init(self):
        # 串口检测按钮
        self.s1__box_1.clicked.connect(self.port_check)

        # 串口信息显示
        self.s1__box_2.currentTextChanged.connect(self.port_imf)

        # 打开串口按钮
        self.open_button.clicked.connect(self.port_open)

        # 关闭串口按钮
        self.close_button.clicked.connect(self.port_close)

        # 发送数据按钮
        self.s3__send_button.clicked.connect(self.data_send)

        # 定时发送数据
        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.data_send)
        self.timer_send_cb.stateChanged.connect(self.data_send_timer)

        # 定时器接收数据
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.data_receive)

        # 清除发送窗口
        self.s3__clear_button.clicked.connect(self.send_data_clear)

        # 清除接收窗口
        self.s2__clear_button.clicked.connect(self.receive_data_clear)

    # 串口检测
    def port_check(self):
        # 检测所有存在的串口，将信息存储在字典中
        self.Com_Dict = {}
        port_list = list(serial.tools.list_ports.comports())
        self.s1__box_2.clear()
        for port in port_list:
            self.Com_Dict["%s" % port[0]] = "%s" % port[1]
            self.s1__box_2.addItem(port[0])
        if len(self.Com_Dict) == 0:
            self.state_label.setText(" 无串口")

    # 串口信息
    def port_imf(self):
        # 显示选定的串口的详细信息
        imf_s = self.s1__box_2.currentText()
        if imf_s != "":
            self.state_label.setText(self.Com_Dict[self.s1__box_2.currentText()])

    # 打开串口
    def port_open(self):
        self.ser.port = self.s1__box_2.currentText()
        self.ser.baudrate = int(self.s1__box_3.currentText())
        self.ser.bytesize = int(self.s1__box_4.currentText())
        self.ser.stopbits = int(self.s1__box_6.currentText())
        self.ser.parity = self.s1__box_5.currentText()
        # self.ser.baudrate = int('9600')
        # self.ser.bytesize = int('8')
        # self.ser.stopbits = int('1')
        # self.ser.parity = 'N'

        try:
            self.ser.open()
        except BaseException as e:
            print(e)
            QMessageBox.critical(self, "Port Error", "此串口不能被打开！")
            return None

        # 打开串口接收定时器，周期为2ms
        self.timer.start(2)

        if self.ser.isOpen():
            self.open_button.setEnabled(False)
            self.close_button.setEnabled(True)
            self.formGroupBox1.setTitle("串口状态（已开启）")

    # 关闭串口
    def port_close(self):
        self.timer.stop()
        self.timer_send.stop()
        try:
            self.ser.close()
        except:
            pass
        self.open_button.setEnabled(True)
        self.close_button.setEnabled(False)
        self.lineEdit_3.setEnabled(True)
        # 接收数据和发送数据数目置零
        self.data_num_received = 0
        self.lineEdit.setText(str(self.data_num_received))
        self.data_num_sended = 0
        self.lineEdit_2.setText(str(self.data_num_sended))
        self.formGroupBox1.setTitle("串口状态（已关闭）")

    # 发送数据
    def data_send(self):
        self.threadSend.start()  # 启动线程
        self.threadRece.start()

        if self.ser.isOpen():
            input_s = self.s3__send_text.toPlainText()
            if input_s != "":
                # 非空字符串               
                if self.hex_send.isChecked():
                    # hex发送
                    input_s = input_s.strip()
                    send_list = []
                    while input_s != '':
                        try:
                            num = int(input_s[0:2], 16)
                        except ValueError:
                            QMessageBox.critical(self, 'wrong data', '请输入十六进制数据，以空格分开!')
                            return None
                        input_s = input_s[2:].strip()
                        send_list.append(num)
                    input_s = bytes(send_list)
                else:
                    # ascii发送
                    input_s = (input_s + '\r\n').encode('utf-8')

            num = self.ser.write(input_s)
            self.data_num_sended += num
            self.lineEdit_2.setText(str(self.data_num_sended))

    def data_send_person(self, data_list):
        # 开启远程
        # 设置电压为0
        # 开启输出
        # data_list = ['SYSTem:REMote', 'VOLTAGE 0', 'OUTPUT 1', 'VOLTAGE 12']

        for i in data_list:
            input_s = (i + '\r\n').encode('utf-8')  # 蜂鸣器

            num = self.ser.write(input_s)
            self.data_num_sended += num
            self.lineEdit_2.setText(str(self.data_num_sended))

        for _ in range(0, 1000000):  # 不停的读取电流值
            input_s = ('MEASure:CURRent?' + '\r\n').encode('utf-8')
            num = self.ser.write(input_s)
            self.data_num_sended += num
            self.lineEdit_2.setText(str(self.data_num_sended))
            # time.sleep(1)
            time.sleep(0.05)
            print("读取次数" + str(_))

    # 接收数据
    def data_receive(self):
        try:
            num = self.ser.inWaiting()
        except:
            self.port_close()
            return None
        if num > 0:
            data = self.ser.read(num)
            num = len(data)
            # hex显示
            if self.hex_receive.checkState():
                out_s = ''
                for i in range(0, len(data)):
                    out_s = out_s + '{:02X}'.format(data[i]) + ' '
                self.s2__receive_text.insertPlainText(out_s)
            else:
                # 串口接收到的字符串为b'123',要转化成unicode字符串才能输出到窗口中去
                self.s2__receive_text.insertPlainText(data.decode('iso-8859-1'))
                self.receive_data_person.append(data.decode('iso-8859-1'))

            # 统计接收字符的数量
            self.data_num_received += num
            self.lineEdit.setText(str(self.data_num_received))

            # 获取到text光标
            textCursor = self.s2__receive_text.textCursor()
            # 滚动到底部
            textCursor.movePosition(textCursor.End)
            # 设置光标到text中去
            self.s2__receive_text.setTextCursor(textCursor)
        else:
            pass

    # 定时发送数据
    def data_send_timer(self):
        if self.timer_send_cb.isChecked():
            self.timer_send.start(int(self.lineEdit_3.text()))
            self.lineEdit_3.setEnabled(False)
        else:
            self.timer_send.stop()
            self.lineEdit_3.setEnabled(True)

    # 清除显示
    def send_data_clear(self):
        self.s3__send_text.setText("")

    def receive_data_clear(self):
        self.s2__receive_text.setText("")

    def print_receive_data_pop(self):
        while True:
            if self.receive_data_person.__len__() != 0:
                print(self.receive_data_person.pop())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myshow = Pyqt5_Serial()
    myshow.show()
    sys.exit(app.exec_())
