# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog

unit_factor = 300 / 25.4


class MarginsDialog(QDialog):

    def __init__(self):
        super().__init__()
        from .margins_ui import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def setModel(self, margins):
        self._margins = margins
        self.ui.top.setValue(round(margins[0] / unit_factor, 2))
        self.ui.right.setValue(round(margins[1] / unit_factor, 2))
        self.ui.bottom.setValue(round(margins[2] / unit_factor, 2))
        self.ui.left.setValue(round(margins[3] / unit_factor, 2))

    def model(self):
        return (
            self.ui.top.value() * unit_factor,
            self.ui.right.value() * unit_factor,
            self.ui.bottom.value() * unit_factor,
            self.ui.left.value() * unit_factor)
