from .qt_helper import QtHelper
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



class AboutDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('About')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog)

        image_path = pathlib.Path(AppPaths.get_resource_dir()) / 'sparamviewer.png'
        self.setLayout(QtHelper.layout_h(
            10, QtHelper.make_image(str(image_path), 'Logo'), 20,
            QtHelper.layout_v(
                QtHelper.make_label(Info.AppName, font=QtHelper.make_font(rel_size=1.25)),
                8,
                Info.AppVersionStr,
                Info.AppDateStr,
                ...
            ),
        ))
        
        self.adjustSize()
    

    def ui_show_modal(self):
        self.exec()
