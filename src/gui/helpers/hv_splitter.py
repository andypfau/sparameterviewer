from __future__ import annotations

from .qt_helper import QtHelper
from .settings import Parameters
from lib import AppPaths, PathExt
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
import math
import numpy as np
import enum
from typing import Callable, Optional, Union



class HvSplitter(QWidget):


    class Orientation:
        Left1Right2 = enum.auto()
        Left2Right1 = enum.auto()
        Top1Bottom2 = enum.auto()
        Top2Bottom1 = enum.auto()


    splitterMoved = pyqtSignal()


    def __init__(self, child1: QWidget, child2: QWidget, orientation: HvSplitter.Orientation, parent: QWidget = None):
        super().__init__(parent)
        self._child1, self._child2 = child1, child2
        self._orientation = orientation
        self._collapsible1, self._collapsible2 = False, False

        self._ui_splitter = QSplitter(self)
        self._ui_splitter.addWidget(self._child1)
        self._ui_splitter.addWidget(self._child2)
        self._ui_layout = QVBoxLayout(self)
        self._ui_layout.addWidget(self._ui_splitter)
        self.setLayout(self._ui_layout)
        self._rearrange()

        
    def orientation(self) -> HvSplitter.orientation:
        return self._orientation
    def setOrientation(self, orienation: HvSplitter.orientation):
        if orienation != self._orientation:
            self._orientation = orienation
            self._rearrange()
    
    
    def setCollapsible(self, child1: bool = False, child2: bool = False):
        self._collapsible1, self._collapsible2 = child1, child2
        self._rearrange()


    def _rearrange(self):
        if self._orientation in [HvSplitter.Orientation.Left1Right2, HvSplitter.Orientation.Left2Right1]:
            self._ui_splitter.setOrientation(Qt.Orientation.Horizontal)
        else:
            self._ui_splitter.setOrientation(Qt.Orientation.Vertical)
        
        # insert dummy widgets first, otherwise the swap doesn't work
        self._ui_splitter.replaceWidget(0, QWidget())
        self._ui_splitter.replaceWidget(1, QWidget())

        if self._orientation in [HvSplitter.Orientation.Left1Right2, HvSplitter.Orientation.Top1Bottom2]:
            self._ui_splitter.replaceWidget(0, self._child1)
            self._ui_splitter.replaceWidget(1, self._child2)
            self._ui_splitter.setCollapsible(0, self._collapsible1)
            self._ui_splitter.setCollapsible(1, self._collapsible2)
        else:
            self._ui_splitter.replaceWidget(0, self._child2)
            self._ui_splitter.replaceWidget(1, self._child1)
            self._ui_splitter.setCollapsible(0, self._collapsible2)
            self._ui_splitter.setCollapsible(1, self._collapsible1)
