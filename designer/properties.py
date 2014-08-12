
from PyQt4.QtCore import Qt, QAbstractTableModel
from PyQt4.QtGui import QColor
import model

GRAY = QColor('lightgray')


class Property(object):

    def __init__(self, propertyName):
        self.propertyName = propertyName


class PropertyTable(QAbstractTableModel):

    def __init__(self, *properties):
        super(PropertyTable, self).__init__()
        self._model = None
        self._properties = properties

    def rowCount(self, parent=None):
        return len(self._properties)

    def columnCount(self, parent=None):
        return 2

    def data(self, index, role=None):
        if role in (Qt.DisplayRole, Qt.EditRole):
            if index.column() == 0:
                return self._properties[index.row()].propertyName
            elif index.column() == 1:
                if self._model is None:
                    return None
                v = getattr(self._model,
                    self._properties[index.row()].propertyName)
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

    def setData(self, index, value, role):
        if role == Qt.EditRole and index.column() == 1:
            setattr(self._model,
                self._properties[index.row()].propertyName, value)

    def setModel(self, model):
        self._model = model
        self.dataChanged.emit(
            self.index(0, 1),
            self.index(len(self._properties) - 1, 1))

property_tables = {

    model.ReportModel: PropertyTable(
        Property('dataSet'),
        Property('paperSize'),
        Property('title')),

    model.SectionModel: PropertyTable(
        Property('columns'),
        Property('columnSpace')),

    model.BandModel: PropertyTable(
        Property('height')),

    model.DetailBandModel: PropertyTable(
        Property('dataSet'),
        Property('height')),

    model.LabelModel: PropertyTable(
        Property('height'),
        Property('left'),
        Property('text'),
        Property('top'),
        Property('width')),

    model.FieldModel: PropertyTable(
        Property('attrName'),
        Property('height'),
        Property('left'),
        Property('top'),
        Property('width')),

    model.FunctionModel: PropertyTable(
        Property('func'),
        Property('height'),
        Property('left'),
        Property('top'),
        Property('width'))

    }