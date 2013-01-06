# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from franq import Report

class EmptyReport(Report):
    printIfEmpty = True

app = QtGui.QApplication([])

r = Report()
r.printIfEmpty = True

printer = QtGui.QPrinter()
printer.setOutputFileName('empty1.pdf')
r.render(printer, None)

r = EmptyReport()


printer.setOutputFileName('empty2.pdf')
r.render(printer, None)



