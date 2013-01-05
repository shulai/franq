# -*- coding: utf-8 -*-

from PyQt4.QtCore import QPointF
from PyQt4.QtGui import QPainter, QPrinter

class BaseElement(object):
    border = None
    background = None
    font = None
    pen = None

    def _renderSetup(self, painter):
        if self.font:
            self.__parent_font = painter.font()
            painter.setFont(self.font)
        if self.pen:
            self.__parent_pen = painter.font()
            painter.setFont(self.font)

    def _renderTearDown(self, painter):
        if self.font:
            painter.setFont(self.__parent_font)
        if self.pen:
            painter.setFont(self.__parent_pen)

    def _renderBorderAndBackground(self, painter, rect):
        if self.background:
            painter.fillRect(rect, self.background)
        if not self.border:
            return
        if len(self.border) == 1:
            border = (self.border,) * 4
        elif len(self.border) != 4:
            raise ValueError('Invalid border')
        else:
            border = self.border
        
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

    print_if_empty = True
    
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

        try:
            data_item = data.next()
        except (AttributeError, StopIteration):
            if self.print_if_empty:
                data_item = None
            else:
                return
               
        painter = QPainter()
        painter.begin(printer)
        self._renderSetup(painter)
        self._renderBorderAndBackground(painter, printer.pageRect())
        self.page = 1

        y = 0.0
        pageHeight = printer.pageRect(QPrinter.Millimeter).height()
        
        if self.title:
            self.title.render(painter, y, data_item)
            printer.newPage()
            self.page += 1

        if self.header:
            self.header.render(painter, y, data_item)

        if self.footer:
            footerHeight = self.footer.renderHeight()
        else:
            footerHeight = 0

        if self.detail is not None and data_item is not None:
            while True:
                detailHeight = self.detail.renderHeight(data_item)
                if y + detailHeight > pageHeight - footerHeight:
                    if self.footer:
                        self.footer.render(painter)
                    printer.newPage()
                    self.page += 1
                    y = 0.0
                    if self.header:
                        headerHeight = self.header.rendeHeight()
                        self.header.render(painter, y, data_item)
                        y += headerHeight
                    
                self.detail.render(painter, y, data_item)
                y += detailHeight
                try:
                    data_item = data.next()
                except StopIteration:
                    break
                    
        if self.summary:
            self.header.render(painter)
        
        painter.end()

class Band(object):

    elements = [] 
    def renderHeight(self, data_item):
        height = self.height
        for element in self.elements:
            elementBottom = element.y + element.renderHeight(data_item) 
            if elementBottom > height:
                heigth = elementBottom
            if self.child:
                heigth += self.child.renderHeigth(data_item)
        return heigth
    
    def render(self, painter, y, data_item=None):
        self._renderSetup(painter)
        self._renderBorderAndBackground(painter, painter.pageRect())
        
        for element in self.elements:
            self.render(painter, y, data_item)

        self._renderTearDown(painter)

class Element(object):
    
    def renderHeight(self, data_item):
        return self.heigth
    
    def render(painter, y, data_item):
        pass # Stub


class TextElement(Element):

    def renderHeight(self, data_item):
        return self.heigth
    
    def _render(self, painter, y, text):
        self._renderSetup(painter)
        self._renderBorderAndBackground(painter, rect)        
        if self.font:
            parent_font = painter.font()
            painter.setFont(self.font)
        rect = painter.boundingRect()
        if self.font:
            painter.setFont(parent_font)
        self._renderTearDown(painter)


class Label(TextElement):
    
    def render(self, painter, y, data_item):

        self._render(self, painter, y, self.text)


class Field(TextElement):
    
    def render(self, painter, y, data_item):
        self._render(self, painter, y, data_item.get(self.fieldName))


class Function(TextElement):
    
    def render(self, painter, y, data_item):
        value = self.func(data_item)
        self._render(self, painter, y, value)


class Image(Element):
    
    def render(painter, y, data_item):
        pass # Stub
