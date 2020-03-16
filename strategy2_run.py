import six
import packaging
import packaging.version
import packaging.specifiers
import packaging.requirements
import sys
from PyQt5.Qt import QApplication
from client.resource.strategy2_main_window import Strategy2MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    mainWin = Strategy2MainWindow()
    mainWin.show()

    sys.exit(app.exec_())