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
from model import (ReportModel, BandModel, SectionModel, DetailBandModel,
    ElementModel, LabelModel, FieldModel,
    FunctionModel)
from view import ReportView, BandView, SectionView
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
        #self.view_map = {}
        self.selected = None
        self.mode = 'select'
        self._context_menu = QtGui.QMenu()

    def new_report(self):
        self.model = ReportModel()
        if self.view:
            self.scene.removeItem(self.view)
        self.view = ReportView(self.model)
        self.scene.addItem(self.view)
        self.select_element(self.model)
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
            self.select_element(self.model)
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

    def generate_report(self, filename):
        with open(filename, 'wt') as source_file:
            source_file.write(self.model.generate())

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
    def on_action_Generate_triggered(self):
        if not self.filename:
            filename = QtGui.QFileDialog.getSaveFileName(self, 'Save File',
            filter='Franq reports (*.franq)')
            if not filename:
                return
        else:
            filename = self.filename
        self.save_report(filename)
        filename = filename.rsplit('.', 2)[0] + '_rpt.py'
        self.generate_report(filename)

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
        self.selected = element
        self.property_table = property_tables[type(element)]
        self.property_table.setModel(element)
        self.ui.properties.setModel(self.property_table)
        for row in range(0, self.property_table.rowCount()):
            delegate = self.property_table.delegate(row)
            #
            self.ui.properties.setItemDelegateForRow(row, delegate)

    def showContextMenu(self, pos):
        self._context_menu.clear()
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        item_view = self.scene.itemAt(scene_pos)
        if not item_view:
            return
        element = item_view.model
        self.select_element(element)
        if isinstance(element, ReportModel):
            if not element.begin:
                action = self._context_menu.addAction('Add begin band')
                action.triggered.connect(self.add_begin_band)

            if not element.header:
                action = self._context_menu.addAction('Add header band')
                action.triggered.connect(self.add_header_band)

            if not element.footer:
                action = self._context_menu.addAction('Add footer band')
                action.triggered.connect(self.add_footer_band)

            if not element.summary:
                action = self._context_menu.addAction('Add summary band')
                action.triggered.connect(self.add_summary_band)

            action = self._context_menu.addAction('Add section')
            action.triggered.connect(self.add_section)

        elif isinstance(element, BandModel):
            if element.parent == self.model:
                action = self._context_menu.addAction(
                    QtGui.QIcon.fromTheme('item-delete'), 'Remove Band')
                slots = {
                    self.model.begin: self.remove_begin_band,
                    self.model.header: self.remove_header_band,
                    self.model.footer: self.remove_footer_band,
                    self.model.summary: self.remove_summary_band
                    }
                action.triggered.connect(slots[element])
            elif isinstance(element.parent, SectionModel):
                if len(element.parent.detailBands) > 1:
                    action = self._context_menu.addAction(
                    QtGui.QIcon.fromTheme('item-delete'), 'Remove Band')
                    action.triggered.connect(self.remove_section_band)

                if isinstance(element, DetailBandModel):
                    if not element.detailBegin:
                        action = self._context_menu.addAction(
                            'Add detail begin band')
                        #action.triggered.connect(self.add_section_band)

                    if not element.columnHeader:
                        action = self._context_menu.addAction(
                            'Add column header band')
                        #action.triggered.connect(self.add_section_band)

                    if not element.columnFooter:
                        action = self._context_menu.addAction(
                            'Add column footer band')

                    if not element.detailSummary:
                        action = self._context_menu.addAction(
                            'Add detail summary band')
                        #action.triggered.connect(self.add_section_band)

                if not element.child:
                    action = self._context_menu.addAction('Add child band')
                    #action.triggered.connect(self.add_child_band)

                self._context_menu.addSeparator()
                action = self._context_menu.addAction('Add detail band')
                action.triggered.connect(self.add_section_detailband)

                action = self._context_menu.addAction('Add regular band')
                action.triggered.connect(self.add_section_band)

            elif isinstance(element.parent, BandModel):
                action = self._context_menu.addAction(
                    QtGui.QIcon.fromTheme('item-delete'), 'Remove Band')
                if element.parent.child == element:
                    action.triggered.connect(self.remove_child_band)
                elif isinstance(element.parent, DetailBandModel):
                    if element.parent.columnHeader == element:
                        action.triggered.connect(self.remove_column_header_band)
                    elif element.parent.columnFooter == element:
                        action.triggered.connect(self.remove_column_footer_band)
                    # TODO: Group header/footer
        elif isinstance(element, ElementModel):
            action = self._context_menu.addAction('Remove Element')
            action.triggered.connect(self.remove_element)

        self._context_menu.popup(self.ui.graphicsView.mapToGlobal(pos))

    def select_item(self):
        try:
            element = self.scene.selectedItems()[0].model
            self.select_element(element)
        except IndexError:
            pass

    def add_element(self, ElementClass):
        view_item = self.scene.selectedItems()[0]
        if not view_item:
            return
        elif isinstance(view_item.model, ReportModel):
            return
        if isinstance(view_item.model, ElementModel):
            band = view_item.parentItem().model
        else:
            band = view_item.model

        element = ElementClass()

        cursor_pos = self.ui.graphicsView.mapFromGlobal(QtGui.QCursor.pos())
        cursor_scene_pos = self.ui.graphicsView.mapToScene(cursor_pos)
        el_pos = view_item.mapFromScene(cursor_scene_pos)
        element.left = el_pos.x()
        element.top = el_pos.y()

        band.add_element(element)

        self.select_element(element)
        self.mode = 'select'

    def remove_element(self):
        element = self.selected
        self.select_element(element.parent)
        element.parent.remove_element(element)

    def add_label(self):
        self.add_element(LabelModel)

    def add_field(self):
        self.add_element(FieldModel)

    def add_function(self):
        self.add_element(FunctionModel)

    def add_report_band(self, band_attr, band):
        self.model.add_band(band_attr, band)
        self.select_element(band)

    def remove_report_band(self, band_attr):
        self.model.remove_band(band_attr)
        self.select_element(self.model)

    def add_begin_band(self):
        self.add_report_band('begin', BandModel('Begin Band'))

    def remove_begin_band(self):
        self.remove_report_band('begin')

    def add_header_band(self):
        self.add_report_band('header', BandModel('Header Band'))

    def remove_header_band(self):
        self.remove_report_band('header')

    def add_footer_band(self):
        self.add_report_band('footer', BandModel('Footer Band'))

    def remove_footer_band(self):
        self.remove_report_band('footer')

    def add_summary_band(self):
        self.add_report_band('summary', BandModel('Summary Band'))

    def remove_summary_band(self):
        self.remove_report_band('summary')

    def add_section(self):
        section = SectionModel()
        self.model.add_section(section)

    def remove_section(self):
        section = self.selected.parent
        self.model.remove_section(section)

    def add_section_detailband(self):
        section = self.selected.parent
        band = DetailBandModel()
        section.add_band(band)

    def add_section_band(self):
        section = self.selected.parent
        band = BandModel('Band')
        section.add_band(band)

    def remove_section_band(self):
        section = self.selected.parent
        section.remove_band(band)
        self.select_element(section)


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
