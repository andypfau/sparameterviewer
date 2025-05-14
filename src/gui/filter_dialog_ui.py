from .helpers.qt_helper import QtHelper
from info import Info
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



class FilterDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Filter Files')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        self._ui_search_text = QLineEdit()
        self._ui_search_text.setPlaceholderText('Enter expression, then press Enter')
        self._ui_search_text.setToolTip('Enter your search expression here, then press Enter (or press Escape to abort)')
        self._ui_search_text.textChanged.connect(self.on_search_change)
        self._ui_search_text.setAcceptDrops(True)
        self._ui_search_text.returnPressed.connect(self.accept)

        self._ui_wildcard_radio = QRadioButton('Wildcards')
        self._ui_wildcard_radio.setToolTip('You can use the wildcards "*" (anything) and "?" (any single character)')
        self._ui_wildcard_radio.toggled.connect(self.on_search_mode_change)

        self._ui_regex_radio = QRadioButton('Regex')
        self._ui_regex_radio.setToolTip('You can use regular expressions')
        self._ui_regex_radio.toggled.connect(self.on_search_mode_change)

        self._ui_files_list = QListView()
        self._ui_files_list.setMinimumSize(200, 100)
        self._ui_files_model = QtGui.QStandardItemModel()
        self._ui_files_list.setModel(self._ui_files_model)
        
        self.setLayout(QtHelper.layout_v(
            QtHelper.layout_h(
                self._ui_search_text,
                self._ui_wildcard_radio,
                self._ui_regex_radio,
            ),
            self._ui_files_list,
        ))

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
    

    def ui_set_files(self, files: list[str], other_files: list[str]):
        self._ui_files_model.clear()
        for file in files:
            item = QtGui.QStandardItem(file)
            self._ui_files_model.appendRow(item)
        for other_file in other_files:
            item = QtGui.QStandardItem(other_file)
            item.setForeground(QPalette().color(QPalette.ColorRole.PlaceholderText))
            self._ui_files_model.appendRow(item)
    

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
