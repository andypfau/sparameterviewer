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

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.ui_infostr = QPlainTextEdit()
        self.ui_infostr.setMinimumSize(200, 100)
        self.ui_infostr.setReadOnly(True)
        self.ui_infostr.setFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self.ui_infostr.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.ui_infostr)

        self.resize(800, 600)
    

    def ui_show_modal(self, text: str):
        self.ui_infostr.setPlainText(text)
        self.exec()
