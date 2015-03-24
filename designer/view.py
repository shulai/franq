
import sip
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import Qt
from franq import inch, mm
from model import (LabelModel, FieldModel, FunctionModel, LineModel, BoxModel,
    ImageModel, BandModel, DetailBandModel)

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
        font = QtGui.QFont(self.model.active_font())
        font.setPointSize(font.pointSize() * inch // 72)
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

        self._children = []
        self._element_map = {}
        for element in self.model.elements:
            self._add_child(element, -1)

    def _add_child(self, element, pos):
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
        if pos is None:
            self._children.append(child)
        else:
            self._children.insert(pos, child)
        self._element_map[element] = child
        print('add_child')
        for m, v in zip(self.model.elements, self._children):
            print(m, v.model)
        return child

    def _remove_child(self, pos):
        child = self._children.pop(pos)
        child.setParentItem(None)
        self.scene().removeItem(child)
        del self._element_map[child.model]

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

    def observe_model_elements(self, elements, event_type, _, event_data):
        if event_type == 'append':
            self._add_child(elements[-1], None)
        elif event_type == 'insert':
            i = event_data
            self._add_child(elements[i], i)
        elif event_type == 'delitem':
            index = event_data
            self._remove_child(index)


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

    def observe_model_bands(self, bands, event_type, _, event_data):
        if event_type == 'append':
            band = bands[-1]
            if isinstance(band, DetailBandModel):
                child = DetailBandView(band)
            elif isinstance(band, BandModel):
                child = BandView(band)
            else:
                print("Error! SectionModel.detailBands can't contain this")
            self.add_child(child)
            self._element_map[child.model] = child

    def parent_size_updated(self):
        # Parent changed width, propagate to children
        self.bounds_updated()
        for child in self.children:
            child.parent_size_updated()

    def child_size_updated(self, child):
        # Child (child models) updated height, propagate to parent
        self.bounds_updated()
        self.parentItem().child_size_updated(self)

    def add_child(self, child):
        child.setParentItem(self)
        child.setPos(0, self.height)
        self.children.append(child)
        self.height += child.height
        return child

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
        self.model.add_callback(self.observe_model)
        self.children = []
        self._element_map = {}
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

    def observe_model(self, model, event_type, _, attrs):
        if event_type == 'update':
            if 'begin' in attrs and model.begin is not None:
                view = BandView(model.begin)
                self.add_child(view, 0)
                self._element_map[model.begin] = view
            elif 'header' in attrs and model.header is not None:
                view = BandView(model.header)
                position = 1 if model.begin else 0
                self.add_child(view, position)
                self._element_map[model.header] = view
            elif 'footer' in attrs and model.footer is not None:
                view = BandView(model.footer)
                position = (len(self.children) - 1
                    if self.model.summary else None)
                self.add_child(view, position)
                self._element_map[model.footer] = view
            elif 'summary' in attrs and model.summary is not None:
                view = BandView(model.summary)
                self.add_child(view, None)
                self._element_map[model.summary] = view
        elif event_type == 'before_update':
            if 'begin' in attrs and model.begin is not None:
                self.remove_child(self._element_map[model.begin])
            elif 'header' in attrs and model.header is not None:
                self.remove_child(self._element_map[model.header])
            elif 'footer' in attrs and model.footer is not None:
                self.remove_child(self._element_map[model.footer])
            elif 'summary' in attrs and model.summary is not None:
                self.remove_child(self._element_map[model.summary])

    def observe_sections(self, sections, event_type, _, event_data):
        if event_type == 'append':
            section = sections[-1]
            view = SectionView(section)
            position = len(self.children)
            if self.model.summary:
                position -= 1
            if self.model.footer:
                position -= 1
            self.add_child(view, position)
            self._element_map[section] = view

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
        child_top = self.model.margins[0]
        for child in self.children:
            child.setPos(self.children_left, child_top)
            child_top += child.height

    #def model_size_updated(self):
        #self.update_size()
        #for child in self.children:
            #child.setWidth(self.children_width)

    def child_size_updated(self, child):
        child_top = child.mapRectToParent(child.boundingRect()).bottom()
        i = self.children.index(child)
        for child in self.children[i + 1:]:
            child.setPos(self.children_left, child_top)
            child_top += child.height

    def add_child(self, child, position=None):
        child.setParentItem(self)
        if position is None:
            if self.children:
                child_top = self.children[-1].mapRectToParent(
                    self.children[-1].boundingRect()).bottom()
            else:
                child_top = self.model.margins[0]
            child.setPos(self.children_left, child_top)
            child.setRect(0, 0, self.children_width, child.height)
            self.children.append(child)
        else:
            if position == 0:
                child_top = self.model.margins[0]
            else:
                child_top = self.children[position - 1].mapRectToParent(
                self.children[position - 1].boundingRect()).bottom()
            child.setPos(self.children_left, child_top)
            child.setRect(0, 0, self.children_width, child.height)
            self.children.insert(position, child)
            for other_child in self.children[position + 1:]:
                other_child.moveBy(0, child.height)

    def remove_child(self, child):
        position = self.children.index(child)
        child.parent = None
        del self.children[position]
        child.setParentItem(None)
        self.scene().removeItem(child)
        for other_child in self.children[position:]:
            other_child.moveBy(0, -child.height)

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
