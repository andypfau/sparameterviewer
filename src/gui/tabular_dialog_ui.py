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
import pandas as pd



class TabularDialogUi(QDialog):


    class TableModel(QtCore.QAbstractTableModel):

        def __init__(self, headers: list[str], columns: list[list[str]]):
            super().__init__()
            self._headers = headers
            self._columns = columns

        def data(self, index, role):
            if role == Qt.ItemDataRole.DisplayRole:
                return str(self._columns[index.column()][index.row()])

        def rowCount(self, index):
            if len(self._columns) > 0:
                return len(self._columns[0])
            else:
                return 0

        def columnCount(self, index):
            return len(self._headers)

        def headerData(self, section, orientation, role):
            if role == Qt.ItemDataRole.DisplayRole:
                if orientation == Qt.Orientation.Horizontal:
                    return str(self._headers[section])
                elif orientation == Qt.Orientation.Vertical:
                    return str(section)
                raise NotImplementedError()
    

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Tabular Data')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)

        main_layout = QVBoxLayout()
        
        self._ui_main_menu = QMenuBar()
        self._build_main_menu()
        main_layout.addWidget(self._ui_main_menu)
        
        self._ui_datasets_combo = QComboBox()
        self._ui_datasets_combo.currentIndexChanged.connect(self.on_change_dataset)
        main_layout.addWidget(self._ui_datasets_combo)

        combo_layout = QHBoxLayout()
        self._ui_format_combo = QComboBox()
        self._ui_format_combo.currentIndexChanged.connect(self.on_change_format)
        combo_layout.addWidget(self._ui_format_combo)
        combo_layout.addWidget(QtHelper.make_label('f:'))
        self._ui_f_filter_edit = QComboBox()
        self._ui_f_filter_edit.currentTextChanged.connect(self.on_change_freq_filter)
        self._ui_f_filter_edit.setEditable(True)
        combo_layout.addWidget(self._ui_f_filter_edit)
        combo_layout.addWidget(QtHelper.make_label('Params:'))
        self._ui_param_filter_edit = QComboBox()
        self._ui_param_filter_edit.currentTextChanged.connect(self.on_change_param_filter)
        self._ui_param_filter_edit.setEditable(True)
        combo_layout.addWidget(self._ui_param_filter_edit)
        main_layout.addLayout(combo_layout)

        self._ui_f_filter_note = None

        self._ui_table = QTableView()
        self._ui_table.setMinimumSize(400, 200)
        main_layout.addWidget(self._ui_table)

        self.setLayout(main_layout)

        self.resize(800, 600)

    
    def _build_main_menu(self):
        self._ui_mainmenu_file = QtHelper.add_submenu(self, self._ui_main_menu, '&File')
        self._ui_menuitem_save = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Save...', self.on_save)
        self._ui_menuitem_saveall = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Save All...', self.on_save_all)

        self._ui_mainmenu_edit = QtHelper.add_submenu(self, self._ui_main_menu, '&Edit')
        self._ui_menuitem_copy_csv = QtHelper.add_menuitem(self._ui_mainmenu_edit, 'Copy CSV', self.on_copy_csv)
        self._ui_mainmenu_edit.addSeparator()
        self._ui_menuitem_copy_numpy = QtHelper.add_menuitem(self._ui_mainmenu_edit, 'Copy Python (NumPy)', self.on_copy_numpy)
        self._ui_menuitem_copy_pandas = QtHelper.add_menuitem(self._ui_mainmenu_edit, 'Copy Python (Pandas)', self.on_copy_pandas)
        self._ui_mainmenu_edit.addSeparator()
        self._ui_menuitem_settings = QtHelper.add_menuitem(self._ui_mainmenu_edit, 'Settings...', self.on_settings, shortcut='F4')
    

    def ui_show(self):
        self.exec()

    
    def ui_set_datasets_list(self, datasets: list[str], selection: str = None):
        self._ui_datasets_combo.clear()
        if len(datasets) < 1:
            return
        for item in datasets:
            self._ui_datasets_combo.addItem(item)
        if not selection:
            selection = datasets[0]
        self._ui_datasets_combo.setCurrentText(selection)
    
    
    def ui_set_formats_list(self, formats: list[str], selection: str = None):
        self._ui_format_combo.clear()
        if len(formats) < 1:
            return
        for item in formats:
            self._ui_format_combo.addItem(item)
        if not selection:
            selection = formats[0]
        self._ui_format_combo.setCurrentText(selection)
    
    
    def ui_enable_format_selection(self, enable: bool):
        self._ui_format_combo.setEnabled(enable)
    
    
    def ui_set_freq_filters_list(self, filters: list[str], selection: str = None):
        self._ui_f_filter_edit.clear()
        if len(filters) < 1:
            return
        for item in filters:
            self._ui_f_filter_edit.addItem(item)
        if not selection:
            selection = filters[0]
        self._ui_f_filter_edit.setCurrentText(selection)
    
    
    def ui_set_param_filters_list(self, filters: list[str], selection: str = None):
        self._ui_param_filter_edit.clear()
        if len(filters) < 1:
            return
        for item in filters:
            self._ui_param_filter_edit.addItem(item)
        if not selection:
            selection = filters[0]
        self._ui_param_filter_edit.setCurrentText(selection)
    

    def ui_populate_table(self, headers: list[str], columns: list[list[str]]):
        self._ui_table_model = TabularDialogUi.TableModel(headers, columns)
        self._ui_table.setModel(self._ui_table_model)

    
    @property
    def ui_selected_dataset(self) -> str:
        return self._ui_datasets_combo.currentText()
    @ui_selected_dataset.setter
    def ui_selected_dataset(self, dataset: str):
        self._ui_datasets_combo.setCurrentText(dataset)

    
    @property
    def ui_selected_format(self) -> str:
        return self._ui_format_combo.currentText()

    
    @property
    def ui_selected_freq_filter(self) -> str:
        return self._ui_f_filter_edit.currentText()

    
    @property
    def ui_selected_param_filter(self) -> str:
        return self._ui_param_filter_edit.currentText()


    # to be implemented by derived class
    def on_change_dataset(self):
        pass
    def on_change_format(self):
        pass
    def on_change_freq_filter(self):
        pass
    def on_change_param_filter(self):
        pass
    def on_save(self):
        pass
    def on_save_all(self):
        pass
    def on_copy_csv(self):
        pass
    def on_copy_numpy(self):
        pass
    def on_copy_pandas(self):
        pass
    def on_settings(self):
        pass
