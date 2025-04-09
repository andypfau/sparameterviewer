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



class SettingsDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        QtHelper.set_dialog_icon(self)

        main_layout = QHBoxLayout()
        tabs = QTabWidget()
        main_layout.addWidget(tabs)
        buttons_layout = QVBoxLayout()
        buttons_layout.addWidget(QtHelper.make_button('&OK', self.on_ok))
        buttons_layout.addWidget(QtHelper.make_button('&Cancel', self.on_cancel))
        main_layout.addLayout(buttons_layout)
        self.setLayout(main_layout)

        axes_widget = QWidget()
        tabs.addTab(axes_widget, 'Axes')

        plot_widget = QWidget()
        tabs.addTab(plot_widget, 'Plot')

        plot_widget = QWidget()
        tabs.addTab(plot_widget, 'Plot')

        self.adjustSize()
    

    def ui_show(self):
        self.exec()


    # to be implemented in derived class
    def on_ok(self): raise NotImplementedError()
    def on_cancel(self): raise NotImplementedError()
