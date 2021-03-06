# -*- coding: utf-8 -*-
import os
from PyQt5.QtGui import QFont
from qonda.mvc.observable import ObservableObject, ObservableListProxy
import franq

mm = franq.mm


class CallGenerator:
    """
    This class generates code for calls (usually object creation)
    """
    def __init__(self, name, *params):
        self._name = name
        self._params = list(params)

    def param(self, name, value):
        self._params.append((name, value))

    def param_font(self, font):
        self.param(
            'font', "QFont({}, {}, {}, {})".format(
                repr(font.family()),
                font.pointSize(),
                font.weight(),
                repr(font.italic())
                )
            )

    def param_list(self, name, l, padding):
        self.param(
            name,
            "[\n"
            + ",\n".join(((" " * padding) + x for x in l))
            + "]"
        )

    def generate(self, padding=0):
        return (
            self._name
                + "(\n" + ",\n".join(
                    [" " * padding + pair[0] + "=" + pair[1]
                    for pair in self._params]) + ")")


class ElementModel(ObservableObject):

    def __init__(self):
        super(ElementModel, self).__init__()
        self.parent = None
        self.font = None
        self.top = 0.0
        self.left = 0.0

    def load(self, json):
        self.top = json['top']
        self.left = json['left']
        self.width = json['width']
        self.height = json['height']
        self.pen = json.get('pen')
        self.background = json.get('background')

    def save(self):
        json = {
            'top': self.top,
            'left': self.left,
            'width': self.width,
            'height': self.height,
            'pen': self.pen,
            'background': self.background
            }
        return json

    def active_font(self):
        return self.font if self.font else self.parent.active_font()


class TextModel(ElementModel):

    def __init__(self):
        super().__init__()
        self.width = 20 * mm
        self.height = 4 * mm
        self.expand = False
        self.alignment = 'Left'
        self.richText = False

    def load(self, json):
        super().load(json)
        if json.get('font'):
            self.font = QFont(*json['font'])
        self.alignment = json.get('alignment', 'Left')
        self.richText = json.get('richText', False)

    def save(self):
        json = super().save()
        json['expand'] = self.expand
        json['alignment'] = self.alignment
        json['richText'] = self.richText
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
            ('richText', str(self.richText)),
            *params
            )
        if self.alignment:
            options = (
                {
                    'Left': 'Qt.AlignLeft',
                    'Center': 'Qt.AlignCenter',
                    'Right': 'Qt.AlignRight',
                    'Justify': 'Qt.AlignJustify',
                }[self.alignment])
            gen.param('textOptions', 'QTextOption(' + options + ')')
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

    def generate(self, padding):
        gen = self._generator('Label')
        gen.param('text', repr(self.text))
        return gen.generate(padding)


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

    def generate(self, padding=0):
        gen = self._generator('Field')
        gen.param('attrName', repr(self.attrName))
        gen.param('formatStr', repr(self.format))
        return gen.generate(padding)


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

    def generate(self, padding=0):
        gen = self._generator('Function')
        gen.param('func', self.func)
        return gen.generate(padding)


class LineModel(ElementModel):

    def __init__(self):
        super().__init__()
        self.width = 20.0 * mm
        self.height = 20.0 * mm

    def save(self):
        json = super().save()
        json['type'] = 'line'
        return json

    def generate(self, padding=0):
        gen = CallGenerator('Line',
            ('top', str(self.top)),
            ('left', str(self.left)),
            ('width', str(self.width)),
            ('height', str(self.height)),
            )
        return gen.generate(padding)


class BoxModel(ElementModel):

    def __init__(self):
        super().__init__()
        self.width = 20.0 * mm
        self.height = 20.0 * mm

    def save(self):
        json = super().save()
        json['type'] = 'box'
        return json

    def generate(self, padding=0):
        gen = CallGenerator('Box',
            ('top', str(self.top)),
            ('left', str(self.left)),
            ('width', str(self.width)),
            ('height', str(self.height)),
            )
        return gen.generate(padding)


