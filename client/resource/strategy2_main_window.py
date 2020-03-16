from PyQt5.QtWidgets import QMainWindow
from client.resource.ui.Strategy2MainWindow_UI import Ui_MainWindow

# 主窗体类
class Strategy2MainWindow(QMainWindow,Ui_MainWindow):

    def __init__(self):
        super(Strategy2MainWindow,self).__init__()
        self.setupUi(self)