# -*- coding: utf-8 -*-

import json
from PyQt4 import QtGui
from PyQt4.QtCore import Qt

mm = 300 / 25.4


class ElementModel(object):

    def load(self, json):
        self.top = json['top']
        self.left = json['left']
        self.width = json['width']
        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None
        self.font = None


class TextModel(ElementModel):

    def __init__(self, parent):
        super(TextModel, self).__init__()
        self.view = TextView(parent.view)


class TextView(QtGui.QWidget):
    pass


class LabelModel(TextModel):

    def load(self, json):
        super(LabelModel, self).load()
        self.text = json['text']


class FieldModel(TextModel):

    def load(self, json):
        super(FieldModel, self).load()
        self.fieldName = json['fieldName']
        self.format = json['format']


class FunctionModel(TextModel):

    def load(self, json):
        super(FunctionModel, self).load()
        self.func = json['func']


class LineModel(ElementModel):

    def __init__(self, parent):
        super(LineModel, self).__init__()
        self.view = LineView(parent.view)


class LineView(QtGui.QWidget):
    pass


class BoxModel(ElementModel):

    def __init__(self, parent):
        super(BoxModel, self).__init__()
        self.view = BoxView(parent.view)


class BoxView(QtGui.QWidget):
    pass


class ImageModel(ElementModel):

    def __init__(self, parent):
        super(ImageModel, self).__init__()
        self.view = ImageView(parent.view)


class ImageView(QtGui.QWidget):
    pass


element_classes = {
    'label': LabelModel,
    'field': FieldModel,
    'function': FunctionModel,
    'line': LineModel,
    'box': BoxModel,
    'image': ImageModel,
    }


class BandModel(object):

    def __init__(self, parent):
        self.parent = parent
        self.elements = []
        self.view = BandView(self.parent.view)

    def load(self, json):

        def element(el_json):
            class_, args = el_json
            e = element_classes[class_](self)
            e.load(args)
            return e

        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None
        self.font = None

        if json['elements']:
            self.elements = [element(e) for e in json['elements']]


class BandView(QtGui.QWidget):
    def __init__(self, parent):
        super(BandView, self).__init__(parent)

    def paintEvent(self, event):

        super(BandView, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        pen = QtGui.QPen(Qt.DotLine)
        pen.setColor(QtGui.QColor(192, 192, 255))
        painter.setPen(pen)
        rect = self.rect()
        painter.drawLine(rect.topLeft(), rect.topRight())
        painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.topLeft(), rect.bottomLeft())


class ReportModel(object):

    def __init__(self, designer_model, container):

        super(ReportModel, self).__init__()
        self.designer_model = designer_model
        # Ok?
        self.title = u'Report'
        self._paperSize = 'A4'
        self._width = 210 * mm
        self._height = 297 * mm

        self.begin = None
        self.header = None
        self.detail = None
        self.footer = None
        self.summary = None

        self.view_container = container
        self.view = ReportView(container, self)
        self.view.resize(self._width * self.designer_model.scale / 300,
            self._height * self.designer_model.scale / 300)

    def load(self, json):

        if json['begin']:
            self.begin = BandModel(self)
            self.begin.load(json['begin'])
        if json['header']:
            self.header = BandModel(self)
            self.header.load(json['header'])
        if json['detail']:
            self.detail = BandModel(self)
            self.detail.load(json['detail'])
        if json['footer']:
            self.footer = BandModel(self)
            self.footer.load(json['footer'])
        if json['summary']:
            self.summary = BandModel(self)
            self.summary.load(json['summary'])


class ReportView(QtGui.QWidget):

    def __init__(self, parent, model):
        super(ReportView, self).__init__(parent)
        self.model = model
        self.move(10, 10)  # Fix

    #def paintEvent(self, event):

        #painter = QtGui.QPainter(self)


class DesignerModel(object):

    def __init__(self, container, filename=None):
        self.filename = filename
        self.scale = 100
        self.displayScale = 1

        self.report = ReportModel(self, container)

        if self.filename:
            self.report.load(json.load(open(self.filename)))
