# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report, DetailBand, Function, mm


class DetailBandReport(Report):
    printIfEmpty = True
    margin = (10 * mm, 10 * mm, 10 * mm, 25 * mm)
    detail = DetailBand(
        dataSet='fruits',
        border=QtGui.QColor("blue"),
        height=5 * mm,
        elements=[
            Function(top=0 * mm, left=5 * mm, height=5 * mm, width=30 * mm,
                func=lambda x: x)
            ])

app = QtGui.QApplication([])

r = DetailBandReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('detail.pdf')
fruits = ["Apple", "Orange", "Pear"]
r.render(printer, fruits=fruits)
