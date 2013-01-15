# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report, Band, Label, mm


class TitleAndChildReport(Report):

    printIfEmpty = True
    background = QtGui.QBrush(QtGui.QColor("cyan"))
    title = Band(
        border=QtGui.QColor("blue"),
        background=QtGui.QBrush(QtGui.QColor("white")),
        elements=[
            Label(top=5 * mm, left=5 * mm, height=5 * mm, width=30 * mm,
                text=u"Hello World")
            ],
        child=Band(
            background=QtGui.QBrush(QtGui.QColor(255, 255, 223)),
            elements=[
                Label(top=5 * mm, left=15 * mm, height=5 * mm, width=30 * mm,
                    text=u"Hello Child")
            ],
))

app = QtGui.QApplication([])

r = TitleAndChildReport()
printer = QtGui.QPrinter()
printer.setOutputFileName('child.pdf')
r.render(printer, None)
