# -*- coding: utf-8 -*-

from PyQt4.QtGui import QPainter, QPrinter

class Report(object):

    title = None
    header = None
    detail = None
    footer = None
    summary = None

    properties = {}
    
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

        if isinstance(self.title, Band):
            self.title = self.title()
        if isinstance(self.header, Band):
            self.header = self.header()
        if isinstance(self.detail, Band):
            self.detail = self.detail()
        if isinstance(self.footer, Band):
            self.footer = self.footer()
        if isinstance(self.summary, Band):
            self.summary = self.summary()

    def render(self, printer, data=None):

        try:
            data_item = data.next()
        except (AttributeError, StopIteration):
            if self.properties['print_if_empty']:
                data_item = None
            else:
                return
               
        painter = QPainter()
        painter.begin(printer)
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
        # TODO: Set background and border
        for element in self.elements:
            self.render(painter, y, data_item)


class Element(object):
    
    def renderHeight(self, data_item):
        return self.heigth
    
    def render(painter, y, data_item):
        pass # Stub


class TextElement(Element):

    def renderHeight(self, data_item):
        return self.heigth
    
    def _renderText(self, painter, y, text):
        pass  # Stub


class Label(TextElement):
    
    def render(self, painter, y, data_item):
        Element.render(self, y, data_item)
        self._renderText(self, painter, y, self.text)


class Field(TextElement):
    
    def render(self, painter, y, data_item):
        Element.render(self, y, data_item)
        self._renderText(self, painter, y, data_item.get(self.fieldName))


class Function(TextElement):
    
    def render(self, painter, y, data_item):
        Element.render(self, y, data_item)
        value = self.func(data_item)
        self._renderText(self, painter, y, value)


class Image(Element):
    
    def render(painter, y, data_item):
        pass # Stub
