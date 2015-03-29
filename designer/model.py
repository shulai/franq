# -*- coding: utf-8 -*-

from PyQt4.QtGui import QFont
from qonda.mvc.observable import ObservableObject, ObservableListProxy
import franq

mm = franq.mm


class CallGenerator:

    def __init__(self, name, *params):
        self._name = name
        self._params = list(params)

    def param(self, name, value):
        self._params.append((name, value))

    def param_font(self, font):
        self.param(
            'font', "QFont({}, {}, {}, {})\n".format(
                repr(font.family()),
                font.pointSize(),
                font.weight(),
                repr(self.font.italic())
                )
            )

    def param_list(self, name, l):
        self.param(name, "[" + ", ".join((x for x in l)) + "]")

    def generate(self):
        return (
            self._name
                + "(" + ", ".join(
                    [pair[0] + "=" + pair[1]
                    for pair in self._params]) + ")")


class ElementModel(ObservableObject):

    def __init__(self):
        super(ElementModel, self).__init__()
        self.parent = None
        self.font = None

    def load(self, json):
        self.top = json['top']
        self.left = json['left']
        self.width = json['width']
        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None

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

    def __init__(self):
        super().__init__()
        self.top = 0.0
        self.left = 0.0
        self.width = 20 * mm
        self.height = 4 * mm
        self.expand = False

    def load(self, json):
        super().load(json)
        if json.get('font'):
            self.font = QFont(*json['font'])

    def save(self):
        json = super().save()
        json['expand'] = self.expand
        if self.font:
            json['font'] = (
                self.font.family(),
                self.font.pointSize(),
                self.font.weight(),
                self.font.italic())
        return json

    def _generator(self, name, *params):
        gen = CallGenerator(name,
            ('top', str(self.top)),
            ('left', str(self.left)),
            ('width', str(self.width)),
            ('height', str(self.height)),
            *params
            )
        if self.font:
            gen.param_font(self.font)
        return gen


class LabelModel(TextModel):

    def __init__(self):
        super().__init__()
        self.text = 'Label'

    def load(self, json):
        super().load(json)
        self.text = json['text']

    def save(self):
        json = super().save()
        json['type'] = 'label'
        json['text'] = self.text
        return json

    def generate(self):
        gen = self._generator('Label')
        if self.font:
            gen.param_font(self.font)
        gen.param('text', repr(self.text))
        return gen.generate()


class FieldModel(TextModel):

    def __init__(self):
        super().__init__()
        self.attrName = ''
        self.format = None

    def load(self, json):
        super().load(json)
        self.attrName = json['attrName']
        self.format = json['format']

    def save(self):
        json = super().save()
        json['type'] = 'field'
        json['attrName'] = self.attrName
        json['format'] = self.format
        return json

    def generate(self):
        gen = self._generator('Field')
        if self.font:
            gen.param_font(self.font)
        gen.param('attrName', repr(self.attrName))
        gen.param('formatStr', repr(self.format))
        return gen.generate()


class FunctionModel(TextModel):

    def __init__(self):
        super().__init__()
        self.func = 'lambda o: str(o)'

    def load(self, json):
        super().load(json)
        self.func = json['func']

    def save(self):
        json = super().save()
        json['type'] = 'function'
        json['func'] = self.func
        return json

    def generate(self):
        gen = self._generator('Function')
        if self.font:
            gen.param_font(self.font)
        gen.param('func', repr(self.func))
        return gen.generate()


class LineModel(ElementModel):

    def __init__(self):
        super().__init__()


class BoxModel(ElementModel):

    def __init__(self):
        super().__init__()


class ImageModel(ElementModel):

    def __init__(self):
        super().__init__()
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

    def __init__(self, description):
        super(BandModel, self).__init__()
        self.description = description
        self.parent = None
        self.elements = ObservableListProxy()
        self.height = 20 * mm
        self.expand = False
        self.font = None
        self.child = None

    def active_font(self):
        return self.font if self.font else self.parent.active_font()

    def add_element(self, element):
        self.elements.append(element)
        element.parent = self

    def remove_element(self, element):
        self.elements.remove(element)
        element.parent = None

    def load(self, json):

        def element(el_json):
            class_ = el_json['type']
            e = element_classes[class_]()
            e.load(el_json)
            e.parent = self  # Assign here to be able to do comprehension below
            return e

        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None
        if json.get('font'):
            self.font = QFont(*json['font'])

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
        if self.font:
            json['font'] = (
                self.font.family(),
                self.font.pointSize(),
                self.font.weight(),
                self.font.italic())

        if hasattr(self, 'elements') and self.elements:
            json['elements'] = [e.save() for e in self.elements]
        return json

    def generate(self):
        gen = CallGenerator("Band",
            ("height", str(self.height)),
            ("expand", repr(self.expand)))

        if self.font:
            gen.param_font(self.font)
        gen.param_list("elements", [el.generate() for el in self.elements])
        return gen.generate()


