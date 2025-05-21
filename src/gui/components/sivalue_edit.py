from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths
from lib import Si, SiFmt

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class SiValueEdit(QLineEdit):

    valueChanged = pyqtSignal()

    def __init__(self, parent: QWidget = None, si: Si|None = None, require_return_press: bool = False):
        super().__init__(parent)
        self.setMinimumWidth(150)
        
        self._require_return_press = require_return_press
        self._value = si
        self.setValue(self._value)
        self.setRequireReturnPress(self._require_return_press)
        self.textChanged.connect(self._on_text_changed)
    

    def keyPressEvent(self, event: QtGui.QKeyEvent|None):
        if event:
            if event.key() == Qt.Key.Key_Escape:
                self._on_escape_pressed()
            elif event.key() == Qt.Key.Key_Return:
                self._on_return_pressed()
        return super().keyPressEvent(event)

    
    def focusOutEvent(self, event: QtGui.QFocusEvent|None):
        if self._value is None:
            self.setText('')
        else:
            self.setText(str(self._value))
        return super().focusOutEvent(event)


    def requireReturnPress(self) -> bool:
        return self._require_return_press
    def setRequireReturnPress(self, value: bool):
        self._require_return_press = value
        if self._require_return_press:
            self.setPlaceholderText('Enter value, press return...')
        else:
            self.setPlaceholderText('Enter value...')


    def value(self) -> Si|None:
        return self._value
    def setValue(self, value: Si|None):
        if value == self._value:
            return
        self._value = value
        if self._value is None:
            self.setText('')
        else:
            self.setText(str(self._value))
        QtHelper.indicate_error(self, False)

    
    def _on_escape_pressed(self):
        if self._value is None:
            self.setText('')
        else:
            self.setText(str(self._value))

    
    def _on_return_pressed(self):
        if self.isReadOnly() or self._value is None or not self._require_return_press:
            return
        try:
            new_value = Si(self.text(), si_fmt=self._value.format)

            if self._value == new_value:
                return
            self._value = new_value
            self.setText(str(self._value))
            self.valueChanged.emit()
        except:
            self.setText(str(self._value))
        QtHelper.indicate_error(self, False)

    
    def _on_text_changed(self):
        if self.isReadOnly() or self._value is None:
            return
        try:
            new_value = Si(self.text(), si_fmt=self._value.format)
            QtHelper.indicate_error(self, False)

            if self._require_return_press:
                return  # we updated the error indicator, that's it for now
            if self._value == new_value:
                return
            self._value = new_value
            self.setText(str(self._value))
            self.valueChanged.emit()
        except:
            QtHelper.indicate_error(self, True)