class ImageModel(ElementModel):

    def __init__(self):
        super().__init__()
        self.width = 20.0 * mm
        self.height = 20.0 * mm
        self.fileName = None

    def load(self, json):
        super().load(json)
        self.fileName = json.get('fileName')

    def save(self):
        json = super().save()
        json['type'] = 'image'
        json['fileName'] = self.fileName
        return json

    def generate(self, padding=0):
        gen = CallGenerator('Image',
            ('top', str(self.top)),
            ('left', str(self.left)),
            ('width', str(self.width)),
            ('height', str(self.height)),
            )
        if self.fileName:
            filename = self.fileName
            if filename[0] in (os.sep, ):
                gen.param('fileName', repr(filename))
            else:
                gen.param('fileName', 'os.path.join(os.path.dirname(__file__), ' + repr(filename) + ')')
        return gen.generate(padding)


element_classes = {
    'label': LabelModel,
    'field': FieldModel,
    'function': FunctionModel,
    'line': LineModel,
    'box': BoxModel,
    'image': ImageModel,
    }


def element_from_json(el_json, parent=None):
    """
    
    """
    class_ = el_json['type']
    e = element_classes[class_]()
    e.load(el_json)
    e.parent = parent
    return e


class BandModel(ObservableObject):

    _notifiables_ = ('description', 'height', 'pen', 'background', 'font',
        'child')

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
        element.parent = self
        self.elements.append(element)

    def remove_element(self, element):
        self.elements.remove(element)
        element.parent = None

    def _add_band(self, band_attr, band):
        setattr(self, band_attr, band)
        band.parent = self

    def add_band(self, band_attr, band):
        if band_attr != 'child':
            raise ValueError('Invalid band_attr')   
        self._add_band(band_attr, band)

    def remove_band(self, band_attr):
        band = getattr(self, band_attr)
        band.parent = None
        setattr(self, band_attr, None)

    def load(self, json):

        self.height = json['height']
        # TODO: Load values if available
        self.pen = None
        self.background = None
        if json.get('font'):
            self.font = QFont(*json['font'])

        if 'elements' in json and json['elements']:
            self.elements = ObservableListProxy(
                [element_from_json(e, self) for e in json['elements']])

        if json.get('child'):
            band = BandModel('Child Band')
            band.load(json['child'])
            self.add_band('child', band)

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

        if self.child:
            json['child'] = self.child.save()

        return json

    def generate(self, padding=0):
        gen = CallGenerator("Band",
            ("height", str(self.height)),
            ("expand", repr(self.expand)))
        #if self.dataSet:
        #    gen.param('dataSet', repr(self.dataSet))
        if self.font:
            gen.param_font(self.font)
        gen.param_list("elements",
                       [el.generate(padding + 4) for el in self.elements],
                       padding)
        if self.child:
            gen.param('child', self.child.generate(padding + 4))
        return gen.generate(padding)


class DetailBandModel(BandModel):

    _notifiables_ = BandModel._notifiables_ + (
        'columnHeader', 'columnFooter', 'detailBegin', 'detailSummary')

    def __init__(self):
        super().__init__('Detail Band')
        self.dataSet = None
        self.columnHeader = None
        self.columnFooter = None
        self.detailBegin = None
        self.detailSummary = None
        self.groups = []

    def add_band(self, band_attr, band):
        if band_attr not in ('child', 'columnHeader', 'columnFooter',
                'detailBegin', 'detailSummary'):
            raise ValueError('Invalid band_attr')
        self._add_band(band_attr, band)

    def load(self, json):
        def group(group_json):
            g = GroupModel()
            g.load(group_json)
            g.parent = self  # Assign here to be able to do comprehension below
            return g

        super().load(json)
        if 'dataSet' in json:
            self.dataSet = json['dataSet']
        if 'groups' in json and json['groups']:
            self.groups = [group(group_json) for group_json in json['groups']]

    def save(self):
        json = super().save()
        if self.groups:
            json['groups'] = [g.save() for g in self.groups]
        return json

    def generate(self, padding=0):
        gen = CallGenerator("DetailBand",
            ("height", str(self.height)),
            ("expand", repr(self.expand)))

        if self.dataSet:
            gen.param('dataSet', repr(self.dataSet))

        if self.font:
            gen.param_font(self.font)
        gen.param_list("elements", 
                       [el.generate(padding + 4)
                        for el in self.elements],
                       padding)
        gen.param_list("groups",
                       [g.generate(padding + 4) 
                       for g in self.groups],
                       padding)
        if self.child:
            gen.param('child', self.child.generate(padding + 4))

        return gen.generate(padding)