class DetailBandModel(BandModel):

    def __init__(self):
        super().__init__('Detail Band')
        self.dataSet = None
        self.columnHeader = None
        self.columnFooter = None
        self.detailBegin = None
        self.detailSummary = None

    def load(self, json):
        super().load(json)
        if 'dataSet' in json:
            self.dataSet = json['dataSet']


class SectionModel(ObservableObject):

    def __init__(self):
        super().__init__()
        self.parent = None
        self.columns = 1
        self.columnSpace = 0.0
        self.detailBands = ObservableListProxy()
        self.add_band(DetailBandModel())

    def add_band(self, band):
        if not isinstance(band, BandModel):
            raise ValueError("SectionModel.detailBands must contain BandModel")
        self.detailBands.append(band)
        band.parent = self

    def remove_band(self, band):
        self.detailBands.remove(band)
        band.parent = None

    def load(self, json):
        self.columns = json['columns']
        self.columnSpace = json['columnSpace']
        if json['detailBands']:
            self.detailBands = ObservableListProxy()
            for json_detail in json['detailBands']:
                detail = DetailBandModel()
                detail.load(json_detail)
                self.add_band(detail)

    def save(self):
        json = {
            'columns': self.columns,
            'columnSpace': self.columnSpace,
            }
        if self.detailBands:
            json['detailBands'] = [detail.save() for detail in self.detailBands]
        return json

    def active_font(self):
        return self.parent.active_font()


class ReportModel(ObservableObject):

    def __init__(self):
        super(ReportModel, self).__init__()

        # Ok?
        self.name = 'NewReport'
        self.title = 'Report'
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

    def add_band(self, band_attr, band):
        if band_attr not in ('begin', 'summary', 'header', 'footer'):
            raise ValueError('Invand band_attr')
        setattr(self, band_attr, band)
        band.parent = self

    def remove_band(self, band_attr):
        band = getattr(self, band_attr)
        band.parent = None
        setattr(self, band_attr, None)

    def add_section(self, section):
        self.sections.append(section)
        section.parent = self

    def remove_section(self, section):
        self.section.remove(section)
        section.parent = None

    def load(self, json):
        """
        Rebuild report structure from json.load() output
        """
        self.name = json['name']
        self.paperSize = json['paperSize']
        if 'title' in json:
            self.title = json['title']
        if 'dataSet' in json:
            self.dataSet = json['dataSet']
        if 'margins' in json:
            self.margins = json['margins']
        self.font = QFont(*json['font'])

        if 'begin' in json and json['begin']:
            self.add_band('begin', BandModel('Begin Band'))
            self.begin.load(json['begin'])
        if 'header' in json and json['header']:
            self.add_band('header', BandModel('Header Band'))
            self.header.load(json['header'])
        if 'sections' in json and json['sections']:
            for json_section in json['sections']:
                section = SectionModel()
                section.load(json_section)
                self.add_section(section)
        if 'footer' in json and json['footer']:
            self.add_band('footer', BandModel('Footer Band'))
            self.footer.load(json['footer'])
        if 'summary' in json and json['summary']:
            self.add_band('summary', BandModel('Summary Band'))
            self.summary.load(json['summary'])

    def save(self):
        """
        Convert report structure to serializable form
        """
        json = {
            'name': self.name,
            'title': self.title,
            'dataSet': self.dataSet,
            'paperSize': self.paperSize,
            'font': (
                self.font.family(),
                self.font.pointSize(),
                self.font.weight(),
                self.font.italic())
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

    def generate(self):
        """
            Generate Python code
        """
        s = (
            "from PyQt4.QtGui import QPrinter, QFont\n"
            "from franq import *\n"
            "\n"
            "class " + self.name + "(Report):\n"
            "\n"
            "    def setup(self):\n"
            "        super(" + self.name + ", self).setup()\n"
            "        self.title = " + repr(self.title) + "\n")
        try:
            paperSizeConst = ['A4', 'B5', 'Letter', 'Legal', 'Executive',
                'A0', 'A1', 'A2', 'A3', 'A5'][self.paperSize]
        except IndexError:
            paperSizeConst = str(self.paperSize)
        s += (
            "        self.paperSize = QPrinter." + paperSizeConst + "\n")
        paperOrientationConst = ('Portrait', 'LandScape')[self.paperOrientation]
        s += (
            "        self.paperOrientation = QPrinter." + paperOrientationConst
                + "\n")
        s += (
            "        self.margins = " + repr(self.margins) + "\n")
        s += (
            "        self.font = QFont({}, {}, {}, {})\n".format(
                repr(self.font.family()),
                self.font.pointSize(),
                self.font.weight(),
                repr(self.font.italic())))

        if self.begin:
            s += "        self.begin = " + self.begin.generate() + "\n"
        return s
