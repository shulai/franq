# -*- coding: utf-8 -*-

import sys

# Import Qt modules
import sip
sip.setapi('QString', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QDate', 2)
sip.setapi('QTime', 2)
sip.setapi('QVariant', 2)

from PyQt4 import QtGui
from model import DesignerModel


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        from fd_ui import Ui_MainWindow
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


class DesignerApp(QtGui.QApplication):

    def __init__(self, argv):
        super(QtGui.QApplication, self).__init__(argv)
        try:
            filename = (arg for arg in argv[1:] if arg[0] != '-').next()
        except StopIteration:
            filename = None
        self.main_window = MainWindow()
        self.model = DesignerModel(self.main_window.ui.centralwidget, filename)

    def exec_(self):
        self.main_window.show()
        super(QtGui.QApplication, self).exec_()


if __name__ == '__main__':
    app = DesignerApp(sys.argv)
    sys.exit(app.exec_())
