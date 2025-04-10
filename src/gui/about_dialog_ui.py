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



class AboutDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('About')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog)

        hlayout = QHBoxLayout()
        image_path = pathlib.Path(AppGlobal.get_resource_dir()) / 'sparamviewer.png'
        hlayout.addSpacing(10)
        hlayout.addWidget(QtHelper.make_image(str(image_path), 'Logo'))
        hlayout.addSpacing(20)
        vlayout = QVBoxLayout()
        hlayout.addLayout(vlayout)
        hlayout.addSpacing(10)
        
        vlayout.addWidget(QtHelper.make_label(Info.AppName, font=QtHelper.make_font(rel_size=1.25)))
        vlayout.addSpacing(8)
        vlayout.addWidget(QtHelper.make_label(Info.AppVersionStr))
        vlayout.addWidget(QtHelper.make_label(Info.AppDateStr))
        vlayout.addStretch()
        self.setLayout(hlayout)
        
        self.adjustSize()
    

    def ui_show_modal(self):
        self.exec()
