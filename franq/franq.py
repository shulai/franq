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

if PYQT_VERSION == 5:
    from PyQt5.QtCore import QPointF, QRectF, QSizeF, Qt
    from PyQt5.QtGui import (QPainter, QTextOption, QPixmap, QColor,
        QTextDocument, QFontMetricsF)
    from PyQt5.QtPrintSupport import QPrinter
else:
    from PyQt4.QtCore import QPointF, QRectF, QSizeF, Qt
    from PyQt4.QtGui import (QPainter, QPrinter, QTextOption, QPixmap, QColor,
        QTextDocument, QFontMetricsF)

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
        * paperSize: QPrinter.PaperSize
        * paperOrientation: QPrinter.Orientation
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
    paperOrientation = QPrinter.Portrait
    margins = (10 * mm, 10 * mm, 10 * mm, 10 * mm)
    headerInFirstPage = True
    footerInLastPage = True
    dataSet = None

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

        self.setup()

        if self.begin is not None and not isinstance(self.begin, Band):
            self.begin = self.begin()
        if self.header is not None and not isinstance(self.header, Band):
            self.header = self.header()
        if self.sections is None:
            if self.detail is None:
                self.sections = []
            else:
                self.sections = [Section(detailBands=[self.detail])]
        for section in self.sections:
            for i, detail in enumerate(section.detailBands):
                if detail is not None and not isinstance(detail, Band):
                    section[i] = detail()
        if self.footer is not None and not isinstance(self.footer, Band):
            self.footer = self.footer()
        if self.summary is not None and not isinstance(self.summary, Band):
            self.summary = self.summary()

    def setup(self):
        pass

    def render(self, printer, **dataSources):

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


class DataSourceExausted(Exception):

    pass


class DataSource:

    def __init__(self, dataSet):
        self._iterator = iter(dataSet)
        self._prev = None
        self._item = None
        try:
            self.nextDataItem()
        except DataSourceExausted:
            pass

    def getDataItem(self):
        return self._item

    def getPrevDataItem(self):
        return self._prev

    def nextDataItem(self):
        self._prev = self._item
        try:
            self._item = next(self._iterator)
        except StopIteration:
            self._item = None
            raise DataSourceExausted()
        return self._item


