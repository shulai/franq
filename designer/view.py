
import sip
from PyQt5 import QtCore, QtGui, QtWidgets, QtPrintSupport
from PyQt5.QtCore import Qt
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


class Grid:

    def __init__(self):
        self.x_spacing = 10 * mm
        self.y_spacing = 10 * mm
        self.snap_to_grid = False

    def draw(self, painter, rect):
        # Draw grid
        painter.setPen(GRID_PEN)
        left, right = rect.left(), rect.right()
        top, bottom = rect.top(), rect.bottom()

        x = left
        while x < right:
            painter.drawLine(QtCore.QLineF(x, top, x, bottom))
            x += self.x_spacing
        y = top
        while y < bottom:
            painter.drawLine(QtCore.QLineF(left, y, right, y))
            y += self.y_spacing

    def snap(self, element):
        element.left = ((element.left + self.x_spacing // 2)
            // self.x_spacing * self.x_spacing)
        element.top = ((element.top + self.y_spacing // 2)
            // self.y_spacing * self.y_spacing)


grid = Grid()


class ElementView(QtWidgets.QGraphicsRectItem):

    def __init__(self, model):
        super(ElementView, self).__init__()
        self.model = model
        self.model.add_callback(self.observe_model)
        self.setFlags(
            QtWidgets.QGraphicsItem.ItemIsSelectable
            | QtWidgets.QGraphicsItem.ItemIsMovable
            | QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setRect(0, 0, self.model.width, self.model.height)
        self._is_resizing = False

    def mousePressEvent(self, event):
        pos = event.pos()
        rect = self.rect()
        self._is_resizing = (
            pos.y() >= rect.bottom() - 1
            or pos.x() >= rect.right() - 1)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            pos = event.scenePos()
            ori = self.pos()
            self.setRect(0, 0, pos.x() - ori.x(), pos.y() - ori.y())
        else:
            super().mouseMoveEvent(event)
            
    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsRectItem.ItemPositionHasChanged:
            # TODO: Restrict to parent
            self.model.left = value.x()
            self.model.top = value.y()

        if grid.snap_to_grid:
            grid.snap(self.model)

        # http://python.6.x6.nabble.com/
        # setapi-and-itemChange-setParentItem-related-bug-td4984797.html
        if isinstance(value, QtWidgets.QGraphicsItem):
            value = sip.cast(value, QtWidgets.QGraphicsItem)
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
        super().paint(painter, option, widget)
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


class LineView(ElementView):

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)


class BoxView(ElementView):

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)

class ImageView(ElementView):

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
            

class BandView(QtWidgets.QGraphicsRectItem):
    def __init__(self, model):
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setBrush(WHITE)

        self.model = model
        self.model.add_callback(self.observe_model)
        self.model.elements.add_callback(self.observe_model_elements)
        self.height = self.model.height
        self.width = 0.0

        self._children = []
        self._band_children = []
        self._element_map = {}
        for element in self.model.elements:
            self._add_child(element, -1)
        if self.model.child:
            child = BandView(model.child)
            self._add_band_child(child)

    def _add_child(self, element, pos):
        class_ = {
            LabelModel: LabelView,
            FieldModel: FieldView,
            FunctionModel: FunctionView,
            LineModel: LineView,
            BoxModel: BoxView,
            ImageModel: ImageView,
            }[type(element)]
        child = class_(element)
        child.setParentItem(self)
        child.setPos(element.left, element.top)
        if pos is None:
            self._children.append(child)
        else:
            self._children.insert(pos, child)
        self._element_map[element] = child
        scene = self.scene()
        if scene:
            self.scene().clearSelection()
            child.setSelected(True)
        return child

    def _remove_child(self, pos):
        child = self._children.pop(pos)
        child.setParentItem(None)
        self.scene().removeItem(child)
        del self._element_map[child.model]
        self.scene().clearSelection()
        self.setSelected(True)

    def _add_band_child(self, child, position=None):
        child.setParentItem(self)

        if position is None:
            if self._band_children:
                child_top = (self._band_children[-1].pos().y()
                    + self._band_children[-1].height)
            else:
                child_top = self.model.height
            child.setPos(0, child_top)
            child.set_width(self.width)
            self._band_children.append(child)
        else:
            if position == 0:
                child_top = self.model.height
            else:
                child_top = (self._band_children[position - 1].pos().y()
                    + self._band_children[position - 1].height)
            child.setPos(0, child_top)
            child.set_width(self.width)
            self._band_children.insert(position, child)
            for other_child in self._band_children[position + 1:]:
                other_child.moveBy(0, child.height)

        self.height += child.height
        self.setRect(0, 0, self.width, self.model.height)
        #try:
        self.parentItem().child_size_updated(self)
        #except AttributeError:
        #    pass
        self._element_map[child.model] = child

        self.scene().clearSelection()
        child.setSelected(True)

        return child

    def _remove_band_child(self, child):
        position = self._band_children.index(child)
        del self._band_children[position]
        child.setParentItem(None)
        self.scene().removeItem(child)
        for other_child in self._band_children[position:]:
            other_child.moveBy(0, -child.height)
        self.height -= child.height
        self.setRect(0, 0, self.width, self.model.height)
        self.parentItem().child_size_updated(self)
        del self._element_map[child.model]
        
        self.scene().clearSelection()
        self.setSelected(True)


    def child_size_updated(self, child):
        # Child (child models) updated height, propagate to parent
        child_top = child.mapRectToParent(child.boundingRect()).bottom()
        i = self._band_children.index(child)
        for child in self.children[i + 1:]:
            child.setPos(0, child_top)
            child_top += child.height
        self.height = child_top
        self.setRect(0, 0, self.width, self.model.height)
        self.parentItem().child_size_updated(self)

    def set_width(self, width):
        self.width = width
        self.setRect(0, 0, self.width, self.model.height)
        for band in self._band_children:
            band.set_width(self.width)

    def paint(self, painter, option, widget):
        super(BandView, self).paint(painter, option, widget)
        grid.draw(painter, self.rect())
        painter.setFont(DESC_FONT)
        painter.setPen(GRAY)
        painter.drawText(0, self.model.height - 10, self.model.description)

    def observe_model(self, model, event_type, _, attrs):
        if event_type == 'update':
            if 'height' in attrs:
                self.height += self.model.height
                self.setRect(0, 0, self.width,
                    self.model.height)
                self.parentItem().child_size_updated(self)
            elif 'child' in attrs and model.child is not None:
                child = BandView(model.child)
                self._add_band_child(child)
        elif event_type == 'before_update':
            if 'height' in attrs:
                # Substract old value before adding new value
                self.height -= self.model.height
            if 'child' in attrs and model.child is not None:
                self._remove_band_child(self._element_map[model.child])

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

    def __init__(self, model):
        super().__init__(model)
        if self.model.columnHeader:
            self.height += self.model.columnHeader.height
        if self.model.columnFooter:
            self.height += self.model.columnFooter.height
        if self.model.detailBegin:
            self.height += self.model.detailBegin.height
        if self.model.detailSummary:
            self.height += self.model.detailSummary.height


class SectionView(QtWidgets.QGraphicsRectItem):

    SECTION_EXTRA_HEIGHT = 10.0 * mm

    def __init__(self, model):
        super(SectionView, self).__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setBrush(WHITE)

        self.model = model

        self.children = []
        self._element_map = {}

        self.height = self.SECTION_EXTRA_HEIGHT
        self.width = 0.0

        for detail_model in self.model.detailBands:
            detail = DetailBandView(detail_model)
            detail.setParentItem(self)
            detail.setPos(0, self.height - self.SECTION_EXTRA_HEIGHT)
            self.children.append(detail)
            self.height += detail.height

        self.update_children_width()
        self.model.add_callback(self.observe_model)
        self.model.detailBands.add_callback(self.observe_model_bands)

    def set_width(self, width):
        self.width = width
        self.setRect(0, 0, self.width, self.height)
        self.update_children_width()

    def update_children_width(self):
        self.children_width = (self.width - self.model.columnSpace *
            (self.model.columns - 1)) / self.model.columns
        for child in self.children:
            child.set_width(self.children_width)

    def observe_model(self, model, event_type, _, attrs):
        if event_type == 'update':
            if 'columns' in attrs or 'columnSpace' in attrs:
                self.update_children_width()

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
        elif event_type == 'before_delitem':
            self.remove_child(self._element_map[bands[event_data]])

    def child_size_updated(self, child):
        # Child (child models) updated height, propagate to parent
        child_top = child.mapRectToParent(child.boundingRect()).bottom()
        i = self.children.index(child)
        for child in self.children[i + 1:]:
            child.setPos(0, child_top)
            child_top += child.height
        self.height = child_top + self.SECTION_EXTRA_HEIGHT
        self.setRect(0, 0, self.width, self.height)
        self.parentItem().child_size_updated(self)

    def add_child(self, child):
        child.setParentItem(self)
        child.setPos(0, self.height - self.SECTION_EXTRA_HEIGHT)
        child.set_width(self.children_width)
        self.children.append(child)
        self.height += child.height
        self.setRect(0, 0, self.width, self.height)
        self.parentItem().child_size_updated(self)
        self._element_map[child.model] = child
        return child

    def remove_child(self, child):
        position = self.children.index(child)
        del self.children[position]
        child.setParentItem(None)
        self.scene().removeItem(child)
        for other_child in self.children[position:]:
            other_child.moveBy(0, -child.height)
        self.height -= child.height
        self.setRect(0, 0, self.width, self.height)
        self.parentItem().child_size_updated(self)
        del self._element_map[child.model]

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        grid.draw(painter, self.rect())
        painter.setFont(DESC_FONT)
        painter.setPen(GRAY)
        painter.drawText(0, self.height - 10, 'Section')


class ReportView(QtWidgets.QGraphicsRectItem):

    def __init__(self, model):
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setBrush(WHITE)
        self.margin_pen = QtGui.QPen(Qt.DashLine)

        self.model = model
        self.model.add_callback(self.observe_model)
        self.model.sections.add_callback(self.observe_sections)
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
            elif 'header' in attrs and model.header is not None:
                view = BandView(model.header)
                position = 1 if model.begin else 0
                self.add_child(view, position)
            elif 'footer' in attrs and model.footer is not None:
                view = BandView(model.footer)
                position = (len(self.children) - 1
                    if self.model.summary else None)
                self.add_child(view, position)
            elif 'summary' in attrs and model.summary is not None:
                view = BandView(model.summary)
                self.add_child(view, None)
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
        elif event_type == 'before_delitem':
            self.remove_child(self._element_map[sections[event_data]])

    def update_size(self):
        printer = QtPrintSupport.QPrinter()
        printer.setPaperSize(self.model.paperSize)
        size = printer.paperSize(QtPrintSupport.QPrinter.Inch) * inch
        self.width = size.width()
        self.height = size.height()
        if self.model.paperOrientation == QtPrintSupport.QPrinter.Landscape:
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
                child_top = (self.children[-1].pos().y()
                    + self.children[-1].height)
            else:
                child_top = self.model.margins[0]
            child.setPos(self.children_left, child_top)
            child.set_width(self.children_width)
            self.children.append(child)
        else:
            if position == 0:
                child_top = self.model.margins[0]
            else:
                child_top = (self.children[position - 1].pos().y()
                    + self.children[position - 1].height)
            child.setPos(self.children_left, child_top)
            child.set_width(self.children_width)
            self.children.insert(position, child)
            for other_child in self.children[position + 1:]:
                other_child.moveBy(0, child.height)

        self._element_map[child.model] = child

    def remove_child(self, child):
        position = self.children.index(child)
        child.parent = None
        del self.children[position]
        child.setParentItem(None)
        self.scene().removeItem(child)
        for other_child in self.children[position:]:
            other_child.moveBy(0, -child.height)
        del self._element_map[child.model]

    def paint(self, painter, option, widget):
        super(ReportView, self).paint(painter, option, widget)

        grid.draw(painter, self.rect())

        # Draw margins
        painter.setPen(self.margin_pen)
        painter.setBrush(TRANSPARENT)
        painter.drawRect(
            QtCore.QRectF(
                QtCore.QPointF(self.model.margins[3], self.model.margins[0]),
                QtCore.QPointF(self.width - self.model.margins[2],
                    self.height - self.model.margins[1])))
