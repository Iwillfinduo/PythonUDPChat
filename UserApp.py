import json
import socket
import sys
import threading
from time import sleep

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QRegularExpression, QThread, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QRegularExpressionValidator, QFont
from PyQt5.QtWidgets import QWidget


class UDPClient:
    def __init__(self, name: str, server_ip: str):
        server_host, server_port = server_ip.split(':')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_tuple = (server_host, int(server_port))
        self.socket.sendto(json.dumps({'type': 'connect'}).encode(), self.server_tuple)
        sleep(0.5)
        self.data = list()
        self.status = False
        threading.Thread(target=self.recive_data, daemon=True).start()

    def recive_data(self):
        data, addr = self.socket.recvfrom(1024 * 80)
        data = data.decode()
        data = json.loads(data)
        print(data, addr, 'outside')
        if isinstance(data, dict) and data['type'] == 'connected':
            self.status = True
        while self.status:
            data, addr = self.socket.recvfrom(1024)
            data = data.decode()
            print(data, addr)
            data = json.loads(data)
            if isinstance(data, dict) and data['type'] == 'data' and data['data'] != self.data:
                self.data = list(data['data'])
            if isinstance(data, dict) and data['type'] == 'disconnected':
                self.status = False
    def send(self, name, text):
        data = json.dumps({'type': 'message', 'message': (name, text)}).encode()
        self.socket.sendto(data, self.server_tuple)
        sleep(0.5)


class ChatView(QWidget):
    def __init__(self, name: str, server_ip: str):
        super().__init__()
        self.client = UDPClient(name, server_ip)
        self.data = list(self.client.data)
        self.name = name
        self.initUI()
        self.thread = DataUpdater(self)
        self.thread.need_update.connect(self.form_the_chat)
        self.thread.start()

    @pyqtSlot()
    def form_the_chat(self):
        scroll_layout = QtWidgets.QVBoxLayout()
        for pair in self.data:
            print(pair)
            name, text = pair[0], pair[1]
            name_font = QFont("Helvetica [Cronyx]", 14)
            text_font = QFont("Helvetica [Cronyx]", 10)
            if self.name == name:
                name_label = QtWidgets.QLabel(name + ' (You):')
                name_label.setAlignment(Qt.AlignRight)
                text_label = QtWidgets.QLabel(text)
                text_label.setAlignment(Qt.AlignRight)
            else:
                name_label = QtWidgets.QLabel(name + ':')
                name_label.setAlignment(Qt.AlignLeft)
                text_label = QtWidgets.QLabel(text)
                text_label.setAlignment(Qt.AlignLeft)
            name_label.setFont(name_font)
            text_label.setFont(text_font)
            gap = QtWidgets.QLabel(' ')
            layout = QtWidgets.QVBoxLayout()
            if self.name == name:
                layout.setAlignment(Qt.AlignRight)
            else:
                layout.setAlignment(Qt.AlignLeft)
            layout.addWidget(name_label)
            layout.addWidget(text_label)
            layout.addWidget(gap)
            scroll_layout.addLayout(layout)
        scroll_widget = QtWidgets.QWidget()
        scroll_widget.setFixedWidth(575)
        scroll_widget.setLayout(scroll_layout)
        self.scrollArea.setWidget(scroll_widget)
        self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        )
        self.scrollArea.horizontalScrollBar().setValue(
            self.scrollArea.horizontalScrollBar().maximum()
        )
    def initUI(self):
        self.scrollArea = QtWidgets.QScrollArea()
        self.text_input = QtWidgets.QLineEdit()
        self.send_button = QtWidgets.QPushButton('Send')
        self.send_button.clicked.connect(self.send_clicked)
        self.form_the_chat()
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.scrollArea)
        self.layout.addWidget(self.text_input)
        self.layout.addWidget(self.send_button)
        self.setLayout(self.layout)
        self.setGeometry(500, 500, 600, 600)
        self.setFixedSize(600, 600)
        super().show()

    def send_clicked(self):
        if self.text_input.text() != '':
            self.client.send(self.name, self.text_input.text())

class DataUpdater(QThread):
    need_update = pyqtSignal()
    def __init__(self, main_widget: ChatView):
        super().__init__()
        self.main_widget = main_widget

    def run(self):

        while self.main_widget.isVisible():
            captured_data = self.main_widget.client.data
            if self.main_widget.data != captured_data:
                self.main_widget.data = self.main_widget.client.data
                self.need_update.emit()

        self.quit()


class UserView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def ClickOnLogin(self):
        self.ui = ChatView(self.name_input.text(), self.ip_input.text())
        self.close()

    def initUI(self):
        self.login_label = QtWidgets.QLabel('Connect to chat server:')
        self.login_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText('Nickname')
        self.name_input.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.ip_input = QtWidgets.QLineEdit()
        self.ip_input.setPlaceholderText('127.0.0.1:8080')
        reg_ex = QRegularExpression(
            r"^(?:1?[0-9]{1,2}|2[0-4][0-9]|25[0-5])"
            r"(?:\.(?:1?[0-9]{1,2}|2[0-4][0-9]|25[0-5]))"
            r"{3}(?::(?:[0-9]{1,4}|[1-5][0-9]{4}|6[0-4]"
            r"[0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$")
        self.ip_validator = QRegularExpressionValidator(reg_ex, self.ip_input)
        self.ip_input.setValidator(self.ip_validator)
        self.button = QtWidgets.QPushButton('Login')
        self.button.clicked.connect(self.ClickOnLogin)

        self.layout = QtWidgets.QHBoxLayout()
        self.layout.addWidget(self.login_label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.ip_input)
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)

        self.setGeometry(500, 500, 600, 100)
        self.setFixedSize(600, 100)
        self.show()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    ui = UserView()
    sys.exit(app.exec_())
