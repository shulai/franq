# -*- coding: utf-8 -*-
#
# This file is part of the Franq reporting framework
# Franq is (C)2012,2013 Julio César Gázquez
#
# Franq is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# Franq is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Franq; If not, see <http://www.gnu.org/licenses/>.

import sip
sip.setapi("QString", 2)

from PyQt4.QtCore import QPointF, QRectF, QSizeF
from PyQt4.QtGui import QPainter, QPrinter, QTextOption, QPixmap

inch = 300
mm = 300 / 25.4
cm = 300 / 2.54


class BaseElement(object):
    """
    The base class of all report elements.

    Properties
    ----------
    * border: Either a single or a list/tuple of 4
        QPen/QColor/QPenStyle for drawing element border, default None.
    * background: QBrush or QColor for background painting, default None.
    * font: QFont, default None
    * pen: QPen/QColor/QPenStyle, default None, for using in drawings

    Properties like font/pen will use the value of the parent property when
    set to None.

    Events
    ------
    * on_before_print: callable (event handler), default None
    """
    border = None
    background = None
    font = None
    pen = None
    on_before_print = None

    def __init__(self, **kw):
        """
            Any keyword properties will be set as object properties.
        """
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

    def _getBackground(self):
        return self.background

    def renderBorderAndBackground(self, painter, rect):
        if self.background:
            painter.fillRect(rect, self._getBackground())
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

    """
        Base report class.

        Inherits BaseElement

        Properties
        ----------
        * paperSize: QPrinter.PageSize
        * margins: list/tuple of 4 floats, use mm/cm/inch constants
            as multipliers
        * headerInFirstPage: Boolean, default True
        * footerInLastPage: Boolean, default True

        * title: Report title, default None
        * begin: Starting Band, default None
        * header: Band for page headers, default None
        * sections: list of Section objects, default None
        * detail: Shorthand for defining a simple Section with a single
            DetailBand, default None.
        * footer: Band for page footers, default None
        * summary: Final band, default None
    """
    title = None

    begin = None
    header = None
    sections = None
    detail = None
    footer = None
    summary = None

    paperSize = QPrinter.A4
    margins = (10 * mm, 10 * mm, 10 * mm, 10 * mm)
    headerInFirstPage = True
    footerInLastPage = True

    def __init__(self, properties=None, begin=None, header=None,
            detail=None, sections=None, footer=None, summary=None):

        if properties:
            self.properties = properties

        if begin:
            self.begin = begin
        if header:
            self.header = header
        if sections:
            self.sections = sections
        elif detail:
            self.detail = detail
        if footer:
            self.footer = footer
        if summary:
            self.summary = summary

        if self.begin is not None and not isinstance(self.begin, Band):
            self.begin = self.begin()
        if self.header is not None and not isinstance(self.header, Band):
            self.header = self.header()
        if self.sections is None:
            self.sections = [Section(detailBands=[self.detail])]
        for section in self.sections:
            for i, detail in enumerate(section.detailBands):
                if detail is not None and not isinstance(detail, Band):
                    section[i] = detail()
        if self.footer is not None and not isinstance(self.footer, Band):
            self.footer = self.footer()
        if self.summary is not None and not isinstance(self.summary, Band):
            self.summary = self.summary()

    def render(self, printer, *dataSources):

        self.renderer = ReportRenderer(self)
        self.renderer.render(printer, dataSources)
        self.renderer = None


class Section(object):
    """
        A Section is a part of a report with one or more detail bands and
        distinctive layout properties, therefore when rendering a new
        section it will go into a new page.

        Currently sections can have distinct column number and spacing,
        in a future should have distinct page sizes and orientation as well.

        Properties
        ----------
        * columns: int, default 1
        * columnSpace: float, use mm/cm/inch constants
            as multipliers
        * detailBands: a list of DetailBand
    """
    columns = 1
    columnSpace = 0.0
    detailBands = []

    def __init__(self, **kw):
        for key, value in kw.items():
            self.__dict__[key] = value


class DataConsumedError(Exception):
    """Raised when there are detailBands yet to be processed but no
    move datasources available to match them"""
    pass