class GroupModel(ObservableObject):

    def __init__(self):
        super(GroupModel, self).__init__()
        self.expression = ''
        self.headerBand = BandModel('Group header')
        self.footerBand = BandModel('Group footer')

    def load(self, json):
        self.expression = json['expression']
        self.headerBand = BandModel('Group header')
        self.headerBand.load(json['header'])
        self.footerBand = BandModel('Group footer')
        self.footerBand.load(json['footer'])

    def save(self):
        json = {
            'expression': self.expression,
            'header': self.headerBand.save(),
            'footer': self.footerBand.save()
            }
        return json

    def generate(self, padding=0):
        gen = CallGenerator("DetailGroup",
            ('expression', str(self.expression)))
        gen.param('header', self.headerBand.generate(padding + 4))
        gen.param('footer', self.footerBand.generate(padding + 4))
        return gen.generate(padding)


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

    def generate(self, padding=0):
        gen = CallGenerator("Section",
            ("columns", str(self.columns)),
            ("columnSpace", str(self.columnSpace)))
        gen.param_list("detailBands", 
                       [d.generate(padding + 4)
                        for d in self.detailBands],
                       padding)
        return gen.generate(padding)


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
        self.grid_x_spacing = 2 * mm
        self.grid_y_spacing = 4 * mm

    def active_font(self):
        return self.font

    def add_band(self, band_attr, band):
        if band_attr not in ('begin', 'summary', 'header', 'footer'):
            raise ValueError('Invalid band_attr')
        print(self.margins)
        band.left = self.margins[3]
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
        self.sections.remove(section)
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

        self.grid_x_spacing = json['grid_x_spacing']

    def save(self):
        """
        Convert report structure to serializable form
        """
        json = {
            'name': self.name,
            'title': self.title,
            'dataSet': self.dataSet,
            'paperSize': self.paperSize,
            'margins': self.margins,
            'font': (
                self.font.family(),
                self.font.pointSize(),
                self.font.weight(),
                self.font.italic()),
            'grid_x_spacing': self.grid_x_spacing,
            'grid_y_spacing': self.grid_y_spacing
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
            "import os.path\n"
            "from PyQt5.QtCore import Qt\n"
            "from PyQt5.QtGui import QFont, QTextOption\n"
            "from PyQt5.QtPrintSupport import QPrinter\n"
            "from franq import (\n"
            "   Report, Section, Band, DetailBand, Label, Field, Function, Line, Box, Image\n"
            "   )\n"
            "\n\n")
        s += (
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

        if self.dataSet:
            s += "        self.dataSet= '" + self.dataSet + "'\n"
        if self.begin:
            s += "        self.begin = " + self.begin.generate(12) + "\n"
        if self.header:
            s += "        self.header= " + self.header.generate(12) + "\n"
        s += "        self.sections = [\n"
        for section in self.sections:
            s += section.generate(12) + "\n"
        s += "            ]\n"
        if self.footer:
            s += "        self.footer = " + self.footer.generate(12) + "\n"
        if self.summary:
            s += "        self.begin = " + self.summary.generate(12) + "\n"
        return s

