# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4.QtCore import QPointF, QRectF, QSizeF
from PyQt4.QtGui import QPainter, QPrinter, QTextOption, QPixmap

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

    def renderSetup(self, painter):
        if self.font:
            self.__parent_font = painter.font()
            painter.setFont(self.font)
        if self.pen:
            self.__parent_pen = painter.pen()
            painter.setPen(self.pen)

    def renderTearDown(self, painter):
        if self.font:
            painter.setFont(self.__parent_font)
        if self.pen:
            painter.setPen(self.__parent_pen)

    def renderBorderAndBackground(self, painter, rect):
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

    title = None

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

        self.renderer = ReportRenderer(self)
        self.renderer.render(printer, data)
        self.renderer = None


class ReportRenderer(object):

    def __init__(self, report):
        self._report = report
        self.page = 1

    def _printerSetup(self):
        rpt = self._report
        self.__printer.setResolution(300)
        self.__printer.setPaperSize(rpt.paperSize)
        self.__printer.setPageMargins(
            rpt.margins[3], rpt.margins[0],
            rpt.margins[1], rpt.margins[2],
            QPrinter.DevicePixel)

    def newPage(self):
        self.__printer.newPage()
        self.page += 1
        self.__y = 0.0

    def _printHeader(self):
        rpt = self._report
        if rpt.header is None:
            return
        height = rpt.header.renderHeight(self.__data_item)
        rect = QRectF(0, self.__y, self.__pageWidth, height)
        rpt.header.render(self.__painter, rect, self.__data_item)
        self.__y += height

    def _printFooter(self):
        rpt = self._report
        if rpt.footer is None:
            return
        self.__y = self.__pageHeight - self.__footerHeight
        rect = QRectF(0, self.__y, self.__pageWidth, self.__footerHeight)
        rpt.footer.render(self.__painter, rect, self.__prev_item)

    def _printBegin(self):
        rpt = self._report
        if rpt.begin is None:
            return
        height = rpt.begin.renderHeight(self.__data_item)
        rect = QRectF(0, self.__y, self.__pageWidth, height)
        rpt.begin.render(self.__painter, rect, self.__data_item)
        if rpt.begin.forceNewPageAfter:
            self.newPage()

    def _printSummary(self):
        rpt = self._report
        if rpt.summary is None:
            return
        summaryHeight = rpt.summary.renderHeight()
        rect = QRectF(self.__x, self.__y, self.__columnWidth, summaryHeight)
        rpt.summary.render(self.__painter, rect, self.__prev_item)

    def render(self, printer, data):

        rpt = self._report
        try:
            data = iter(data)
            self.__prev_item = None
            self.__data_item = data.next()
        except (TypeError, StopIteration):
            if rpt.printIfEmpty:
                self.__data_item = None
            else:
                return

        self.__printer = printer
        self._printerSetup()
        self.__painter = QPainter()
        self.__painter.begin(printer)

        rpt.renderSetup(self.__painter)
        rect = printer.pageRect()
        rect.moveTo(0.0, 0.0)

        rpt.renderBorderAndBackground(self.__painter, rect)
        self.page = 1
        self.lastPage = False

        self.__y = 0.0
        self.__pageHeight = printer.pageRect().height()
        self.__pageWidth = printer.pageRect().width()

        if rpt.headerInFirstPage:
            self._printHeader()
        self._printBegin()

        detailTop = self.__y
        # I'm assuming footer height _cannot_ vary according the detail item
        # If I don't, I'll be never sure when I must print the footer
        # just by looking at a single detail item
        if rpt.footer is not None:
            self.__footerHeight = rpt.footer.renderHeight()
        else:
            self.__footerHeight = 0

        detailBottom = self.__pageHeight - self.__footerHeight

        if rpt.detail is not None and self.__data_item is not None:
            self.__col = 0
            self.__x = 0
            self.__columnWidth = (self.__pageWidth - rpt.detail.columnSpace *
                (rpt.detail.columns - 1)) / rpt.detail.columns
            while True:
                detailHeight = rpt.detail.renderHeight(self.__data_item)

                if self.__y + detailHeight > detailBottom:
                    self.__col += 1
                    if self.__col < rpt.detail.columns:
                        self.__y = detailTop
                        self.__x += self.__columnWidth + rpt.detail.columnSpace
                    else:
                        self._printFooter()
                        self.newPage()
                        self._printHeader()
                        self.__col = 0
                        self.__x = 0

                rect = QRectF(self.__x, self.__y,
                    self.__columnWidth, detailHeight)
                rpt.detail.render(self.__painter, rect, self.__data_item)
                self.__y += detailHeight
                try:
                    self.__prev_item = self.__data_item
                    self.__data_item = data.next()
                except StopIteration:
                    break

        self._printSummary()
        self._printFooter()

        self.__painter.end()


class Band(BaseElement):

    height = 20 * mm
    elements = []
    child = None
    forceNewPage = False
    forceNewPageAfter = False

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
        self.renderSetup(painter)
        self.renderBorderAndBackground(painter, band_rect)

        for element in self.elements:
            element.render(painter, band_rect, data_item)

        if self.child:
            child_rect = QRectF(rect.left(), self.height, rect.width(),
                rect.height() - self.height)
            self.child.render(painter, child_rect, data_item)

        self.renderTearDown(painter)


class DetailBand(Band):

    columns = 1
    columnSpace = 0.0
    groups = []
    forceNewColumn = False
    columnHeader = None
    columnFooter = None


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
        self.renderSetup(painter)
        self.renderBorderAndBackground(painter, rect)
        if self.font:
            parent_font = painter.font()
            painter.setFont(self.font)
        elementRect = QRectF(QPointF(self.left, self.top) + rect.topLeft(),
            QSizeF(self.width, self.height))
        if self.font:
            painter.setFont(parent_font)
        painter.drawText(elementRect, unicode(text), self.textOptions)
        self.renderTearDown(painter)


class Label(TextElement):

    def render(self, painter, rect, data_item):
        self._render(painter, rect, self.text)


class Field(TextElement):

    formatStr = None

    def render(self, painter, rect, data_item):
        if self.format:
            self._render(self, painter, rect,
                self.formatStr.format(getattr(data_item, self.fieldName,
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
