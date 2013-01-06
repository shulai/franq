# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report, Band, Function


class DetailBandReport(Report):
    printIfEmpty = True
    margin = (10, 10, 10, 25)
    detail = Band(
        border=QtGui.QColor("blue"),
        height = 5,
        elements = [
            Function(top=5, left=5, height=5, width=30, func=lambda x: x)
            ])

app = QtGui.QApplication([])

r = DetailBandReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('detail.pdf')
fruits=["Apple", "Orange", "Pear"]
r.render(printer, fruits)
