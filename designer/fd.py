# -*- coding: utf-8 -*-

import sys
import os.path
import json
# Import Qt modules
import sip
sip.setapi('QString', 2)
sip.setapi('QDateTime', 2)
sip.setapi('QDate', 2)
sip.setapi('QTime', 2)
sip.setapi('QVariant', 2)

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSlot
from model import ReportModel
from view import ReportView
from properties import property_tables


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        from fd_ui import Ui_MainWindow
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.scale = 100.0
        self.scene = QtGui.QGraphicsScene()
        #self.scene.setBackgroundBrush(
        #    QtGui.QBrush(QtGui.QColor('brown'), Qt.Dense4Pattern))
        self.set_scale()
        self.ui.graphicsView.setScene(self.scene)
        self.scene.selectionChanged.connect(self.on_scene_selectionChanged)
        self.model = None
        self.view = None
        self.selected = None

    def new_report(self):
        self.model = ReportModel()
        if self.view:
            self.scene.removeItem(self.view)
        self.view = ReportView(self.model)
        self.scene.addItem(self.view)
        self.filename = None
        self.setWindowTitle('Franq Designer [New Report]')

    def load_report(self, filename):
        try:
            new_model = ReportModel()
            with open(filename) as report_file:
                new_model.load(json.load(report_file))

            self.model = new_model
            if self.view:
                self.scene.removeItem(self.view)
            self.view = ReportView(self.model)
            self.scene.addItem(self.view)
            self.filename = filename
            self.setWindowTitle('Franq Designer [{0}]'
                .format(os.path.basename(self.filename)))
        except IOError as e:
            QtGui.QMessageBox('Open file', str(e))

    def save_report(self, filename):
        print 'save', self.model.save()
        with open(filename, 'wt') as report_file:
            json.dump(self.model.save(), report_file)
        self.filename = filename
        self.setWindowTitle('Franq Designer [{0}]'
            .format(os.path.basename(self.filename)))

    def set_scale(self):
        print "set_scale", self.scale
        self.ui.graphicsView.resetTransform()
        self.ui.graphicsView.scale(
            self.physicalDpiX() / 300.0 * self.scale / 100.0,
            self.physicalDpiY() / 300.0 * self.scale / 100.0)

    @pyqtSlot()
    def on_action_New_triggered(self):
        self.new_report()

    @pyqtSlot()
    def on_action_Open_triggered(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, 'Open File',
            filter='Franq reports (*.franq)')
        if filename:
            self.load_report(filename)

    @pyqtSlot()
    def on_action_Save_triggered(self):
        if not self.filename:
            filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File',
            filter='Franq reports (*.franq)')
            if not filename:
                return
        else:
            filename = self.filename
        self.save_report(filename)

    @pyqtSlot()
    def on_action_Save_As_triggered(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File',
            filter='Franq reports (*.franq)')
        if not filename:
            return
        self.save_report(filename)

    @pyqtSlot()
    def on_action_Zoom_In_triggered(self):
        if self.scale < 400.0:
            self.scale *= 2
            self.set_scale()

    @pyqtSlot()
    def on_action_Zoom_Out_triggered(self):
        if self.scale > 25:
            self.scale /= 2
            self.set_scale()

    def on_scene_selectionChanged(self):
        element = self.scene.selectedItems()[0].model
        self.property_table = property_tables[type(element)]
        self.property_table.setModel(element)
        self.ui.properties.setModel(self.property_table)


class DesignerApp(QtGui.QApplication):

    def __init__(self, argv):
        super(QtGui.QApplication, self).__init__(argv)
        try:
            filename = (arg for arg in argv[1:] if arg[0] != '-').next()
        except StopIteration:
            filename = None
        self.main_window = MainWindow()

        if filename:
            self.main_window.load_report(filename)
        else:
            self.main_window.new_report()

    def exec_(self):
        self.main_window.show()
        super(QtGui.QApplication, self).exec_()


if __name__ == '__main__':
    app = DesignerApp(sys.argv)
    sys.exit(app.exec_())
