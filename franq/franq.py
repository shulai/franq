# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4.QtCore import QPointF, QRectF, QSizeF
from PyQt4.QtGui import QPainter, QPrinter, QColor, QFont, QTextOption, QPixmap

inch = 300
mm = 300 / 25.4
cm = 300 / 2.54


class BaseElement(object):
    border = None
    background = None
    font = None
    pen = None

    def __init__(self, **kw):
        for key, value in kw.items():
            self.__dict__[key] = value

    def _renderSetup(self, painter):
        if self.font:
            self.__parent_font = painter.font()
            painter.setFont(self.font)
        if self.pen:
            self.__parent_pen = painter.pen()
            painter.setPen(self.pen)

    def _renderTearDown(self, painter):
        if self.font:
            painter.setFont(self.__parent_font)
        if self.pen:
            painter.setPen(self.__parent_pen)

    def _renderBorderAndBackground(self, painter, rect):
        if self.background:
            painter.fillRect(rect, self.background)
        if not self.border:
            return
        try:
            if len(self.border) != 4:
                raise ValueError('Invalid border')
            border = self.border
        except TypeError:
            border = (self.border,) * 4

        pen = painter.pen()
        if border[0]:
            painter.setPen(border[0])
            painter.drawLine(rect.topLeft(), rect.topRight())
        if border[1]:
            painter.setPen(border[1])
            painter.drawLine(rect.topRight(), rect.bottomRight())
        if border[2]:
            painter.setPen(border[2])
            painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        if border[3]:
            painter.setPen(border[3])
            painter.drawLine(rect.topLeft(), rect.bottomLeft())
        painter.setPen(pen)


class Report(BaseElement):

    begin = None
    header = None
    detail = None
    footer = None
    summary = None

    paperSize = QPrinter.A4
    margins = (10 * mm, 10 * mm, 10 * mm, 10 * mm)
    printIfEmpty = False
    headerInFirstPage = True

    def __init__(self, properties=None, begin=None, header=None, detail=None,
            footer=None, summary=None):

        if properties:
            self.properties = properties

        if begin:
            self.begin = begin
        if header:
            self.header = header
        if detail:
            self.detail = detail
        if footer:
            self.footer = footer
        if summary:
            self.summary = summary

        if self.begin is not None and not isinstance(self.begin, Band):
            self.begin = self.begin()
        if self.header is not None and not isinstance(self.header, Band):
            self.header = self.header()
        if self.detail is not None and not isinstance(self.detail, Band):
            self.detail = self.detail()
        if self.footer is not None and not isinstance(self.footer, Band):
            self.footer = self.footer()
        if self.summary is not None and not isinstance(self.summary, Band):
            self.summary = self.summary()

    def render(self, printer, data=None):

        renderer = ReportRenderer(self)
        renderer.render(printer, data)


