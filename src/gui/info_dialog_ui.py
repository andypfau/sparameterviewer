from .qt_helper import QtHelper
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

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Info')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)

        layout = QVBoxLayout()
        self.setLayout(layout)
        self.ui_editor = QPlainTextEdit()
        self.ui_editor.setMinimumSize(400, 300)
        self.ui_editor.setReadOnly(True)
        editor_font = QFont()
        editor_font.setFamilies(['Fira Code', 'Consolas', 'Courier New', 'monospace'])
        self.ui_editor.setFont(editor_font)
        self.ui_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.ui_editor)

        self.resize(800, 600)
    

    def ui_show(self, title: str, text: str):
        self.setWindowTitle(title)
        self.ui_editor.setPlainText(text)
        self.exec()