class ReportRenderer(object):

    def __init__(self, report):
        self._report = report
        self.page = 1
        self._sections = None
        self._detailBands = None
        self.section = None
        self.detailBand = None
        self.dataSource = None
        self.__prev_item = None
        self.__data_item = None

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

    def _printPageHeader(self):
        header = self._report.header
        if header is None:
            return
        height = header.renderHeight(self.__data_item)
        rect = QRectF(0, self.__y, self.__pageWidth, height)
        header.render(self.__painter, rect, self.__data_item)
        self.__y += height

    def _printPageFooter(self):
        footer = self._report.footer
        if footer is None:
            return
        self.__y = self.__pageHeight - self.__footerHeight
        rect = QRectF(0, self.__y, self.__pageWidth, self.__footerHeight)
        footer.render(self.__painter, rect, self.__prev_item)

    def _printBegin(self):
        begin = self._report.begin
        if begin is None:
            return
        height = begin.renderHeight(self.__data_item)
        # Should use columnWidth?
        rect = QRectF(0, self.__y, self.__pageWidth, height)
        begin.render(self.__painter, rect, self.__data_item)
        if begin.forceNewPageAfter:
            self.newPage()
        else:
            self.__y += height

    def _printSummary(self):
        summary = self._report.summary
        if summary is None:
            return
        if summary.forceNewPage:
            self.newPage()
        height = summary.renderHeight()
        rect = QRectF(self.__x, self.__y, self.__columnWidth, height)
        summary.render(self.__painter, rect, self.__prev_item)

    def _printColumnHeader(self):
        header = self.detailBand.columnHeader
        if header is None:
            return
        height = header.renderHeight(self.__data_item)
        rect = QRectF(self.__x, self.__y, self.__columnWidth, height)
        header.render(self.__painter, rect, self.__data_item)
        self.__y += height

    def _printColumnFooter(self):
        footer = self.detailBand.columnFooter
        if footer is None:
            return
        self.__y = self.__pageHeight - (self.__footerHeight +
            self.__columnFooterHeight)
        rect = QRectF(self.__x, self.__y, self.__columnWidth,
            self.__footerHeight)
        footer.render(self.__painter, rect, self.__prev_item)

    def render(self, printer, dataSources):
        rpt = self._report

        # 1
        self._sections = iter(rpt.sections)
        try:
            self.section = self._sections.next()
            self._detailBands = iter(self.section.detailBands)
            self.detailBand = self._detailBands.next()
        except StopIteration:
            self.detailBand = None

        # 2
        self._dataSources = iter(dataSources)
        try:
            self.dataSource = iter(self._dataSources.next())
            self.__data_item = self.dataSource.next()
        except StopIteration:
            if self.detailBand:  # If detail-less report, continue
                return

        # 3
        self.__printer = printer
        self._printerSetup()
        self.__painter = QPainter()
        self.__painter.begin(printer)

        # 4
        rpt.renderSetup(self.__painter)
        rect = printer.pageRect()
        rect.moveTo(0.0, 0.0)

        # 5
        rpt.renderBorderAndBackground(self.__painter, rect)
        self.page = 1

        self.__y = 0.0
        self.__pageHeight = printer.pageRect().height()
        self.__pageWidth = printer.pageRect().width()

        # 6
        if rpt.headerInFirstPage:
            self._printPageHeader()
        self._printBegin()

        # I'm assuming footer height _cannot_ vary according the detail item
        # If I don't, I'll be never sure when I must print the footer
        # just by looking at a single detail item
        if rpt.footer is not None:
            self.__footerHeight = rpt.footer.renderHeight()
        else:
            self.__footerHeight = 0

        if self.detailBand and self.__data_item is not None:

            # 7
            self.__col = 0
            self.__x = 0
            self.__columnWidth = (self.__pageWidth - self.section.columnSpace *
                (self.section.columns - 1)) / self.section.columns

            detailTop = self.__y
            self._printColumnHeader()

            if self.detailBand.columnFooter is not None:
                self.__columnFooterHeight = (self.detailBand.columnFooter.
                    renderHeight())
            else:
                self.__columnFooterHeight = 0

            detailBottom = self.__pageHeight - (self.__footerHeight +
                self.__columnFooterHeight)

            groupingLevel = 0
            # Print first round of group headers
            for group in self.detailBand.groups:
                groupingLevel += 1
                group.value = group.expression(self.__data_item)
                if group.header:
                    groupHeaderHeight = group.header.renderHeight()
                    rect = QRectF(self.__x, self.__y,
                        self.__columnWidth, groupHeaderHeight)
                    group.header.render(self.__painter, rect, self.__data_item)
                    self.__y += groupHeaderHeight

            # Detail main loop
            while True:

                # Print group footers before detail row if required
                # then group headers
                for group in self.detailBand.groups[::-1]:
                    new_group_value = group.expression(self.__data_item)
                    if new_group_value == group.value:
                        break
                    groupingLevel -= 1
                    group.value = new_group_value
                    if group.footer:
                        groupFooterHeight = group.footer.renderHeight()
                        rect = QRectF(self.__x, self.__y,
                            self.__columnWidth, groupFooterHeight)
                        group.footer.render(self.__painter, rect,
                            self.__data_item)
                        self.__y += groupFooterHeight

                for group in self.detailBand.groups[groupingLevel:]:
                    groupingLevel += 1
                    if group.header:
                        groupHeaderHeight = group.header.renderHeight(
                            self.__data_item)
                        rect = QRectF(self.__x, self.__y,
                            self.__columnWidth, groupHeaderHeight)
                        group.header.render(self.__painter, rect,
                            self.__data_item)
                        self.__y += groupHeaderHeight

                detailHeight = self.detailBand.renderHeight(self.__data_item)

                # If there is no space left, start new column/page
                # Print footers and headers
                if self.__y + detailHeight > detailBottom:
                    self._printColumnFooter()
                    self.__col += 1
                    if self.__col < self.section.columns:
                        self.__y = detailTop
                        self.__x += self.__columnWidth + self.section.columnSpace
                    else:
                        self._printPageFooter()
                        self.newPage()
                        self._printPageHeader()
                        self.__col = 0
                        self.__x = 0
                    self._printColumnHeader()

                rect = QRectF(self.__x, self.__y,
                    self.__columnWidth, detailHeight)
                self.detailBand.render(self.__painter, rect, self.__data_item)
                self.__y += detailHeight
                try:
                    self.__prev_item = self.__data_item
                    self.__data_item = self.dataSource.next()
                except StopIteration:
                    # No more data for this DetailBand
                    # Close groups, proceed to the next DetailBand
                    for group in self.detailBand.groups[::-1]:
                        groupingLevel -= 1
                        if group.footer:
                            groupFooterHeight = group.footer.renderHeight()
                            rect = QRectF(self.__x, self.__y,
                                self.__columnWidth, groupFooterHeight)
                            group.footer.render(self.__painter, rect,
                                self.__data_item)
                            self.__y += groupFooterHeight

                    self._printColumnFooter()
                    # TODO: Print detailBand.detailSummary
                    try:
                        self.detailBand = self._detailBands.next()
                        self._printColumnHeader()
                        # TODO: Start new column/page if forceNewColumn is set
                        # TODO: Print detailBand.detailBegin
                    except StopIteration:
                        # No more detail bands in this section, proceed to
                        # the next section
                        self._printPageFooter()
                        try:
                            self.section = self._sections.next()
                            self._detailBands = iter(self.section.detailBands)
                            self.detailBand = self._detailBands.next()
                            self.newPage()
                            self._printPageHeader()
                            self.__col = 0
                            self.__x = 0
                            self.__columnWidth = (self.__pageWidth - self.section.columnSpace *
                                (self.section.columns - 1)) / self.section.columns
                            self._printColumnHeader()
                        except StopIteration:
                            break
                    try:
                        self.dataSource = iter(self._dataSources.next())
                        self.__data_item = self.dataSource.next()
                    except StopIteration:
                        raise DataConsumedError()

            self._printColumnFooter()
        self._printSummary()
        if rpt.footerInLastPage:
            self._printPageFooter()

        self.__painter.end()