class ReportRenderer(object):

    def __init__(self, report):
        self._report = report

    def _printerSetup(self, printer):
        rpt = self._report
        printer.setResolution(300)
        printer.setPaperSize(rpt.paperSize)
        printer.setPageMargins(
            rpt.margins[3], rpt.margins[0],
            rpt.margins[1], rpt.margins[2],
            QPrinter.DevicePixel)

    def render(self, printer, data):

        rpt = self._report
        try:
            data = iter(data)
            data_item = data.next()
        except (TypeError, StopIteration):
            if rpt.printIfEmpty:
                data_item = None
            else:
                return

        self._printerSetup(printer)
        painter = QPainter()
        painter.begin(printer)
        rpt._renderSetup(painter)
        rect = printer.pageRect()
        rect.moveTo(0.0, 0.0)
        #hasta aca
        rpt._renderBorderAndBackground(painter, rect)
        self.page = 1

        y = 0.0
        pageHeight = printer.pageRect().height()
        pageWidth = printer.pageRect().width()

        if rpt.header and rpt.headerInFirstPage:
            headerHeight = rpt.header.renderHeight(data_item)
            rect = QRectF(0, y, pageWidth, headerHeight)
            rpt.header.render(painter, rect, data_item)
            y += headerHeight

        if rpt.begin:
            bandHeight = rpt.begin.renderHeight(data_item)
            rect = QRectF(0, y, pageWidth, bandHeight)
            rpt.begin.render(painter, rect, data_item)
            printer.newPage()
            self.page += 1

        if rpt.footer:
            footerHeight = rpt.footer.renderHeight()
        else:
            footerHeight = 0

        if rpt.detail is not None and data_item is not None:
            column = 0
            x = 0
            columnWidth = (pageWidth - rpt.detail.columnSpace *
                (rpt.detail.columns - 1)) / rpt.detail.columns
            while True:
                detailHeight = rpt.detail.renderHeight(data_item)

                if y + detailHeight > pageHeight - footerHeight:
                    column += 1
                    x += columnWidth + rpt.detail.columnSpace
                    if column < rpt.detail.columns:
                        y = headerHeight
                    else:
                        if rpt.footer:
                            y = pageHeight - footerHeight
                            rect = QRectF(0, y, pageWidth, footerHeight)
                            rpt.footer.render(painter, rect)
                        printer.newPage()
                        self.page += 1
                        y = 0.0
                        if rpt.header:
                            headerHeight = rpt.header.renderHeight(data_item)
                            rect = QRectF(0, y, pageWidth, headerHeight)
                            rpt.header.render(painter, rect, data_item)
                            y += headerHeight
                        column = 0
                        x = 0

                rect = QRectF(x, y, columnWidth, detailHeight)
                rpt.detail.render(painter, rect, data_item)
                y += detailHeight
                try:
                    data_item = data.next()
                except StopIteration:
                    break

        if rpt.summary:
            summaryHeight = rpt.summary.renderHeight()
            rect = QRectF(x, y, columnWidth, summaryHeight)
            rpt.summary.render(painter, rect)

        if rpt.footer:
            y = pageHeight - footerHeight
            rect = QRectF(0, y, pageWidth, footerHeight)
            rpt.footer.render(painter, rect)

        painter.end()


class Band(BaseElement):

    height = 20 * mm
    elements = []
    child = None

    def renderHeight(self, data_item=None):
        height = self.height
        for element in self.elements:
            elementBottom = element.top + element.renderHeight(data_item)
            if elementBottom > height:
                height = elementBottom
            if self.child:
                height += self.child.renderHeight(data_item)
        return height

    def render(self, painter, rect, data_item=None):
        band_rect = QRectF(rect.left(), rect.top(), rect.width(), self.height)
        self._renderSetup(painter)
        self._renderBorderAndBackground(painter, band_rect)

        for element in self.elements:
            element.render(painter, band_rect, data_item)

        if self.child:
            child_rect = QRectF(rect.left(), self.height, rect.width(),
                rect.height() - self.height)
            self.child.render(painter, child_rect, data_item)

        self._renderTearDown(painter)


class DetailBand(Band):

    columns = 1
    columnSpace = 0.0
    groups = []


class DetailGroup(object):

    expression = None
    header = None
    footer = None


class Element(BaseElement):

    def renderHeight(self, data_item):
        return self.height

    def render(painter, rect, data_item):
        pass  # Stub


class TextElement(Element):

    textOptions = QTextOption()

    def renderHeight(self, data_item):
        return self.height

    def _render(self, painter, rect, text):
        self._renderSetup(painter)
        self._renderBorderAndBackground(painter, rect)
        if self.font:
            parent_font = painter.font()
            painter.setFont(self.font)
        elementRect = QRectF(QPointF(self.left, self.top) + rect.topLeft(),
            QSizeF(self.width, self.height))
        if self.font:
            painter.setFont(parent_font)
        painter.drawText(elementRect, unicode(text), self.textOptions)
        self._renderTearDown(painter)


class Label(TextElement):

    def render(self, painter, rect, data_item):
        self._render(painter, rect, self.text)


class Field(TextElement):

    format = None

    def render(self, painter, rect, data_item):
        if self.format:
            self._render(self, painter, rect,
                self.format.format(getattr(data_item, self.fieldName,
                    "<Error>")))
        else:
            self._render(painter, rect, getattr(data_item,
                self.fieldName, "<Error>"))


class Function(TextElement):

    def render(self, painter, rect, data_item):
        value = self.func(data_item)
        self._render(painter, rect, value)


class Line(Element):

    def render(painter, rect, data_item):
        pass  # Stub


class Image(Element):

    fileName = None
    pixmap = None

    def render(self, painter, rect, data_item):
        if not self.pixmap:
            if self.fileName:
                self.pixmap = QPixmap(self.pixmap)

            painter.drawPixmap(QPointF(self.left, self.top), self.pixmap,
                self.pixmap.rect())
