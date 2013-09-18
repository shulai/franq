# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report


class EmptyReport(Report):
    printIfEmpty = True

app = QtGui.QApplication([])

r = Report()
r.printIfEmpty = False

printer = QtGui.QPrinter()
printer.setOutputFileName('empty1.pdf')
r.render(printer)

r = EmptyReport()


printer.setOutputFileName('empty2.pdf')
r.render(printer)
