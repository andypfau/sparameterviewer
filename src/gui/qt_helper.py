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
    def make_label(text: str, *, font: Union[QFont,None] = None, stretch: bool = False) -> QLabel:
        label = QLabel()
        label.setText(text)
        if font:
            label.setFont(font)
        if not stretch:
            label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed, QSizePolicy.ControlType.Label))
        return label


    @staticmethod
    def make_font(*, base: QFont = None, families: list[str] = None, bold: bool = None, underline: bool = None, strikethru: bool = None, rel_size: float = None) -> QFont:
        if base:
            font = QFont(base)
        else:
            font = QFont()
        if families is not None:
            font.setFamilies(families)
        if bold is not None:
            font.setBold(bold)
        if rel_size is not None:
            font.setPointSizeF(font.pointSizeF() * rel_size)
        if underline is not None:
            font.setUnderline(bold)
        if strikethru is not None:
            font.setStrikeOut(strikethru)
        return font


    @staticmethod
    def make_image(path: str, placeholder: str = 'Placeholder') -> QLabel:
        image = QLabel()
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                raise RuntimeError('QPixmap is null')
            image.setPixmap(pixmap)
            image.adjustSize()
        except Exception as ex:
            logging.error('Unable to create QPixmap from <{path}>')
            logging.exception(ex)
            image.setText(placeholder)
        return image


    @staticmethod
    def make_button(text: str, action: Callable = None) -> QPushButton:
        button = QPushButton()
        button.setText(text)
        if action:
            button.clicked.connect(action)
        return button


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


    @staticmethod
    def get_available_fonts() -> list[str]:
        return QtGui.QFontDatabase.families()
