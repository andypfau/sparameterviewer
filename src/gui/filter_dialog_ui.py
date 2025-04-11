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
        search_layout = QHBoxLayout()
        layout.addLayout(search_layout)
        self._ui_search_text = QLineEdit()
        self._ui_search_text.setPlaceholderText('Search expression...')
        self._ui_search_text.textChanged.connect(self.on_search_change)
        self._ui_search_text.setAcceptDrops(True)
        self._ui_search_text.returnPressed.connect(self.accept)
        search_layout.addWidget(self._ui_search_text)
        self._ui_wildcard_radio = QRadioButton('Wildcards')
        self._ui_wildcard_radio.toggled.connect(self.on_search_mode_change)
        search_layout.addWidget(self._ui_wildcard_radio)
        self._ui_regex_radio = QRadioButton('Regex')
        self._ui_regex_radio.toggled.connect(self.on_search_mode_change)
        search_layout.addWidget(self._ui_regex_radio)
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
    @ui_search_text.setter
    def ui_search_text(self, value: str):
        self._ui_search_text.setText(value)
    

    @property
    def ui_regex_mode(self) -> bool:
        return self._ui_regex_radio.isChecked()
    @ui_regex_mode.setter
    def ui_regex_mode(self, value: bool):
        if value:
            self._ui_regex_radio.setChecked(True)
        else:
            self._ui_wildcard_radio.setChecked(True)
    

    def ui_set_files(self, files: list[str]):
        self._ui_files_model.clear()
        for file in files:
            self._ui_files_model.appendRow(QtGui.QStandardItem(file))
    

    def ui_indicate_search_error(self, indicate_error: bool = True):
        QtHelper.indicate_error(self._ui_search_text, indicate_error)
    

    def ui_show_modal(self) -> bool:
        self._ui_search_text.selectAll()
        self._ui_search_text.focusWidget()
        return self.exec() == QDialog.DialogCode.Accepted


    # to be implemented in derived class
    def on_search_change(self):
        pass
    def on_search_mode_change(self):
        pass
