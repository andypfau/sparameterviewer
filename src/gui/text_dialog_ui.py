from .helpers.qt_helper import QtHelper
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



class TextDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Info')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        self._ui_infostr = QPlainTextEdit()
        self._ui_infostr.setMinimumSize(200, 100)
        self._ui_infostr.setReadOnly(True)
        self._ui_infostr.setFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self._ui_infostr.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self._ui_copy_button = QtHelper.make_button('Copy', self.on_copy)
        self._ui_copy_shortcut = QtHelper.make_shortcut(self, 'Ctrl+C', self.on_copy)
        self._ui_save_button = QtHelper.make_button('Save As...', self.on_save)
        self._ui_save_shortcut = QtHelper.make_shortcut(self, 'Ctrl+S', self.on_save)
        self._ui_open_button = QtHelper.make_button('Open Externally', self.on_open_ext)
        
        self.setLayout(QtHelper.layout_v(
            self._ui_infostr,
            QtHelper.layout_h(self._ui_copy_button, self._ui_save_button, self._ui_open_button, ...),
        ))

        self.resize(800, 600)
    

    def ui_show_modal(self):
        self.exec()


    def ui_show_open_button(self, show: bool = True):
        self._ui_open_button.setVisible(show)


    def ui_set_text(self, text: str):
        self._ui_infostr.setPlainText(text)


    def ui_set_title(self, title: str):
        self.setWindowTitle(title)


    # to be implemented in derived class
    def on_copy(self):
        pass
    def on_save(self):
        pass
    def on_open_ext(self):
        pass