class Band(BaseElement):
    """
        A Band of the report.

        Inherits BaseElement.

        Properties
        ----------
        height: float, use mm/cm/inch constants as multipliers.
        elements: list of Element objects.
        child: A Band to be printed after this band, being separate allows
            for example page breaks.
        forceNewPage: boolean. Start a new page before start printing the band,
            default False.
        forceNewPageAfter: boolean, Start a new page before start printing the
            band, default False.

    """
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

        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        band_rect = QRectF(rect.left(), rect.top(), rect.width(), self.height)
        self.renderSetup(painter)
        self.renderBorderAndBackground(painter, band_rect)

        for element in self.elements:
            element.render(painter, band_rect, data_item)

        if self.child:
            child_rect = QRectF(rect.left(), rect.top() + self.height,
                rect.width(), rect.height() - self.height)
            self.child.render(painter, child_rect, data_item)

        self.renderTearDown(painter)


class DetailBand(Band):
    """
        A Band associated with a detail dataset.

        Inherits Band.

        Properties
        ----------
        * groups: List of DetailGroup, default empty list.
        * columnHeader: Header Band for the column, useful for detail titles,
            default None.
        * columnFooter: Footer Band for the column, useful for detail summaries,
            default None.
        * detailBegin: Band preceding the detail, default None.
        * detailSummary: Band after the detail, default None.

    """
    groups = []
    forceNewColumn = False
    columnHeader = None
    columnFooter = None
    detailBegin = None
    detailSummary = None


