
from PyQt4.QtCore import Qt, QAbstractTableModel
from PyQt4 import QtGui
from qonda.mvc.adapters import ValueListAdapter
from qonda.mvc.delegates import ComboBoxDelegate
import model
from dialogs import MarginsDialog, FontDialog

GRAY = QtGui.QColor('lightgray')

unit_factor = 300 / 25.4


class PropertyDialogDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, dialogClass, parent=None):
        super().__init__(parent)
        self.DialogClass = dialogClass
        self._dialog = None

    def createEditor(self, parent, options, index):
        if not self._dialog:
            self._dialog = self.DialogClass()
        self._dialog.setModel(index.data(Qt.EditRole))
        self._dialog.exec_()
        index.model().setData(index, self._dialog.model())
        self._editor = QtGui.QLabel("", parent)
        self.closeEditor.emit(self._editor, QtGui.QAbstractItemDelegate.NoHint)
        return self._editor

    def setEditorData(self, editor, index):
        pass

    def setModelData(self, editor, model, index):
        pass


class Property:

    def __init__(self, propertyName):
        self.propertyName = propertyName

    def propertyTransform(self, value, role=Qt.DisplayRole):
        return value

    def propertyInverseTransform(self, value):
        return value

    delegate = None


class BooleanProperty(Property):

    _values = ['False', 'True']

    def __init__(self, propertyName):
        super().__init__(propertyName)
        self.delegate = ComboBoxDelegate(
            model=ValueListAdapter(self._values),
            allowEmpty=False)

    def propertyTransform(self, v, role=Qt.DisplayRole):
        return str(bool(v))

    def propertyInverseTransform(self, v):
        return v == 'True'


class DimensionProperty(Property):

    def propertyTransform(self, v, role=Qt.DisplayRole):
        return round(v / unit_factor, 2)

    def propertyInverseTransform(self, v):
        return round(v * unit_factor, 2)


class PaperSizeProperty(Property):

    _paperSizes = ['A4', 'B5', 'Letter', 'Legal', 'Executive',
        'A0', 'A1', 'A2', 'A3', 'A5']

    def __init__(self, propertyName):
        super().__init__(propertyName)
        self.delegate = ComboBoxDelegate(
            model=ValueListAdapter(sorted(self._paperSizes)),
            allowEmpty=False)

    def propertyTransform(self, v, role=Qt.DisplayRole):
        if role == Qt.EditRole:
            return v
        else:
            return self._paperSizes[v]

    def propertyInverseTransform(self, v):
        print('pit', v)
        return self._paperSizes.index(v)


class MarginsProperty(Property):

    def __init__(self, propertyName):
        super().__init__(propertyName)
        self.delegate = PropertyDialogDelegate(MarginsDialog)

    def propertyTransform(self, v, role=Qt.DisplayRole):
        if role == Qt.EditRole:
            return v
        else:
            return '({}, {}, {}, {})'.format(
                *[round(x / unit_factor, 2) for x in v])

    def propertyInverseTransform(self, v):
        return v


class FontProperty(Property):

    def __init__(self, propertyName):
        super().__init__(propertyName)
        self.delegate = PropertyDialogDelegate(FontDialog)

    def propertyTransform(self, v, role=Qt.DisplayRole):
        if role == Qt.EditRole:
            return v
        else:
            return '{}{} {}pt{}'.format(
                v.family(),
                ' bold' if v.bold() else '',
                v.pointSize() * 24 // 100,
                ' italic' if v.italic() else '') if v else "(Parent's)"


class PropertyTable(QAbstractTableModel):

    def __init__(self, *properties):
        super(PropertyTable, self).__init__()
        self._model = None
        self._properties = properties

    def rowCount(self, parent=None):
        return len(self._properties)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == 0:
                return self._properties[index.row()].propertyName
            elif index.column() == 1:
                if self._model is None:
                    return None
                prop = self._properties[index.row()]
                v = prop.propertyTransform(
                    self._model.getPropertyValue(prop.propertyName), role)
                if v is None:
                    v = ''
                return v
        elif role == Qt.BackgroundRole and index.column() == 0:
            return GRAY
        else:
            return None

    def flags(self, index):
        if index.column() == 0:
            return Qt.NoItemFlags
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole and index.column() == 1:
            prop = self._properties[index.row()]
            value = prop.propertyInverseTransform(value)
            self._model.setPropertyValue(prop.propertyName, value)
        return True

    def setModel(self, model):
        if self._model:
            self._model.remove_callback(self.observe_model)
        self._model = model
        if self._model:
            self._model.add_callback(self.observe_model)
        self.dataChanged.emit(
            self.index(0, 1),
            self.index(len(self._properties) - 1, 1))

    def delegate(self, row):
        return self._properties[row].delegate

    def observe_model(self, sender, event_type, _, attrs):
        if event_type != 'update':
            return
        try:
            propertyNames = [p.propertyName for p in self._properties]
            index = self.createIndex(propertyNames.index(attrs[0]), 1)
            self.dataChanged.emit(index, index)
        except (KeyError, ValueError):
            pass


property_tables = {

    model.ReportModel: PropertyTable(
        Property('dataSet'),
        FontProperty('font'),
        MarginsProperty('margins'),
        PaperSizeProperty('paperSize'),
        Property('title')),

    model.SectionModel: PropertyTable(
        Property('columns'),
        Property('columnSpace')),

    model.BandModel: PropertyTable(
        BooleanProperty('expand'),
        FontProperty('font'),
        DimensionProperty('height')),

    model.DetailBandModel: PropertyTable(
        Property('dataSet'),
        BooleanProperty('expand'),
        FontProperty('font'),
        DimensionProperty('height')),

    model.LabelModel: PropertyTable(
        BooleanProperty('expand'),
        FontProperty('font'),
        DimensionProperty('height'),
        DimensionProperty('left'),
        Property('text'),
        DimensionProperty('top'),
        DimensionProperty('width')),

    model.FieldModel: PropertyTable(
        Property('attrName'),
        BooleanProperty('expand'),
        FontProperty('font'),
        DimensionProperty('height'),
        DimensionProperty('left'),
        DimensionProperty('top'),
        DimensionProperty('width')),

    model.FunctionModel: PropertyTable(
        BooleanProperty('expand'),
        FontProperty('font'),
        Property('func'),
        DimensionProperty('height'),
        DimensionProperty('left'),
        DimensionProperty('top'),
        DimensionProperty('width'))
    }
