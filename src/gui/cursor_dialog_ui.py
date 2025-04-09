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



class CursorDialogUi(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Trace Cursors')
        QtHelper.set_dialog_icon(self)
    

    def show(self):
        self.exec()
