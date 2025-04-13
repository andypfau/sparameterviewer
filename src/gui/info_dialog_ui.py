from .qt_helper import QtHelper
from lib import AppPaths
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import pathlib
import enum
import logging
import os
from typing import Callable, Union



class InfoDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('File Info')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        self._ui_infostr = QPlainTextEdit()
        self._ui_infostr.setMinimumSize(200, 100)
        self._ui_infostr.setReadOnly(True)
        self._ui_infostr.setFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self._ui_infostr.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        self.setLayout(QtHelper.layout_v(self._ui_infostr))

        self.resize(800, 600)
    

    def ui_show_modal(self):
        self.exec()


    def ui_set_text(self, text: str):
        self._ui_infostr.setPlainText(text)
