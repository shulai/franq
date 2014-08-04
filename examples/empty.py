# -*- coding: utf-8 -*-

import sip
sip.setapi("QString", 2)

from PyQt4 import QtGui
from franq import Report


class EmptyReport(Report):
    pass

app = QtGui.QApplication([])

r = Report()

printer = QtGui.QPrinter()
printer.setOutputFileName('empty.pdf')
r.render(printer)

