from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths
from lib import SiValue, SiFormat

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class SiValueEdit(QLineEdit):

    valueChanged = pyqtSignal()

    def __init__(self, parent: QWidget = None, si: SiValue = None, require_return_press: bool = False):
        super().__init__(parent)
        self.setMinimumWidth(150)
        self._require_return_press = require_return_press
        self._value: SiValue = si or SiValue(0)
        self._blank = False
        
        self.setPlaceholderText('Enter value...')
        self.setRequireReturnPress(self._require_return_press)
        
        self._value.attach(self._on_value_changed_externally)
        self._update_text_from_value()
        
        self.textChanged.connect(self._on_text_changed)
    

    def keyPressEvent(self, event: QtGui.QKeyEvent|None):
        if event:
            if event.key() == Qt.Key.Key_Escape:
                self._on_escape_pressed()
            elif event.key() == Qt.Key.Key_Return:
                self._on_return_pressed()
        return super().keyPressEvent(event)

    
    def focusOutEvent(self, event: QtGui.QFocusEvent|None):
        self._update_text_from_value()
        return super().focusOutEvent(event)
    

    def _update_text_from_value(self):
        if self._blank:
            self.setText('')
        else:
            self.setText(str(self._value))
        QtHelper.indicate_error(self, False)


    def requireReturnPress(self) -> bool:
        return self._require_return_press
    def setRequireReturnPress(self, value: bool):
        self._require_return_press = value
        if self._require_return_press:
            self.setPlaceholderText('Enter value, press return...')
        else:
            self.setPlaceholderText('Enter value...')


    def blank(self) -> bool:
        return self._blank
    def setBlank(self, value: bool):
        self._blank = value
        self._update_text_from_value()


    def value(self) -> SiValue:
        return self._value
    def setValue(self, value: SiValue):
        self._value = value
        self._value.attach(self._on_value_changed_externally)
        self._update_text_from_value()

    
    def _on_escape_pressed(self):
        self._update_text_from_value()

    
    def _on_return_pressed(self):
        if self.isReadOnly() or self._blank or not self._require_return_press:
            return
        
        try:
            if self._require_return_press:
                old_value = self._value.value
                self._value.parse(self.text())
                QtHelper.indicate_error(self, False)
                if self._value == old_value:
                    return
                self.valueChanged.emit()
            else:
                # was already parsed when text was changed
                self._update_text_from_value()
            QtHelper.indicate_error(self, False)
        except:
            QtHelper.indicate_error(self, True)
        self.selectAll()

    
    def _on_text_changed(self):
        if self.isReadOnly() or self._blank:
            return

        try:
            if self._require_return_press:
                # just parse it, so that the error indicator gets updated
                self._value.copy().parse(self.text())
                QtHelper.indicate_error(self, False)
            else:
                old_value = self._value.value
                self._value.parse(self.text())
                QtHelper.indicate_error(self, False)
                if self._value == old_value:
                    return
                self.valueChanged.emit()
        except:
            QtHelper.indicate_error(self, True)



    def _on_value_changed_externally(self, *args, **kwargs):
        self._update_text_from_value()
