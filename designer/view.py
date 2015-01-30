
import sip
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from franq import inch, mm
from model import (LabelModel, FieldModel, FunctionModel, LineModel, BoxModel,
    ImageModel)

WHITE = QtGui.QColor('white')
BLACK = QtGui.QColor('black')
BLUE = QtGui.QColor('blue')
GRAY = QtGui.QColor('gray')
TRANSPARENT = QtGui.QColor(0, 0, 0, 0)
DESC_FONT = QtGui.QFont('Helvetica', 6 * 300 / 72)
GRID_PEN = QtGui.QPen(Qt.DotLine)
GRID_PEN.setColor(BLUE)

grid_size = 10.0 * mm  # FIXME: Configurable grid


def draw_grid(painter, rect):
    # Draw grid
    painter.setPen(GRID_PEN)
    left, right = rect.left(), rect.right()
    top, bottom = rect.top(), rect.bottom()

    x = left
    while x < right:
        painter.drawLine(QtCore.QLineF(x, top, x, bottom))
        x += grid_size
    y = top
    while y < bottom:
        painter.drawLine(QtCore.QLineF(left, y, right, y))
        y += grid_size


class ElementView(QtGui.QGraphicsRectItem):

    def __init__(self, model):
        super(ElementView, self).__init__()
        self.model = model
        self.model.add_callback(self.observe_model)
        self.setFlags(
            QtGui.QGraphicsItem.ItemIsSelectable
            | QtGui.QGraphicsItem.ItemIsMovable
            | QtGui.QGraphicsItem.ItemSendsGeometryChanges)
        self.setRect(0, 0, self.model.width, self.model.height)

    def itemChange(self, change, value):
        if change == QtGui.QGraphicsRectItem.ItemPositionHasChanged:
            # TODO: Restrict to parent
            self.model.left = value.x()
            self.model.top = value.y()
        # http://python.6.x6.nabble.com/
        # setapi-and-itemChange-setParentItem-related-bug-td4984797.html
        if isinstance(value, QtGui.QGraphicsItem):
            value = sip.cast(value, QtGui.QGraphicsItem)
        return value

    def observe_model(self, sender, event_type, _, attrs):
        if event_type == 'update':
            attrs = set(attrs)
            if attrs & {'top', 'left'}:
                self.setPos(self.model.left, self.model.top)
            elif attrs & {'height', 'width'}:
                self.setRect(0, 0, self.model.width, self.model.height)
            else:
                self.update()


class TextView(ElementView):

    def paint(self, painter, option, widget):
        super(TextView, self).paint(painter, option, widget)

        font = self.model.active_font()
        painter.setFont(font)
        painter.drawText(self.rect(),
            self.text_placeholder())


class LabelView(TextView):

    def text_placeholder(self):
        return self.model.text


class FieldView(TextView):

    def text_placeholder(self):
        return self.model.attrName


class FunctionView(TextView):

    def text_placeholder(self):
        return self.model.func


#class LineView(QtGui.QWidget):
    #pass


#class BoxView(QtGui.QWidget):
    #pass

#class ImageView(QtGui.QWidget):
    #pass


