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
import os
from typing import Callable, Union



class LogDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Log')
        QtHelper.set_dialog_icon(self)
        self.setSizeGripEnabled(True)
        #self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
        #self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint, False)
        #self.setModal(False)
        
        self._ui_logtext = QPlainTextEdit()
        self._ui_logtext.setMinimumSize(200, 100)
        self._ui_logtext.setReadOnly(True)
        self._ui_logtext.setFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self._ui_logtext.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._ui_level_combo = QComboBox()
        self._ui_level_combo.currentIndexChanged.connect(self.on_select_level)
        
        self._ui_clear_button = QPushButton('Clear Log')
        self._ui_clear_button.clicked.connect(self.on_clear)

        self.setLayout(QtHelper.layout_v(
            self._ui_logtext,
            QtHelper.layout_h('Level:', self._ui_level_combo, ..., self._ui_clear_button)
        ))

        self.resize(800, 600)
    

    def ui_set_level_strings(self, levels: list[str]):
        for level in levels:
            self._ui_level_combo.addItem(level)
    

    def ui_show(self):
        self.show()

    
    @property
    def ui_level_str(self) -> str:
        return self._ui_level_combo.currentText()
    @ui_level_str.setter
    def ui_level_str(self, value: str):
        self._ui_level_combo.setCurrentText(value)


    def ui_set_logtext(self, text: str):
        self._ui_logtext.setPlainText(text)


    # to be implemented in derived class
    def on_select_level(self):
        pass
    def on_clear(self):
        pass
