# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from franq import Report, Band, DetailBand, Label, Function, mm


def pager():
    page = 1
    while True:
        yield page
        page +=1


page = pager()

class DetailBandReport(Report):
    printIfEmpty = True
    margin = (10 * mm, 10 * mm, 10 * mm, 25 * mm)
    dataSet = 'data'
    header = Band(
        elements=[
            Label(top=0 * mm, left=20 * mm, height=10 * mm, width=145 * mm,
                border=(None, None, QtGui.QPen(QtGui.QBrush("black"), 3),
                    None),
                font=QtGui.QFont("Serif", 14),
                text=u"Header - Title",
                textOptions=QtGui.QTextOption(Qt.AlignCenter))
            ])
    detail = DetailBand(
        height=5 * mm,
        elements=[
            Function(top=0 * mm, left=0 * mm, height=5 * mm, width=30 * mm,
                func=lambda x: x[0]),
            Function(top=0 * mm, left=100 * mm, height=5 * mm, width=30 * mm,
                func=lambda x: x[1])
            ])
    footer = Band(
        elements=[
            Label(top=0 * mm, left=0 * mm, height=10 * mm, width=185 * mm,
                text=u"Footer - Title"),
            Function(top=0, left=180 * mm, width=20 * mm,
                func=lambda o: 'Page ' + str(next(page)))
            ])

app = QtGui.QApplication([])

r = DetailBandReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('headfoot.pdf')
data = [(i, i * 3) for i in range(0, 100)]
r.render(printer, data=data)
