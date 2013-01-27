# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report, Band, Label, mm


class BeginBandReport(Report):

    printIfEmpty = True
    background = QtGui.QBrush(QtGui.QColor("cyan"))
    begin = Band(
        border=QtGui.QColor("blue"),
        background=QtGui.QBrush(QtGui.QColor("white")),
        elements=[
            Label(top=5 * mm, left=5 * mm, height=5 * mm, width=30 * mm,
                text=u"Hello World")
            ])

app = QtGui.QApplication([])

r = BeginBandReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('begin.pdf')
r.render(printer, None)
