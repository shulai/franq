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
from PyQt4.QtCore import Qt, pyqtSlot, QPoint
from model import (ReportModel, BandModel, ElementModel, LabelModel, FieldModel,
    FunctionModel)
from view import ReportView, BandView
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

        def mousePressEvent(event):
            QtGui.QGraphicsView.mousePressEvent(self.ui.graphicsView, event)
            if event.button() == Qt.LeftButton:
                self.on_view_click()
            elif event.button() == Qt.RightButton:
                pass

        self.ui.graphicsView.mousePressEvent = mousePressEvent
        self.ui.graphicsView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.graphicsView.customContextMenuRequested.connect(self.showContextMenu)
        self.model = None
        self.view = None
        self.selected = None
        self.mode = 'select'
        self._context_menu = QtGui.QMenu()

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
            QtGui.QMessageBox.critical(self, 'Open file', str(e))

    def save_report(self, filename):
        with open(filename, 'wt') as report_file:
            json.dump(self.model.save(), report_file, indent=4)
        self.filename = filename
        self.setWindowTitle('Franq Designer [{0}]'
            .format(os.path.basename(self.filename)))

    def set_scale(self):
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

    @pyqtSlot()
    def on_action_Select_triggered(self):
        self.mode = 'select'
        self.scene.clearSelection()

    @pyqtSlot()
    def on_action_Add_Label_triggered(self):
        self.mode = 'add_label'
        self.scene.clearSelection()

    @pyqtSlot()
    def on_action_Add_Field_triggered(self):
        self.mode = 'add_field'
        self.scene.clearSelection()

    @pyqtSlot()
    def on_action_Add_Function_triggered(self):
        self.mode = 'add_function'
        self.scene.clearSelection()

    def on_view_click(self):
        print('on_view_click')
        {
            'select': self.select_item,
            'add_label': self.add_label,
            'add_field': self.add_field,
            'add_function': self.add_function
            }[self.mode]()

    @pyqtSlot()
    def on_actionAlign_Top_triggered(self):
        try:
            head, *tail = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        except ValueError:
            return  # No items selected
        for item in tail:
            item.top = head.top

    @pyqtSlot()
    def on_actionAlign_Middle_triggered(self):
        try:
            head, *tail = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        except ValueError:
            return  # No items selected
        for item in tail:
            item.top = head.top + head.height / 2 - item.height / 2

    @pyqtSlot()
    def on_actionAlign_Bottom_triggered(self):
        try:
            head, *tail = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        except ValueError:
            return  # No items selected
        for item in tail:
            item.top = head.top + head.height - item.height

    @pyqtSlot()
    def on_actionAlign_Left_triggered(self):
        try:
            head, *tail = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        except ValueError:
            return  # No items selected
        for item in tail:
            item.left = head.left

    @pyqtSlot()
    def on_actionAlign_Center_triggered(self):
        try:
            head, *tail = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        except ValueError:
            return  # No items selected
        for item in tail:
            item.left = head.left + head.width / 2 - item.width / 2

    @pyqtSlot()
    def on_actionAlign_Right_triggered(self):
        try:
            head, *tail = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        except ValueError:
            return  # No items selected
        for item in tail:
            item.left = head.left + head.width - item.width

    @pyqtSlot()
    def on_actionDistribute_Horizontally_triggered(self):
        items = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        if len(items) < 2:
            return
        items.sort(key=lambda item: item.left)
        group_width = items[-1].left + items[-1].width - items[0].left
        items_widths = sum([item.width for item in items])
        space_available = group_width - items_widths
        if space_available < 0:
            return  # Unable to distribute
        space_between = space_available / (len(items) - 1)
        item_left = items[0].left
        for item in items[:-1]:
            item.left = item_left
            item_left += item.width + space_between

    @pyqtSlot()
    def on_actionDistribute_Vertically_triggered(self):
        items = [item.model for item in self.scene.selectedItems()
                if isinstance(item.model, ElementModel)]
        if len(items) < 2:
            return
        items.sort(key=lambda item: item.top)
        group_height = items[-1].top + items[-1].height - items[0].top
        items_heights = sum([item.height for item in items])
        space_available = group_height - items_heights
        if space_available < 0:
            return  # Unable to distribute
        space_between = space_available / (len(items) - 1)
        item_top = items[0].top
        for item in items[:-1]:
            item.top = item_top
            item_top += item.height + space_between

    def select_element(self, element):
        self.property_table = property_tables[type(element)]
        self.property_table.setModel(element)
        self.ui.properties.setModel(self.property_table)
        for row in range(0, self.property_table.rowCount()):
            delegate = self.property_table.delegate(row)
            #
            self.ui.properties.setItemDelegateForRow(row, delegate)

    def showContextMenu(self, pos):
        self._context_menu.clear()
        print(pos.x(), pos.y())
        transform = self.ui.graphicsView.transform()
        scene_pos = QPoint(pos.x() / transform.m11(), pos.y() / transform.m22())
        print('m11', transform.m11())
        item_view = self.scene.itemAt(scene_pos)
        print(item_view)
        if not item_view:
            return
        element = item_view.model
        if isinstance(element, ReportModel):
            print('reportmodel')
            if element.begin:
                action = self._context_menu.addAction('Remove begin band')
                action.triggered.connect(self.remove_begin_band)
            else:
                action = self._context_menu.addAction('Add begin band')
                action.triggered.connect(self.add_begin_band)

            if element.header:
                action = self._context_menu.addAction('Remove header band')
                action.triggered.connect(self.remove_header_band)
            else:
                action = self._context_menu.addAction('Add header band')
                action.triggered.connect(self.add_header_band)

            if element.footer:
                action = self._context_menu.addAction('Remove footer band')
                action.triggered.connect(self.remove_footer_band)
            else:
                action = self._context_menu.addAction('Add footer band')
                action.triggered.connect(self.add_footer_band)

            if element.summary:
                action = self._context_menu.addAction('Remove summary band')
                action.triggered.connect(self.remove_summary_band)
            else:
                action = self._context_menu.addAction('Add summary band')
                action.triggered.connect(self.add_summary_band)

        self._context_menu.popup(self.ui.graphicsView.mapToGlobal(pos))

    def select_item(self):
        element = self.scene.selectedItems()[0].model
        self.select_element(element)

    def add_element(self, ElementClass):
        print('add_element')
        view_item = self.scene.selectedItems()[0]
        if not view_item:
            return
        elif isinstance(view_item.model, ReportModel):
            print(view_item.model, 'return')
            return
        if isinstance(view_item.model, ElementModel):
            band = view_item.parentItem().model
        else:
            band = view_item.model

        print(band, band.description)
        el = ElementClass(band)
        band.elements.append(el)

        cursor_pos = self.ui.graphicsView.mapFromGlobal(QtGui.QCursor.pos())
        cursor_scene_pos = self.ui.graphicsView.mapToScene(cursor_pos)
        el_pos = view_item.mapFromScene(cursor_scene_pos)
        el.left = el_pos.x()
        el.top = el_pos.y()

        view_item.add_child(el, -1)

        self.select_element(el)
        self.mode = 'select'

    def add_label(self):
        self.add_element(LabelModel)

    def add_field(self):
        self.add_element(FieldModel)

    def add_function(self):
        self.add_element(FunctionModel)

    def remove_band(self, band_attr):
        model = getattr(self.model, band_attr)
        view = next((child
            for child in self.view.children
            if child.model == model))
        self.view.remove_child(view)
        self.scene.removeItem(view)
        model.parent = None
        setattr(self.model, band_attr, None)

    def add_begin_band(self):
        model = BandModel('Begin Band', self.model)
        self.model.begin = model
        view = BandView(model)
        self.view.add_child(view, 0)

    def remove_begin_band(self):
        self.remove_band('begin')

    def add_header_band(self):
        model = BandModel('Header Band', self.model)
        self.model.header = model
        view = BandView(model)
        position = 1 if self.model.begin else 0
        self.view.add_child(view, position)

    def remove_header_band(self):
        self.remove_band('header')

    def add_footer_band(self):
        model = BandModel('Footer Band', self.model)
        self.model.footer = model
        view = BandView(model)
        position = len(self.view.children) - 1 if self.model.summary else None
        self.view.add_child(view, position)

    def remove_footer_band(self):
        self.remove_band('footer')

    def add_summary_band(self):
        model = BandModel('Summary Band', self.model)
        self.model.summary = model
        view = BandView(model)
        self.view.add_child(view, None)

    def remove_summary_band(self):
        self.remove_band('summary')


class DesignerApp(QtGui.QApplication):

    def __init__(self, argv):
        super(QtGui.QApplication, self).__init__(argv)
        try:
            filename = (arg for arg in argv[1:] if arg[0] != '-').__next__()
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