class DetailGroup(object):
    """
        Grouping of a detailband dataset items

        Properties
        ----------
        * expression: callable, usually a lambda. Default None.
        * header: Group header band, useful for titles, default None.
        * footer: Group footer band, useful for summaries, default None.
    """
    expression = None
    header = None
    footer = None

    def __init__(self, expression=None, header=None, footer=None):
        if expression:
            self.expression = expression
        if header:
            self.header = header
        if footer:
            self.footer = footer
        self.value = None


class Element(BaseElement):
    """
        Base of Band Elements, like labels, values or drawings

        Inherits BaseElement.

        Properties
        ----------
        * left: float, position into the band use mm/cm/inch constants
            as multipliers, default 0.
        * top: float, position into the band use mm/cm/inch constants
            as multipliers, default 0.
        * width: float, element width, use mm/cm/inch constants as multipliers,
            default 0.
        * height: float, element width, use mm/cm/inch constants as multipliers,
            default 0.
    """
    left = 0.0
    top = 0.0
    width = 100 * mm
    height = 5 * mm

    def renderHeight(self, data_item):
        return self.height

    def render(painter, rect, data_item):
        pass  # Stub


class TextElement(Element):
    """
        Base of text-rendering Elements.

        Inherits Element.

        Properties
        ----------
        * textOptions: QTextOption, mainly used for text alignment.
    """
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
    """
        Static (unless you cheat using events ;-) text element.

        Inherits TextElement.

        Properties
        ----------
        * text: unicode, text value of the Label.
    """
    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        self._render(painter, rect, self.text)


class Field(TextElement):
    """
        Dynamic, dataset item attribute based text element.
        Useful when dataset items are entity objects.

        Inherits TextElement.

        Properties
        ----------
        * fieldName: str, attribute name.
        * formatStr: unicode, optional Python standard formatting string,
            default None.
    """
    formatStr = None

    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        if self.formatStr:
            self._render(painter, rect,
                self.formatStr.format(getattr(data_item, self.fieldName,
                    "<Error>")))
        else:
            v = getattr(data_item, self.fieldName, "<Error>")
            if v is None:
                v = ''
            self._render(painter, rect, v)


class Function(TextElement):
    """
        Dynamic Function based text element.

        Inherits TextElement.

        Properties
        ----------
        * func: callable, usually a lambda or a report method, receives the
            data item as parameter, returns unicode value to render.
    """
    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        value = self.func(data_item)
        self._render(painter, rect, value)


class Line(Element):
    """
        Line drawing element.

        Inherits Element.
    """
    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        self.renderSetup(painter)
        painter.drawLine(self.left, self.top, self.left + self.width,
            self.top + self.height)
        self.renderTearDown(painter)


class Box(Element):
    """
        Box drawing element. (Currently stub)

        Inherits Element.
    """
    def render(painter, rect, data_item):
        pass  # Stub


class Image(Element):
    """
        Image rendering element.

        Inherits Element.

        Properties
        ----------
        * pixmap: QPixmap of the image, default None.
        * fileName: name of the image file, used if pixmap is None,
            default None.
    """
    fileName = None
    pixmap = None

    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        if not self.pixmap:
            if self.fileName:
                self.pixmap = QPixmap(self.pixmap)

            painter.drawPixmap(QPointF(self.left, self.top), self.pixmap,
                self.pixmap.rect())
