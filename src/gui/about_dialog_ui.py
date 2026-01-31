from .helpers.qt_helper import QtHelper
from info import Info
from lib.settings import Settings
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
import sys
from typing import Callable, Union



class AboutDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('About')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog)

        self._ui_expand_link = QLabel()
        self._ui_expand_link.setText('<a href=".">Show more...</a>')
        self._ui_expand_link.setOpenExternalLinks(False)
        self._ui_expand_link.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
        self._ui_expand_link.linkActivated.connect(self._ui_link_clicked)
        
        executable_loc = os.path.abspath(sys.argv[0])
        settings_loc = os.path.abspath(Settings.settings_file_path)
        docs_loc = os.path.abspath(AppPaths.get_doc_dir())
        changelog_loc = os.path.abspath(AppPaths.get_changelog())
        license_loc = os.path.abspath(AppPaths.get_license())
        log_loc = os.path.abspath(AppPaths.get_log_path())
        self._ui_more_text = QTextEdit()
        self._ui_more_text.setText(f'Help: <{docs_loc}>\nChangelog: <{changelog_loc}>\nLicense: <{license_loc}>\nExecutable: <{executable_loc}>\nSettings: <{settings_loc}>\nLog: <{log_loc}>')
        self._ui_more_text.setReadOnly(True)
        self._ui_more_text.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        self._ui_more_text.setMinimumSize(250, 80)
        self._ui_more_text.setVisible(False)

        image_path = pathlib.Path(AppPaths.get_resource_dir()) / 'sparamviewer.png'
        self.setLayout(QtHelper.layout_h(
            10, QtHelper.make_image(str(image_path), 'Logo'), 20,
            QtHelper.layout_v(
                QtHelper.make_label(Info.AppName, font=QtHelper.make_font(rel_size=1.25)),
                8,
                Info.AppVersionStr,
                Info.AppDateStr,
                16,
                self._ui_expand_link,
                self._ui_more_text,
                ...
            ),
        ))
        
        self.adjustSize()
    

    def ui_show_modal(self):
        self.exec()


    def _ui_link_clicked(self):
        self._ui_more_text.setVisible(True)
        self._ui_expand_link.setVisible(False)
