# -*- coding: utf-8 -*-

from PyQt4.QtGui import QFontDialog


class FontDialog(QFontDialog):

    def __init__(self):
        super(FontDialog, self).__init__()

    def setModel(self, font):
        self.setCurrentFont(font)

    def model(self):
        return self.currentFont()