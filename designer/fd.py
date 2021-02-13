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

import builtins
builtins.PYQT_VERSION = 5

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot
from qonda.mvc.observable import Observable
from model import (ReportModel, BandModel, SectionModel, DetailBandModel,
    ElementModel, LabelModel, FieldModel,
    FunctionModel, LineModel, BoxModel, ImageModel, GroupModel, element_from_json)
from view import ReportView, grid
from properties import PropertyTable, property_registry, property_tables


class SelectionGroup(Observable):
    
    def __init__(self, elements):
        super().__init__()
        # Avoid premature call to __getattr__ 
        self.__dict__['_SelectionGroup__elements'] = elements
        for element in elements:
            element.add_callback(self.__observe)

    def __getattr__(self, name):
        """ Returns attribute value if equal in all items, None otherwise """
        if len(self.__elements) == 0:
            return None
        v = getattr(self.__elements[0], name)
        for element in self.__elements[1:]:
            v1 = getattr(element, name)
            if v != v1:
                return None
        return v
    
    def __setattr__(self, name, value):
        if value is None:  # FIXME: Find the way to do this safely 
            return
        for element in self.__elements:
            setattr(element, name, value)
    
    def __observe(self, sender, event_type, _, event_data):
        if event_type == 'update':
            self._notify('update', event_data)
 

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        from fd_ui import Ui_MainWindow
        super(MainWindow, self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.scale = 100.0
        self.scene = QtWidgets.QGraphicsScene()
        #self.scene.setBackgroundBrush(
        #    QtGui.QBrush(QtGui.QColor('brown'), Qt.Dense4Pattern))
        self.scene.selectionChanged.connect(self.update_property_view)
        self.set_scale()
        self.ui.graphicsView.setScene(self.scene)

        def mousePressEvent(event):
            QtWidgets.QGraphicsView.mousePressEvent(self.ui.graphicsView, event)
            if event.button() == Qt.LeftButton:
                self.on_view_click()
            elif event.button() == Qt.RightButton:
                pass

        self.ui.graphicsView.mousePressEvent = mousePressEvent
        self.ui.graphicsView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.graphicsView.customContextMenuRequested.connect(
            self.showContextMenu)
        self.model = None
        self.view = None
        self.__clipboard = None
        #self.view_map = {}
        self.mode = 'select'
        self._context_menu = QtWidgets.QMenu()

    def new_report(self):
        self.model = ReportModel()
        self.model.add_callback(self.observe_model)
        grid.x_spacing = self.model.grid_x_spacing
        grid.y_spacing = self.model.grid_y_spacing
        if self.view:
            self.scene.removeItem(self.view)
        self.view = ReportView(self.model)
        self.scene.addItem(self.view)
        self.select_element(self.view)
        self.filename = None
        self.setWindowTitle('Franq Designer [New Report]')

    def load_report(self, filename):
        try:
            new_model = ReportModel()
            with open(filename) as report_file:
                new_model.load(json.load(report_file))
            self.model = new_model
            grid.x_spacing = self.model.grid_x_spacing
            grid.y_spacing = self.model.grid_y_spacing
            self.model.add_callback(self.observe_model)
            if self.view:
                self.scene.removeItem(self.view)
            self.view = ReportView(self.model)
            self.scene.addItem(self.view)
            self.select_element(self.view)
            self.filename = filename
            self.setWindowTitle('Franq Designer [{0}]'
                .format(os.path.basename(self.filename)))
        except IOError as e:
            QtWidgets.QMessageBox.critical(self, 'Open file', str(e))

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

    def observe_model(self, model, event_type, _, attrs):
        if event_type == 'update' and attrs[0] in (
                'grid_x_spacing', 'grid_y_spacing'):
            grid.x_spacing = model.grid_x_spacing
            grid.y_spacing = model.grid_y_spacing
            self.view.update()

    @pyqtSlot()
    def on_action_New_triggered(self):
        self.new_report()

    @pyqtSlot()
    def on_action_Open_triggered(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File',
            filter='Franq reports (*.franq)')[0]
        if filename:
            self.load_report(filename)

    @pyqtSlot()
    def on_action_Save_triggered(self):
        if not self.filename:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
            filter='Franq reports (*.franq)')[0]
            if not filename:
                return
        else:
            filename = self.filename
        self.save_report(filename)

    @pyqtSlot()
    def on_action_Generate_triggered(self):
        if not self.filename:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
            filter='Franq reports (*.franq)')[0]
            if not filename:
                return
        else:
            filename = self.filename
        self.save_report(filename)
        filename = filename.rsplit('.', 2)[0] + '_rpt.py'
        self.generate_report(filename)

    @pyqtSlot()
    def on_action_Save_As_triggered(self):
        filename = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File',
            filter='Franq reports (*.franq)')[0]
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

    @pyqtSlot()
    def on_action_Add_Line_triggered(self):
        self.mode = 'add_line'
        self.scene.clearSelection()

    @pyqtSlot()
    def on_action_Add_Box_triggered(self):
        self.mode = 'add_box'
        self.scene.clearSelection()

    @pyqtSlot()
    def on_action_Add_Image_triggered(self):
        self.mode = 'add_image'
        self.scene.clearSelection()

    def on_view_click(self):
        {
            'select': self.select_item,
            'add_label': self.add_label,
            'add_field': self.add_field,
            'add_function': self.add_function,
            'add_line': self.add_line,
            'add_box': self.add_box,
            'add_image': self.add_image
            }[self.mode]()

    @pyqtSlot()
    def on_actionSnap_to_grid_triggered(self):
        grid.snap_to_grid = not grid.snap_to_grid

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

    def select_element(self, item):
        self.scene.clearSelection()
        item.setSelected(True)
        self.selected = item
        
    def update_property_view(self):
        selection = self.scene.selectedItems()
        if not selection:
            property_names = []
        else:
            element = selection[0].model
            property_names = {name
                            for name in property_tables[type(element)]}
            for item_view in selection[1:]:
                element = item_view.model
                property_names &= {name
                            for name in property_tables[type(element)]}
            property_names = list(property_names)
        property_names.sort()
        property_list = [property_registry[property_name] 
                         for property_name in property_names]
        self.property_table = PropertyTable(*property_list)
        if len(selection) == 0:
            self.property_table.setModel(None)
        elif len(selection) == 1:
            self.property_table.setModel(element)
        else:
            group = SelectionGroup([item_view.model for item_view in selection])
            self.property_table.setModel(group)
        self.ui.properties.setModel(self.property_table)
        for row in range(0, self.property_table.rowCount()):
            delegate = self.property_table.delegate(row)
            #
            self.ui.properties.setItemDelegateForRow(row, delegate)

    def showContextMenu(self, pos):
        self._context_menu.clear()
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        item_view = self.scene.itemAt(scene_pos, self.ui.graphicsView.transform())
        if not item_view:
            return
        self.select_element(item_view)
        element = item_view.model
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

        elif isinstance(element, SectionModel):

            action = self._context_menu.addAction('Remove section')
            action.triggered.connect(self.remove_section)

            action = self._context_menu.addAction('Add detail band')
            action.triggered.connect(self.add_section_detailband)

            action = self._context_menu.addAction('Add regular band')
            action.triggered.connect(self.add_section_band)

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

                if not element.child:
                    action = self._context_menu.addAction('Add child band')
                    action.triggered.connect(self.add_child_band)

            elif isinstance(element.parent, SectionModel):
                if len(element.parent.detailBands) > 1:
                    action = self._context_menu.addAction(
                    QtGui.QIcon.fromTheme('item-delete'), 'Remove Band')
                    action.triggered.connect(self.remove_section_band)

                if not element.child:
                    action = self._context_menu.addAction('Add child band')
                    action.triggered.connect(self.add_child_band)

                if isinstance(element, DetailBandModel):
                    if not element.detailBegin:
                        action = self._context_menu.addAction(
                            'Add detail begin band')
                        action.triggered.connect(self.add_detail_begin_band)

                    if not element.columnHeader:
                        action = self._context_menu.addAction(
                            'Add column header band')
                        action.triggered.connect(self.add_detail_header_band)

                    if not element.columnFooter:
                        action = self._context_menu.addAction(
                            'Add column footer band')
                        action.triggered.connect(self.add_detail_footer_band)

                    if not element.detailSummary:
                        action = self._context_menu.addAction(
                            'Add detail summary band')
                        action.triggered.connect(self.add_detail_summary_band)

                    action = self._context_menu.addAction(
                        'Add detail group')
                    action.triggered.connect(self.add_detail_group)

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
            item = self.scene.selectedItems()[0]
            # Bands and reports select separately
            if not isinstance(item.model, ElementModel):
                self.select_element(item)
        except IndexError:
            pass

    def add_element(self, element):
        selection = self.scene.selectedItems()
        assert(len(selection)==1)

        view_item = selection[0]

        if isinstance(view_item.model, ReportModel):
            return
        if isinstance(view_item.model, ElementModel):
            band = view_item.parentItem().model
        else:
            band = view_item.model

        cursor_pos = self.ui.graphicsView.mapFromGlobal(QtGui.QCursor.pos())
        cursor_scene_pos = self.ui.graphicsView.mapToScene(cursor_pos)
        el_pos = view_item.mapFromScene(cursor_scene_pos)
        element.left = el_pos.x()
        element.top = el_pos.y()
        if grid.snap_to_grid:
            grid.snap(element)
        band.add_element(element)
        self.mode = 'select'

    def remove_element(self):
        selection = self.scene.selectedItems()
        assert(len(selection)==1)
        view_item = selection[0]
        self.select_element(view_item.parentItem())
        element = view_item.model
        element.parent.remove_element(element)

    def add_label(self):
        self.add_element(LabelModel())

    def add_field(self):
        self.add_element(FieldModel())

    def add_function(self):
        self.add_element(FunctionModel())

    def add_line(self):
        print('add_line')
        self.add_element(LineModel())

    def add_box(self):
        self.add_element(BoxModel())

    def add_image(self):
        self.add_element(ImageModel())

    def add_report_band(self, band_attr, band):
        self.model.add_band(band_attr, band)

    def remove_report_band(self, band_attr):
        self.model.remove_band(band_attr)

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
        section = self.selected.model
        self.model.remove_section(section)

    def add_section_detailband(self):
        section = self.selected.model
        band = DetailBandModel()
        section.add_band(band)

    def add_section_band(self):
        section = self.selected.model
        band = BandModel('Band')
        section.add_band(band)

    def remove_section_band(self):
        band = self.selected.model
        section = band.parent
        section.remove_band(band)

    def add_detail_begin_band(self):
        detail_band = self.selected.model
        assert(detail_band.detailBegin is None)
        band = BandModel('Detail Begin Band')
        detail_band.detailBegin = band

    def add_detail_header_band(self):
        detail_band = self.selected.model
        assert(detail_band.columnHeader is None)
        band = BandModel('Detail Column Header')
        detail_band.columnHeader = band

    def add_detail_footer_band(self):
        detail_band = self.selected.model
        assert(detail_band.columnFooter is None)
        band = BandModel('Detail Column Footer')
        detail_band.columnFooter = band

    def add_detail_summary_band(self):
        detail_band = self.selected.model
        assert(detail_band.detailSummary is None)
        band = BandModel('Detail Summary Band')
        detail_band.detailSummary = band

    def add_detail_group(self):
        detail_band = self.selected.model
        assert(detail_band.detailSummary is None)
        group = GroupModel()
        detail_band.groups.append(group)

    def add_child_band(self):
        band = self.selected.model
        assert(band.child is None)
        child_band = BandModel('Child Band')
        band.add_band('child', child_band)

    def remove_child_band(self):
        self.selected.model.parent.remove_band('child')

    @pyqtSlot()
    def on_action_Copy_triggered(self):
        self.__clipboard = [item.model.save() for item in self.scene.selectedItems() 
                            if isinstance(item.model, ElementModel)]

    @pyqtSlot()
    def on_action_Cut_triggered(self):
        self.on_action_Copy_triggered()
        elements = [item.model for item in self.scene.selectedItems() 
                            if isinstance(item.model, ElementModel)]
        for element in elements:
            self.remove_element()
        
    @pyqtSlot()
    def on_action_Paste_triggered(self):
        for e in self.__clipboard:
            new_element = element_from_json(e)
            self.add_element(new_element)
            # Shift in order to allow multiple pastes without overlap
            e['top'] += 60
            e['left'] += 60


class DesignerApp(QtWidgets.QApplication):

    def __init__(self, argv):
        super().__init__(argv)
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
        super().exec_()


if __name__ == '__main__':
    app = DesignerApp(sys.argv)
    sys.exit(app.exec_())

