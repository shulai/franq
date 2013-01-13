# -*- coding: utf-8 -*-

from PyQt4 import QtGui

mm = 300 / 25.4

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

        if json['elements']:
            self.elements = [element(e) for e in json['elements']]


class BandView(QtGui.QWidget):
    def __init__(self, parent):
        super(BandView, self).__init__(parent)


class ReportModel(object):
    
    def __init__(self, container):
        
        super(ReportModel, self).__init__(parent)
        # Ok?
        self.title = u'Report'
        self._paperSize = 'A4'
        self._width = 210 * mm
        self._heigth = 297 * mm        
        
        self.begin = None
        self.header = None
        self.detail = None
        self.footer = None
        self.summary = None

        self.view_container = container
        self.view = ReportView(container, self)

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

    def paintEvent(self, event):
        
        painter = QtGui.QPainter(self)
        
        

class DesignerModel(object):

    def __init__(self, container, filename=None):
        self.filename = filename
        self.report = ReportModel(container)
        self.scale = 100
        self.displayScale = 1

        if self.filename:
            self.report.load(json.load(open(self.filename)))            


