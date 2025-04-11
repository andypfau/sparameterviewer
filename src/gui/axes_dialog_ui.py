from .qt_helper import QtHelper
from info import Info
from lib import AppGlobal
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



class AxesDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Manual Axes')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        
        self._ui_x_text = QComboBox()
        self._ui_x_text.setMinimumWidth(150)
        self._ui_x_text.setEditable(True)
        self._ui_x_text.currentTextChanged.connect(self.on_x_change)
        self._ui_x_model = QtGui.QStandardItemModel()
        self._ui_x_text.setModel( self._ui_x_model)
        
        self._ui_y_text = QComboBox()
        self._ui_y_text.setMinimumWidth(150)
        self._ui_y_text.setEditable(True)
        self._ui_y_text.currentTextChanged.connect(self.on_y_change)
        self._ui_y_model = QtGui.QStandardItemModel()
        self._ui_y_text.setModel( self._ui_y_model)

        self.setLayout(QtHelper.layout_grid([
            [None, 'Y:'                                   ],
            ['↑',  self._ui_y_text                        ],
            [None, None,             'X:', self._ui_x_text],
            [None, None,             None, '→'            ],
        ]))

        self.adjustSize()


    def ui_show_modal(self):
        self._ui_x_text.focusWidget()
        self.exec()


    def ui_set_x_presets(self, presets: list[str]):
        self._ui_x_model.clear()
        for preset in presets:
            self._ui_x_model.appendRow(QtGui.QStandardItem(preset))


    def ui_set_y_presets(self, presets: list[str]):
        self._ui_y_model.clear()
        for preset in presets:
            self._ui_y_model.appendRow(QtGui.QStandardItem(preset))


    @property
    def ui_x(self) -> str:
        return self._ui_x_text.currentText()
    @ui_x.setter
    def ui_x(self, value: str):
        self._ui_x_text.setCurrentText(value)


    @property
    def ui_y(self) -> str:
        return self._ui_y_text.currentText()
    @ui_y.setter
    def ui_y(self, value: str):
        self._ui_y_text.setCurrentText(value)

    
    def ui_inidicate_x_error(self, indicate_error: bool = True):
        QtHelper.indicate_error(self._ui_x_text, indicate_error)

    
    def ui_inidicate_y_error(self, indicate_error: bool = True):
        QtHelper.indicate_error(self._ui_y_text, indicate_error)


    # to be implemented in derived class
    def on_x_change(self):
        pass
    def on_y_change(self):
        pass