class BandView(QtGui.QGraphicsRectItem):
    def __init__(self, model):
        super(BandView, self).__init__()
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setBrush(WHITE)

        self.model = model
        self.model.add_callback(self.observe_model)
        self.model.elements.add_callback(self.observe_model_elements)
        self.height = self.model.height

        self.children = []
        for element in self.model.elements:
            self.add_child(element, -1)

    def add_child(self, element, pos):
        class_ = {
            LabelModel: LabelView,
            FieldModel: FieldView,
            FunctionModel: FunctionView,
            LineModel: None,
            BoxModel: None,
            ImageModel: None,
            }[type(element)]
        child = class_(element)
        child.setParentItem(self)
        child.setPos(element.left, element.top)
        self.children.insert(pos, child)

    def setWidth(self, width):
        self.width = width
        self.setRect(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        super(BandView, self).paint(painter, option, widget)

        draw_grid(painter, self.rect())

        painter.setFont(DESC_FONT)
        painter.setPen(GRAY)
        painter.drawText(0, self.height - 10, self.model.description)

    def observe_model(self, sender, event_type, _, attrs):
        if event_type == 'update':
            if 'height' in attrs:
                self.height = self.model.height
                self.setRect(0, 0, self.boundingRect().width(),
                    self.height)
                self.parentItem().child_size_updated(self)

    def observe_model_elements(self, sender, event_type, _, event_data):
        if event_type == 'append':
            self.add_child(sender[-1], -1)
        elif event_type == 'insert':
            self.add_child(sender[-1], event_data)
        elif event_type == 'remove':
            self.children.pop(event_data)


class DetailBandView(BandView):

    pass


class SectionView(QtGui.QGraphicsRectItem):

    def __init__(self, model):
        super(SectionView, self).__init__()
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setBrush(WHITE)

        self.model = model

        self.children = []
        if hasattr(self.model, 'detailBands'):
            self.height = 0.0
            for detail_model in self.model.detailBands:
                detail = DetailBandView(detail_model)
                detail.setParentItem(self)
                detail.setPos(0, self.height)
                self.children.append(detail)
                self.height += detail.height

        # FIXME: Repeating bounds_updated

    def parent_size_updated(self):
        # Parent changed width, propagate to children
        self.bounds_updated()
        for child in self.children:
            child.parent_size_updated()

    def child_size_updated(self, child):
        # Child (child models) updated height, propagate to parent
        self.bounds_updated()
        self.parentItem().child_size_updated(self)

    def paint(self, painter, option, widget):
        super(SectionView, self).paint(painter, option, widget)
        draw_grid(painter, self.rect())


class ReportView(QtGui.QGraphicsRectItem):

    def __init__(self, model):
        super(ReportView, self).__init__()
        self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setBrush(WHITE)
        self.margin_pen = QtGui.QPen(Qt.DashLine)

        self.model = model
        self.children = []
        self.update_size()

        if self.model.header:
            self.add_child(BandView(self.model.header))
        if self.model.begin:
            self.add_child(BandView(self.model.begin))
        if hasattr(self.model, 'sections'):
            for section in self.model.sections:
                self.add_child(SectionView(section))
        if self.model.summary:
            self.add_child(BandView(self.model.summary))
        if self.model.footer:
            self.add_child(BandView(self.model.footer))

    def update_size(self):
        printer = QtGui.QPrinter()
        printer.setPaperSize(self.model.paperSize)
        size = printer.paperSize(QtGui.QPrinter.Inch) * inch
        self.width = size.width()
        self.height = size.height()
        if self.model.paperOrientation == QtGui.QPrinter.Landscape:
            self.width, self.height = self.height, self.width
        self.setRect(0, 0, self.width, self.height)
        self.update_margins()

    def update_margins(self):
        self.children_left = self.model.margins[3]
        self.children_width = (self.width - self.model.margins[1]
            - self.model.margins[3])
        self.child_top = self.model.margins[0]
        for child in self.children:
            child.setPos(self.children_left, self.child_top)
            self.child_top += child.height

    #def model_size_updated(self):
        #self.update_size()
        #for child in self.children:
            #child.setWidth(self.children_width)

    def child_size_updated(self, child):
        self.child_top = child.y() + child.boundingRect().height()
        i = self.children.index(child)
        for child in self.children[i + 1:]:
            child.setPos(self.children_left, self.child_top)
            self.child_top += child.height

    def add_child(self, child):
        child.setParentItem(self)
        child.setPos(self.children_left, self.child_top)
        child.setRect(0, 0, self.children_width, child.height)
        self.children.append(child)
        self.child_top += child.height

    def paint(self, painter, option, widget):
        super(ReportView, self).paint(painter, option, widget)

        draw_grid(painter, self.rect())

        # Draw margins
        painter.setPen(self.margin_pen)
        painter.setBrush(TRANSPARENT)
        painter.drawRect(
            QtCore.QRectF(
                QtCore.QPointF(self.model.margins[3], self.model.margins[0]),
                QtCore.QPointF(self.width - self.model.margins[2],
                    self.height - self.model.margins[1])))
