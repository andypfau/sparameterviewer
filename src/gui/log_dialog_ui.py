from .qt_helper import QtHelper
from lib import AppGlobal
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import pathlib
import enum
import os
from typing import Callable, Union



class LogDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Log')
        QtHelper.set_dialog_icon(self)
        self.finished.connect(self.on_close)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setSizeGripEnabled(True)
        
        self.ui_logtext = QPlainTextEdit()
        self.ui_logtext.setMinimumSize(200, 100)
        self.ui_logtext.setReadOnly(True)
        self.ui_logtext.setFont(QtHelper.make_font(families=AppGlobal.get_preferred_monospace_fonts()))
        self.ui_logtext.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.ui_logtext)

        layout.addWidget(QtHelper.make_label('Level:'))
        self.ui_level_combo = QComboBox()
        self.ui_level_combo.currentIndexChanged.connect(self.on_select_level)
        layout.addWidget(self.ui_level_combo)

        self.resize(800, 600)
    

    def ui_set_level_strings(self, levels: list[str]):
        for level in levels:
            self.ui_level_combo.addItem(level)
    

    def ui_show(self):
        self.show()

    
    @property
    def ui_level_str(self) -> str:
        return self.ui_level_combo.currentText()
    @ui_level_str.setter
    def ui_level_str(self, value: str):
        self.ui_level_combo.setCurrentText(value)


    def ui_set_logtext(self, text: str):
        self.ui_logtext.setPlainText(text)


    # to be implemented in derived class
    def on_select_level(self):
        raise NotImplementedError
