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



class TabularDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Tabular Data')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)

        main_layout = QVBoxLayout()
        
        self.ui_main_menu = QMenuBar()
        self._build_main_menu()
        main_layout.addWidget(self.ui_main_menu)
        
        self.ui_fileselect_combo = QComboBox()
        main_layout.addWidget(self.ui_fileselect_combo)

        combo_layout = QHBoxLayout()
        self.ui_param_combo = QComboBox()
        combo_layout.addWidget(self.ui_param_combo)
        combo_layout.addWidget(QtHelper.make_label('f:'))
        self.ui_f_filter_edit = QComboBox()
        self.ui_f_filter_edit.setEditable(True)
        combo_layout.addWidget(self.ui_f_filter_edit)
        combo_layout.addWidget(QtHelper.make_label('Params:'))
        self.ui_param_filter_edit = QComboBox()
        self.ui_param_filter_edit.setEditable(True)
        combo_layout.addWidget(self.ui_param_filter_edit)
        main_layout.addLayout(combo_layout)

        self.ui_table = QTableView()
        main_layout.addWidget(self.ui_table)

        self.setLayout(main_layout)

    
    def _build_main_menu(self):
        self.ui_mainmenu_file = QtHelper.add_submenu(self, self.ui_main_menu, '&File')
        self.ui_mainmenu_export = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Export', action=None)
    

    def ui_show(self):
        self.exec()