class ReportRenderer(object):

    def __init__(self, report):
        self._report = report
        self.page = 1

    def _printerSetup(self):
        rpt = self._report
        self.__printer.setResolution(300)
        self.__printer.setPaperSize(rpt.paperSize)
        self.__printer.setOrientation(rpt.paperOrientation)
        self.__printer.setPageMargins(
            rpt.margins[3], rpt.margins[0],
            rpt.margins[1], rpt.margins[2],
            QPrinter.DevicePixel)

    def _newPage(self, dataItem):
        if (self._report.footer
                and self.__y < self.__pageHeight - self.__footerHeight):
            self._printPageFooter(dataItem)

        self.__printer.newPage()
        self.page += 1
        self.__y = 0.0
        self._printPageHeader(dataItem)

    def _renderBandPageWide(self, band, dataItem, checkEnd=True):
        if band.forceNewPage:
            self._newPage(dataItem)

        # Band own's dataset overrides provided by the caller
        # for detail bands it gets the same items as provided by the renderer!
        try:
            ds = self._dataSources[band.dataSet]
            dataItem = ds.getDataItem()
        except KeyError:
            pass
        height = band.renderHeight(self.__painter, dataItem)
        if checkEnd and self.__y + height > self.__detailBottom:
            self._newPage(dataItem)
        rect = QRectF(0.0, self.__y, self.__pageWidth, height)
        if band.render(self.__painter, rect, dataItem):
            self.__y += height
        if band.forceNewPageAfter:
            self._newPage(dataItem)

    def _renderBandColumnWide(self, band, dataItem, checkEnd=True):
        try:
            ds = self._dataSources[band.dataSet]
            dataItem = ds.getDataItem()
        except KeyError:
            pass

        if band.forceNewPage:
            self._newPage(dataItem)
        else:
            # FIXME: Only works if band's dataSet attribute is defined
            try:
                if band.startNewPage and ds.getPrevDataItem():
                    self._newPage(dataItem)
            except UnboundLocalError:  # Ignore if no datasource
                print('UnboundLocalError')
                pass

        height = band.renderHeight(self.__painter, dataItem)
        if checkEnd and self.__y + height > self.__detailBottom:
            self._continueInNewColumn(dataItem)
        rect = QRectF(self.__x, self.__y, self.__columnWidth, height)
        if band.render(self.__painter, rect, dataItem):
            self.__y += height
        if band.forceNewPageAfter:
            self._newPage(dataItem)

    def _printPageHeader(self, dataItem):
        if self._report.header is not None:
            self._renderBandPageWide(self._report.header, dataItem, False)

    def _printPageFooter(self, dataItem):
        if self._report.footer is not None:
            self.__y = self.__pageHeight - self.__footerHeight
            self._renderBandPageWide(self._report.footer, dataItem, False)

    def _printBegin(self, dataItem):
        if self._report.begin is not None:
            self._renderBandPageWide(self._report.begin, dataItem, False)

    def _printSummary(self, dataItem):
        if self._report.summary is not None:
            self._renderBandPageWide(self._report.summary, dataItem, True)

    def _printColumnHeader(self, detailBand, dataItem):
        try:
            if detailBand.columnHeader is not None:

                # Check for new column here, if done in _renderBandColumnWide
                # the header will print twice
                try:
                    ds = self._dataSources[detailBand.columnHeader.dataSet]
                    dataItem = ds.getDataItem()
                except KeyError:
                    pass

                height = detailBand.columnHeader.renderHeight(self.__painter,
                    dataItem)
                if self.__y + height > self.__detailBottom:
                    # recursively calls _printColumnHeader and do the
                    # actual band rendering falling by the else clause
                    self._continueInNewColumn(dataItem)
                else:
                    # Not at the end, render normally
                    self._renderBandColumnWide(detailBand.columnHeader,
                        dataItem, False)
        except AttributeError:  # detailBand is a regular band
            pass

    def _printColumnFooter(self, detailBand, dataItem):
        try:
            if detailBand.columnFooter is not None:
                self.__y = self.__detailBottom
                self._renderBandColumnWide(detailBand.columnFooter, dataItem,
                    False)
        except AttributeError:  # detailBand is a regular band
            pass

    def _printDetailBegin(self, detailBand, dataItem):
        if detailBand.begin:
            self._renderBandColumnWide(detailBand.begin, dataItem, True)

    def _printDetailSummary(self, detailBand, dataItem):
        if detailBand.summary:
            self._renderBandColumnWide(detailBand.summary, dataItem, True)

    def _continueInNewColumn(self, dataItem):
        self._printColumnFooter(self._currentDetailBand, dataItem)
        self.__col += 1
        if self.__col < self._currentSection.columns:
            self.__y = self.__detailTop
            self.__x += self.__columnWidth + self._currentSection.columnSpace
        else:
            self._newPage(dataItem)
            self.__col = 0
            self.__x = 0
        self._printColumnHeader(self._currentDetailBand, dataItem)

    def _renderDetailBand(self, detailBand, dataSet=None):
        """
            Render a dataset into a detail band.
            If a dataset is not provided, it is determined using either
            the band's dataSet attribute or the report dataSet attribute
            The dataset attribute is provided for subdetails.
        """
        self._currentDetailBand = detailBand
        try:
            detailFooterHeight = detailBand.columnFooter.renderHeight(
                self.__painter)
        except AttributeError:
            detailFooterHeight = 0
        self.__detailBottom = self.__pageHeight - (self.__footerHeight +
                detailFooterHeight)

        if dataSet is not None:
            ds = DataSource(dataSet)
        elif detailBand.dataSet is not None:
            ds = self._dataSources[detailBand.dataSet]
        else:
            ds = self._dataSources[self._report.dataSet]

        try:
            groupingLevel = 0
            dataItem = ds.getDataItem()
            if not dataItem and not detailBand.renderIfEmpty:
                return
            self._printDetailBegin(detailBand, dataItem)
            self._printColumnHeader(detailBand, dataItem)

            if dataItem:
                # Print first round of group headers
                for group in detailBand.groups:
                    groupingLevel += 1
                    group.value = group.expression(dataItem)
                    if group.header:
                        self._renderBandColumnWide(group.header, dataItem, True)

                while True:

                    # Print headers
                    # TODO: Can I use this to print the first round?
                    for group in detailBand.groups[groupingLevel:]:
                        groupingLevel += 1
                        group.value = group.expression(dataItem)
                        if group.header:
                            self._renderBandColumnWide(group.header, dataItem,
                                True)

                    self._renderBandColumnWide(detailBand, dataItem, True)

                    for subdetail in detailBand.subdetails:
                        if isinstance(subdetail, DetailBand):
                            self._renderDetailBand(subdetail,
                                getattr(dataItem, subdetail.dataSet))
                        else:
                            self._currentDetailBand = subdetail
                            self.__detailBottom = (
                                self.__pageHeight - self.__footerHeight)
                            self._renderBandColumnWide(subdetail, dataItem,
                                True)

                    dataItem = ds.nextDataItem()

                    for group in detailBand.groups[::-1]:
                        new_group_value = group.expression(dataItem)
                        if new_group_value == group.value:
                            break
                        groupingLevel -= 1
                        group.value = new_group_value
                        if group.footer:
                            self._renderBandColumnWide(group.footer,
                                ds.getPrevDataItem(), True)
                        if group.on_new_group is not None:
                            group.on_new_group()

        except DataSourceExausted:
            pass  # Out of loop
        # Print last round of group footers, only if datasource not empty
        if ds.getPrevDataItem():
            for group in detailBand.groups[::-1]:
                groupingLevel -= 1
                # group.value = new_group_value
                if group.footer:
                    self._renderBandColumnWide(group.footer,
                        ds.getPrevDataItem(), True)

        self._printDetailSummary(detailBand, ds.getPrevDataItem())

    def _renderSection(self, section):
        self._currentSection = section
        # TODO: Setup section here
        self.__columnWidth = (self.__pageWidth - section.columnSpace *
            (section.columns - 1)) / section.columns

        for band in section.detailBands:
            if isinstance(band, DetailBand):
                self._renderDetailBand(band)
            else:
                try:
                    ds = self._dataSources[self._report.dataSet]
                    dataItem = ds.getDataItem()
                except (KeyError, DataSourceExausted):
                    dataItem = None
                self._currentDetailBand = band
                self.__detailBottom = self.__pageHeight - self.__footerHeight
                self._renderBandColumnWide(band, dataItem, True)

    def render(self, printer, dataSources):
        rpt = self._report

        # 3
        self.__printer = printer
        self._printerSetup()
        self.__painter = QPainter()
        self.__painter.begin(printer)

        # 4
        rpt.renderSetup(self.__painter)
        rect = printer.pageRect()
        rect.moveTo(0.0, 0.0)

        if rpt.on_before_print is not None:
            rpt.on_before_print()

        # 5
        rpt.renderBorderAndBackground(self.__painter, rect)
        self.page = 1

        self.__y = 0.0
        self.__col = 0
        self.__x = 0

        self.__pageHeight = printer.pageRect().height()
        self.__pageWidth = printer.pageRect().width()

        self._dataSources = {k: DataSource(ds)
            for k, ds in dataSources.iteritems()}
        try:
            ds = self._dataSources[rpt.dataSet]
            dataItem = ds.getDataItem()
        except (KeyError, DataSourceExausted):
            dataItem = None

        # 6
        if rpt.headerInFirstPage:
            self._printPageHeader(dataItem)
        self.__detailTop = self.__y
        self._printBegin(dataItem)

        # I'm assuming footer height _cannot_ vary according the detail item
        # If I don't, I'll be never sure when I must print the footer
        # just by looking at a single detail item
        if rpt.footer is not None:
            self.__footerHeight = rpt.footer.renderHeight(self.__painter)
        else:
            self.__footerHeight = 0

        for section in rpt.sections:
            self._renderSection(section)

        self._printSummary(dataItem)
        if rpt.footerInLastPage:
            self._printPageFooter(dataItem)

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
        dataSet: The dataset for its elements, overrides dataSet defined at
            Report level.
        forceNewPage: boolean. Start a new page before start printing the band,
            default False.
        forceNewPageAfter: boolean, Start a new page before start printing the
            band, default False.
        startNewPage: boolean. Start a new page before start printing the band,
            when no previous data in the DataSet.
            default False.
        expand: boolean, if False honors height attribute, if True expands
            height to accomodate elements if necessary
    """
    height = 20 * mm
    elements = None
    child = None
    forceNewPage = False
    forceNewPageAfter = False
    startNewPage = False
    expand = False
    dataSet = None
    renderBand = True

    def __init__(self, **kw):
        super().__init__(**kw)
        if self.elements is None:
            self.elements = []

    def _bandRenderHeight(self, painter, data_item=None):
        height = self.height
        if self.expand:
            self.renderSetup(painter)  # Set font
            for element in self.elements:
                elementBottom = element.top + element.renderHeight(painter,
                    data_item)
                if elementBottom > height:
                    height = elementBottom
        return height

    def renderHeight(self, painter, data_item=None):
        height = self._bandRenderHeight(painter, data_item)
        if self.child:
            height += self.child.renderHeight(painter, data_item)
        return height

    def render(self, painter, rect, data_item=None):

        self.renderBand = True
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        if not self.renderBand:
            return False

        if self.expand:
            band_rect = QRectF(rect.left(), rect.top(),
                 rect.width(), self._bandRenderHeight(painter, data_item))
        else:
            band_rect = QRectF(rect.left(), rect.top(),
                 rect.width(), self.height)
        self.renderSetup(painter)
        self.renderBorderAndBackground(painter, band_rect)

        for element in self.elements:
            element.render(painter, band_rect, data_item)

        if self.child:
            child_rect = QRectF(rect.left(), rect.top() + self.height,
                rect.width(), rect.height() - self.height)
            self.child.render(painter, child_rect, data_item)

        self.renderTearDown(painter)
        return True


class DetailBand(Band):
    """
        A Band associated with a detail dataset.

        Inherits Band.

        Properties
        ----------
        * groups: List of DetailGroup, default empty list.
        * subdetails: List of DetailBand, default empty list.
        * columnHeader: Header Band for the detail/column,
            default None.
        * columnFooter: Footer Band for the detail/column,
            default None.
        * begin: Band preceding the detail, default None.
        * summary: Band after the detail, default None.

    """
    groups = []
    subdetails = []
    forceNewColumn = False
    columnHeader = None
    columnFooter = None
    begin = None
    summary = None
    renderIfEmpty = False


class DetailGroup(object):
    """
        Grouping of a detailband dataset items

        Properties
        ----------
        * expression: callable, usually a lambda. Default None.
        * header: Group header band, useful for titles, default None.
        * footer: Group footer band, useful for summaries, default None.

        Events
        ------
        * on_new_group: callable (event handler), default None
    """
    expression = None
    header = None
    footer = None
    on_new_group = None

    def __init__(self, expression=None, header=None, footer=None,
            on_new_group=None):
        if expression:
            self.expression = expression
        if header:
            self.header = header
        if footer:
            self.footer = footer
        if on_new_group:
            self.on_new_group = on_new_group
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

    def renderHeight(self, painter, data_item):
        return self.height

    def render(painter, rect, data_item):
        pass  # Stub


class TextElement(Element):
    """
        Base of text-rendering Elements.

        Inherits Element.

        Properties
        ----------
        * expand: Increase effective height if necessary to make the value
            fit. Default True.
        * noRepeat: Don't print again if it's the same value as the last
            record. Default False.
        * richText: Render the value as HTML code. Default False.
        * textOptions: QTextOption, mainly used for text alignment.

    """
    textOptions = QTextOption()
    noRepeat = False
    _lastText = None
    richText = False
    expand = False

    def _expandHeight(self, painter, text):
        if self.richText:
            doc = QTextDocument()
            font = self.font or painter.font()
            doc.setDefaultFont(font)
            doc.setTextWidth(self.width)
            doc.setHtml(text)
            return max(self.height, doc.size().height())
        else:
            font = self.font or painter.font()
            fm = QFontMetricsF(font)
            bound_rect = fm.boundingRect(
                QRectF(self.left, self.top, self.width, self.height),
                self.textOptions.flags() | Qt.TextWordWrap,
                text)
            return max(self.height, bound_rect.height())

    def renderHeight(self, painter, data_item):
        if self.expand:
            text = self._text(data_item)
            return self._expandHeight(painter, text)
        else:
            return self.height

    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        text = self._text(data_item)

        if self.noRepeat and self._lastText == text:
            return
        self._lastText = text

        self.renderSetup(painter)
        if self.font:
            parent_font = painter.font()
            painter.setFont(self.font)
        if self.expand:
            effectiveHeight = self._expandHeight(painter, text)
        else:
            effectiveHeight = self.height
        elementRect = QRectF(
            QPointF(self.left, self.top) + rect.topLeft(),
            QSizeF(self.width, effectiveHeight))
        self.renderBorderAndBackground(painter, elementRect)

        if self.richText:
            doc = QTextDocument()
            doc.documentLayout().setPaintDevice(painter.device())
            doc.setPageSize(elementRect.size())
            doc.setDefaultFont(painter.font())
            doc.setHtml(text)
            painter.translate(elementRect.topLeft())
            doc.drawContents(painter)
            painter.resetTransform()
        else:
            textOptions = self.textOptions
            textOptions.setWrapMode(QTextOption.WordWrap)
            painter.drawText(elementRect, unicode(text),
                textOptions)
        self.renderTearDown(painter)


class Label(TextElement):
    """
        Static (unless you cheat using events ;-) text element.

        Inherits TextElement.

        Properties
        ----------
        * text: unicode, text value of the Label.
    """

    def _text(self, data_item):
        return self.text

class FranqAttributeError(AttributeError):
    pass

class FranqFormatterError(Exception):
    pass


class Field(TextElement):
    """
        Dynamic, dataset item attribute based text element.
        Useful when dataset items are entity objects.

        Inherits TextElement.

        Properties
        ----------
        * attrName: str, attribute name.
        * formatter: callable, optional, default None.
        * formatStr: unicode, optional Python standard formatting string,
            default None.
        If both formatter and formatStr are set, formatter is used.
    """
    formatStr = None
    formatter = None

    def _get_value(self, data_item):
        value = None

        propertyparts = self.attrName.split('.')

        try:
            obj = data_item
            prop = propertyparts.pop(0)
            while propertyparts:
                obj = getattr(obj, prop)
                prop = propertyparts.pop(0)
            value = getattr(obj, prop)
        except AttributeError:
            raise FranqAttributeError("Attribute {} ({}) not found"
                " in the model {}({})"
                .format(self.attrName, prop, data_item, type(data_item)))
        return value

    def _text(self, data_item):
        v = self._get_value(data_item)
        if self.formatter:
            try:
                return self.formatter(v)
            except (TypeError, ValueError):
                raise FranqFormatterError("Can't format value \"{}\""
                    " from attribute {} with formatter {}"
                    .format(v, self.attrName, self.formatter.__name__))
        elif self.formatStr:
            return self.formatStr.format(v)
        else:
            if v is None:
                v = ''
            return str(v)


class Function(TextElement):
    """
        Dynamic Function based text element.

        Inherits TextElement.

        Properties
        ----------
        * func: callable, usually a lambda or a report method, receives the
            data item as parameter, returns unicode value to render.
    """

    def __init__(self, **kw):
        super(TextElement, self).__init__(**kw)
        self._last_id = None
        self._last_value = None

    def _text(self, data_item):
        # Avoid calling func twice with the same argument
        # _last_id is reset in render() as the main reason to do caching
        # is to reuse the value for renderHeight() and render() calls.
        # Also, when the Function object is created as a report class member
        # the _last_id is preserved between report renderings leading
        # to incorrect behaviour if caching is allowed
        if id(data_item) != self._last_id:
            self._last_id = id(data_item)
            self._last_value = self.func(data_item)
        return self._last_value

    def render(self, painter, rect, data_item):
        super().render(painter, rect, data_item)
        self._last_id = None


class Line(Element):
    """
        Line drawing element.

        Inherits Element.
    """
    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)

        self.renderSetup(painter)
        left = self.left + rect.left()
        top = self.top + rect.top()
        painter.drawLine(left, top, left + self.width, top + self.height)
        self.renderTearDown(painter)


class Box(Element):
    """
        Box drawing element

        Inherits Element.
    """
    pen = QColor("black")  # FIXME: Keep inheritance while making border optional?

    def render(self, painter, rect, data_item):
        if self.on_before_print is not None:
            self.on_before_print(self, data_item)
        elementRect = QRectF(QPointF(self.left, self.top) + rect.topLeft(),
            QSizeF(self.width, self.height))
        self.renderSetup(painter)
        if self.background:
            painter.fillRect(elementRect, self._getBackground())
        if self.pen is not None:
            painter.drawRect(
                QRectF(self.left + rect.left(), self.top + rect.top(),
                self.width, self.height))
        self.renderTearDown(painter)


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
                self.pixmap = QPixmap(self.fileName)
            else:
                return

        painter.drawPixmap(
            QRectF(self.left + rect.left(), self.top + rect.top(),
                self.width, self.height),
            self.pixmap,
            QRectF(0, 0, self.pixmap.width(), self.pixmap.height()))
