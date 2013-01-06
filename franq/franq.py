# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4.QtCore import QPointF, QRectF, QSizeF
from PyQt4.QtGui import QPainter, QPrinter, QColor, QFont, QTextOption

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
            font = QFont(self.font)
            font.setPointSizeF(self.font.pointSizeF() * 25.4/72.0)
            painter.setFont(font)
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
        painter.setPen(border[0])
        painter.drawLine(rect.topLeft(), rect.topRight())
        painter.setPen(border[1])
        painter.drawLine(rect.topRight(), rect.bottomRight())
        painter.setPen(border[2])
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.setPen(border[3])
        painter.drawLine(rect.topLeft(), rect.bottomLeft())
        painter.setPen(pen)
            
        
class Report(BaseElement):

    title = None
    header = None
    detail = None
    footer = None
    summary = None

    paperSize = QPrinter.A4
    margins = (10, 10, 10, 10)
    printIfEmpty = True
    font = QFont("Helvetica", 10)
    
    def __init__(self, properties=None, title=None, header=None, detail=None, 
            footer=None, summary=None):
                
        if properties:
            self.properties = properties

        if title:
            self.title = title        
        if header:
            self.header = header
        if detail:
            self.detail = detail
        if footer:
            self.footer = footer
        if summary:
            self.summary = summary

        if self.title is not None and not isinstance(self.title, Band):
            self.title = self.title()
        if self.header is not None and not isinstance(self.header, Band):
            self.header = self.header()
        if self.detail is not None and not isinstance(self.detail, Band):
            self.detail = self.detail()
        if self.footer is not None and not isinstance(self.footer, Band):
            self.footer = self.footer()
        if self.summary is not None and not isinstance(self.summary, Band):
            self.summary = self.summary()

    def render(self, printer, data=None):

        data = iter(data)
        try:
            data_item = data.next()
        except (AttributeError, StopIteration):
            if self.printIfEmpty:
                data_item = None
            else:
                return

        printer.setPaperSize(self.paperSize)
        printer.setPageMargins(self.margins[3], self.margins[0], self.margins[1], self.margins[2], QPrinter.Millimeter)
        painter = QPainter()
        painter.begin(printer)
        scale = printer.resolution() * 3937.0 / 100000.0
        painter.scale(scale, scale)
        self._renderSetup(painter)
        rect = printer.pageRect(QPrinter.Millimeter)
        rect.moveTo(0.0, 0.0)
        self._renderBorderAndBackground(painter, rect)
        self.page = 1

        y = 0.0
        pageHeight = printer.pageRect(QPrinter.Millimeter).height()
        pageWidth = printer.pageRect(QPrinter.Millimeter).width()
        
        if self.title:
            bandHeight = self.title.renderHeight(data_item)
            rect = QRectF(0, y, pageWidth, bandHeight)
            self.title.render(painter, rect, data_item)
            printer.newPage()
            self.page += 1

        if self.header:
            bandHeight = self.header.renderHeight(data_item)
            rect = QRectF(0, y, pageWidth, bandHeight)
            self.header.render(painter, rect, data_item)
            y += bandHeight

        if self.footer:
            footerHeight = self.footer.renderHeight()
        else:
            footerHeight = 0

        if self.detail is not None and data_item is not None:
            while True:
                detailHeight = self.detail.renderHeight(data_item)
                if y + detailHeight > pageHeight - footerHeight:
                    if self.footer:
                        rect = QRectF(0, y, width, headerHeight)
                        self.footer.render(painter, rect)
                    printer.newPage()
                    self.page += 1
                    y = 0.0
                    if self.header:
                        headerHeight = self.header.renderHeight(data_item)
                        rect = QRectF(0, y, pageWidth, headerHeight)
                        self.header.render(painter, rect, data_item)
                        y += headerHeight

                rect = QRectF(0, y, pageWidth, detailHeight)
                self.detail.render(painter, rect, data_item)
                y += detailHeight
                try:
                    data_item = data.next()
                except StopIteration:
                    break
                    
        if self.summary:
            self.header.render(painter)
        
        painter.end()

class Band(BaseElement):

    height = 20
    elements = []
    child = None

    def renderHeight(self, data_item):
        height = self.height
        for element in self.elements:
            elementBottom = element.top + element.renderHeight(data_item) 
            if elementBottom > height:
                height = elementBottom
            if self.child:
                height += self.child.renderHeight(data_item)
        return height
    
    def render(self, painter, rect, data_item=None):
        self._renderSetup(painter)
        self._renderBorderAndBackground(painter, rect)
        
        for element in self.elements:
            element.render(painter, rect, data_item)

        self._renderTearDown(painter)

class Element(BaseElement):
    
    def renderHeight(self, data_item):
        return self.height
    
    def render(painter, rect, data_item):
        pass # Stub


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
        elementRect = QRectF(QPointF(self.top, self.left) + rect.topLeft(), QSizeF(self.width, self.height))
        if self.font:
            painter.setFont(parent_font)
        painter.drawText(elementRect, text, self.textOptions)
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


class Image(Element):
    
    def render(painter, rect, data_item):
        pass # Stub
