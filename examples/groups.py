# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report, Band, DetailBand, DetailGroup, Label, Function, mm


class GroupedReport(Report):
    printIfEmpty = True
    margin = (10 * mm, 10 * mm, 10 * mm, 25 * mm)
    detail = DetailBand(
        dataSet = 'foods',
        height=5 * mm,
        groups=[
            DetailGroup(
                lambda(r): r['type'],
                Band(
                    height=5 * mm,
                    elements=[
                        Label(top=0, left=0, height=5 * mm, width=10 * mm,
                            text=u"Type:"),
                        Function(top=0 * mm, left=10 * mm,
                            height=5 * mm, width=30 * mm,
                            func=lambda r: r['type'])
                        ]
                    ),
                Band(
                    height=5 * mm,
                    elements=[
                        Label(top=0, left=0, height=5 * mm, width=50 * mm,
                            text=u"End of group [type]"),
                        ]
                    )
                ),
            DetailGroup(
                lambda(r): r['sweet'],
                Band(
                    height=5 * mm,
                    elements=[
                        Label(top=0, left=10 * mm,
                            height=5 * mm, width=12 * mm,
                            text=u"Sweet:"),
                        Function(top=0 * mm, left=25 * mm,
                            height=5 * mm, width=30 * mm,
                            func=lambda r: r['sweet'])
                        ]
                    ),
                Band(
                    height=5 * mm,
                    elements=[
                        Label(top=0, left=10 * mm, height=5 * mm, width=50 * mm,
                            text=u"End of group [sweet]"),
                        ]
                    )
                ),
            ],
        elements=[
            Function(top=0 * mm, left=40 * mm, height=5 * mm, width=30 * mm,
                func=lambda r: r['name'])
            ])

app = QtGui.QApplication([])

r = GroupedReport()

printer = QtGui.QPrinter()
printer.setOutputFileName('groups.pdf')
foods = [
    {
        'name': "Bread",
        'type': 'bakery',
        'sweet': 'no'
    },
    {
        'name': "Cookies",
        'type': 'bakery',
        'sweet': 'yes'
    },
    {
        'name': "Olive",
        'type': 'fruit',
        'sweet': 'no'
    },
    {
        'name': "Apple",
        'type': 'fruit',
        'sweet': 'yes'
        },
    {
        'name': "Orange",
        'type': 'fruit',
        'sweet': 'yes'
        },
    {
        'name': "Pear",
        'type': 'fruit',
        'sweet': 'yes'
        }
    ]
r.render(printer, foods=foods)
