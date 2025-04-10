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



class FilterDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Filter')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        layout = QVBoxLayout()
        self._ui_search_text = QLineEdit()
        self._ui_search_text.setPlaceholderText('Search regex')
        self._ui_search_text.textChanged.connect(self.on_search_change)
        self._ui_search_text.setAcceptDrops(True)
        self._ui_search_text.returnPressed.connect(self.accept)
        layout.addWidget(self._ui_search_text)
        self._ui_files_list = QListView()
        self._ui_files_list.setMinimumSize(200, 100)
        self._ui_files_model = QtGui.QStandardItemModel()
        self._ui_files_list.setModel(self._ui_files_model)
        layout.addWidget(self._ui_files_list)
        self.setLayout(layout)

        self.resize(400, 500)
    

    @property
    def ui_search_text(self) -> str:
        return self._ui_search_text.text()
    

    def ui_set_files(self, files: list[str]):
        self._ui_files_model.clear()
        for file in files:
            self._ui_files_model.appendRow(QtGui.QStandardItem(file))
    

    def ui_indicate_search_error(self, indicate_error: bool = True):
        QtHelper.apply_warning_color(self._ui_search_text, indicate_error)
    

    def ui_show_modal(self) -> bool:
        return self.exec() == QDialog.DialogCode.Accepted


    # to be implemented in derived class
    def on_search_change(self):
        pass
