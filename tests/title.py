# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report, Band, Label


class TitleBandReport(Report):
    
    print_if_empty = True
    background = QtGui.QBrush(QtGui.QColor("cyan"))
    title = Band(
        border=QtGui.QColor("blue"),
        background=QtGui.QBrush(QtGui.QColor("white")),
        elements = [
            Label(top=5, left=5, height=5, width=30, text=u"Hello World")
            ])

app = QtGui.QApplication([])

r = TitleBandReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('title.pdf')
r.render(printer, None)
