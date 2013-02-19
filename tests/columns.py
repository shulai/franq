# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from PyQt4.QtCore import Qt
from franq import Report, Section, Band, DetailBand, Label, Function, mm


class DetailBandReport(Report):
    printIfEmpty = True
    margin = (10 * mm, 10 * mm, 10 * mm, 25 * mm)
    header = Band(
        elements=[
            Label(top=0 * mm, left=20 * mm, height=10 * mm, width=145 * mm,
                border=(None, None, QtGui.QPen(QtGui.QBrush("black"), 3),
                    None),
                font=QtGui.QFont("Serif", 14),
                text=u"Header - Title",
                textOptions=QtGui.QTextOption(Qt.AlignCenter))
            ])
    sections = [
        Section(
            columns=2,
            detailBands=[
                DetailBand(
                    height=5 * mm,
                    columnSpace=10 * mm,
                    elements=[
                        Function(top=0 * mm, left=0 * mm,
                            height=5 * mm, width=30 * mm,
                            func=lambda x: x[0]),
                        Function(top=0 * mm, left=30 * mm,
                            height=5 * mm, width=30 * mm,
                            func=lambda x: x[1])
                    ]
                )
            ]
        )
    ]
    footer = Band(
        elements=[
            Label(top=0 * mm, left=0 * mm, height=10 * mm, width=185 * mm,
                text=u"Footer - Title")
            ])

app = QtGui.QApplication([])

r = DetailBandReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('columns.pdf')
data = [(i, i * 3) for i in range(0, 100)]
r.render(printer, data)
