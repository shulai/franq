# -*- coding: utf-8 -*-

from PyQt4.QtGui import QFont, QColor
from qonda.mvc.observable import ObservableObject, ObservableListProxy
import franq

mm = franq.mm


def load_font(f):
    return QFont(f['family'], f['size'], f['weight'], f['italic'])


class ElementModel(ObservableObject):

    def __init__(self, parent):
        super(ElementModel, self).__init__()
        self.parent = parent
        self.font = None

    def load(self, json):
        self.top = json['top']
        self.left = json['left']
        self.width = json['width']
        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None
        if 'font' in json:
            self.font = load_font(json['font'])

    def save(self):
        json = {
            'top': self.top,
            'left': self.left,
            'width': self.width,
            'height': self.height
            }
        return json

    def active_font(self):
        return self.font if self.font else self.parent.active_font()


class TextModel(ElementModel):

    def __init__(self, parent):
        super(TextModel, self).__init__(parent)
        self.top = 0.0
        self.left = 0.0
        self.width = 20 * mm
        self.height = 4 * mm
        self.expand = False

    def save(self):
        json = super().save()
        json['expand'] = self.expand
        json['font'] = self.font


class LabelModel(TextModel):

    def __init__(self, parent):
        super().__init__(parent)
        self.text = 'Label'

    def load(self, json):
        super(LabelModel, self).load(json)
        self.text = json['text']

    def save(self):
        json = super().save()
        json['type'] = 'label'
        json['text'] = self.text
        return json


class FieldModel(TextModel):

    def __init__(self, parent):
        super().__init__(parent)
        self.attrName = ''
        self.format = None

    def load(self, json):
        super(FieldModel, self).load(json)
        self.attrName = json['attrName']
        self.format = json['format']

    def save(self):
        json = super(FieldModel, self).save()
        json['type'] = 'field'
        json['attrName'] = self.attrName
        json['format'] = self.format
        return json


class FunctionModel(TextModel):

    def __init__(self, parent):
        super().__init__(parent)
        self.func = 'lambda o: str(o)'

    def load(self, json):
        super().load(json)
        self.func = json['func']

    def save(self):
        json = super().save()
        json['type'] = 'function'
        json['func'] = self.func
        return json


class LineModel(ElementModel):

    def __init__(self):
        super(LineModel, self).__init__()


class BoxModel(ElementModel):

    def __init__(self):
        super(BoxModel, self).__init__()


class ImageModel(ElementModel):

    def __init__(self):
        super(ImageModel, self).__init__()
        self.fileName = None

    def load(self, json):
        super().load(json)
        self.fileName = json['filename']

    def save(self):
        json = super().save()
        json['type'] = 'image'
        json['fileName'] = self.fileName
        return json


element_classes = {
    'label': LabelModel,
    'field': FieldModel,
    'function': FunctionModel,
    'line': LineModel,
    'box': BoxModel,
    'image': ImageModel,
    }


class BandModel(ObservableObject):

    _notifiables_ = ('description', 'height', 'pen', 'background', 'font')

    def __init__(self, description, parent):
        super(BandModel, self).__init__()
        self.description = description
        self.parent = parent
        self.elements = ObservableListProxy()
        self.height = 20 * mm
        self.expand = False
        self.font = None

    def active_font(self):
        return self.font if self.font else self.parent.active_font()

    def load(self, json):

        def element(el_json):
            class_ = el_json['type']
            e = element_classes[class_](self)
            e.load(el_json)
            return e

        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None
        self.font = None

        if 'elements' in json and json['elements']:
            self.elements = ObservableListProxy(
                [element(e) for e in json['elements']])

    def save(self):
        # TODO
        json = {
            'expand': self.expand,
            'font': self.font,
            'height': self.height
            }
        if hasattr(self, 'elements') and self.elements:
            json['elements'] = [e.save() for e in self.elements]
        return json


class DetailBandModel(BandModel):

    def __init__(self, parent):
        super(DetailBandModel, self).__init__('Detail Band', parent)
        self.dataSet = None

    def load(self, json):
        super(DetailBandModel, self).load(json)
        if 'dataSet' in json:
            self.dataSet = json['dataSet']


class SectionModel(ObservableObject):

    def __init__(self, parent):
        super(SectionModel, self).__init__()
        self.parent = parent
        self.columns = 1
        self.columnSpace = 0.0
        self.detailBands = ObservableListProxy([DetailBandModel(self)])

    def load(self, json):
        self.columns = json['columns']
        self.columnSpace = json['columnSpace']
        if json['detailBands']:
            self.detailBands = ObservableListProxy()
            for json_detail in json['detailBands']:
                detail = DetailBandModel(self)
                detail.load(json_detail)
                self.detailBands.append(detail)

    def save(self):
        json = {
            'columns': self.columns,
            'columnSpace': self.columnSpace,
            }
        if self.detailBands:
            json['detailBands'] = [detail.save() for detail in self.detailBands]
        return json


class ReportModel(ObservableObject):

    def __init__(self):
        super(ReportModel, self).__init__()

        # Ok?
        self.title = u'Report'
        self.paperSize = franq.Report.paperSize
        self.paperOrientation = franq.Report.paperOrientation
        self.font = QFont('Helvetica', 12)
        self.font.setStyleHint(QFont.SansSerif, QFont.ForceOutline)

        self.margins = franq.Report.margins
        self.begin = None
        self.header = None
        self.detail = None
        self.footer = None
        self.summary = None
        self.sections = ObservableListProxy()
        self.dataSet = None

    def active_font(self):
        return self.font

    def load(self, json):
        """
        Rebuild report structure from json.load() output
        """
        self.paperSize = json['paperSize']
        if 'title' in json:
            self.title = json['title']
        if 'dataSet' in json:
            self.dataSet = json['dataSet']
        if 'margins' in json:
            self.margins = json['margins']

        if 'begin' in json and json['begin']:
            self.begin = BandModel('Begin Band', self)
            self.begin.load(json['begin'])
        if 'header' in json and json['header']:
            self.header = BandModel('Header Band', self)
            self.header.load(json['header'])
        if 'sections' in json and json['sections']:
            for json_section in json['sections']:
                section = SectionModel(self)
                section.load(json_section)
                self.sections.append(section)
        if 'footer' in json and json['footer']:
            self.footer = BandModel('Footer Band', self)
            self.footer.load(json['footer'])
        if 'summary' in json and json['summary']:
            self.summary = BandModel('Summary Band', self)
            self.summary.load(json['summary'])

    def save(self):
        """
        Convert report structure to serializable form
        """
        json = {
            'title': self.title,
            'dataSet': self.dataSet,
            'paperSize': self.paperSize
            }
        if self.begin:
            json['begin'] = self.begin.save()
        if self.header:
            json['header'] = self.header.save()
        if self.sections:
            json['sections'] = [section.save() for section in self.sections]
        if self.footer:
            json['footer'] = self.footer.save()
        if self.summary:
            json['summary'] = self.summary.save()
        return json
