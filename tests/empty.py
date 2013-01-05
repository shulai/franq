# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from franq import Report

class EmptyReport(Report):
    pass

app = QtGui.QApplication([])

r = Report()
r.properties['print_if_empty'] = True

printer = QtGui.QPrinter()
printer.setOutputFileName('empty1.pdf')
r.render(printer, None)

r = EmptyReport()
r.properties['print_if_empty'] = True

printer.setOutputFileName('empty2.pdf')
r.render(printer, None)



