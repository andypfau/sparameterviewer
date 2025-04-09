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



class RlDialogUi(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Return Loss Integrator')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
    

    def show(self):
        self.exec()
