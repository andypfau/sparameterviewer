from lib import is_windows, AppGlobal
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import logging
import pathlib
from typing import Callable, Union



class QtHelper:


    @staticmethod
    def set_dialog_icon(dialog: Union[QDialog,QMainWindow]):
        
        if is_windows():
            images_to_try = ['sparamviewer.ico']
        else:
            images_to_try = ['sparamviewer.png', 'sparamviewer.xbm']
        for image in images_to_try:
            try:
                icon_path = pathlib.Path(AppGlobal.get_resource_dir()) / image
                dialog.setWindowIcon(QtGui.QIcon(str(icon_path)))
                return
            except Exception as ex:
                logging.debug(f'Cannot load icon <{image}>, trying next')
        logging.debug(f'Unable to set window icon')


    @staticmethod
    def make_label(text: str) -> QLabel:
        label = QLabel()
        label.setText(text)
        return label


    @staticmethod
    def add_submenu(parent, menu: QMenu, text: str, visible: bool = True) -> QMenu:
        submenu = QMenu(text, parent)
        if not visible:
            submenu.setVisible(False)
        menu.addMenu(submenu)
        return submenu


    @staticmethod
    def add_menuitem(menu: QMenu, text: str, action: Callable, *, shortcut: str = '', visible: bool = True, checkable: bool = False) -> QAction:
        item = QAction(text)
        if action:
            item.triggered.connect(action)
        if shortcut:
            item.setShortcut(QKeySequence(shortcut))
        if checkable:
            item.setCheckable(True)
        if not visible:
            item.setVisible(False)
        menu.addAction(item)
        return item
