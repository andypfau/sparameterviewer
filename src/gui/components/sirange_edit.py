from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths
from lib import SiFormat, SiRange

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class SiRangeEdit(QComboBox):

    rangeChanged = pyqtSignal()

    def __init__(self, parent: QWidget, range: SiRange, presets: list[tuple[any,any]], require_return_press: bool = False):
        super().__init__(parent)
        self._require_return_press = require_return_press
        
        self.setPlaceholderText('Enter range...')
        self.setMinimumWidth(150)
        self.setEditable(True)
        self.currentTextChanged.connect(self._on_text_change)

        self._range = range
        self._range.attach(self._on_range_changed_externally)
        
        self.clear()
        preset_texts = [self._range.reconstruct(low,high).format() for (low,high) in presets]
        for text in preset_texts:
            self.addItem(text)
        
        if len(preset_texts) >= 1:
            self.setCurrentText(preset_texts[0])
        else:
            self._update_text_from_value()
    

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
        QtHelper.indicate_error(self, False)
        self.setCurrentText(self._range.format())


    def requireReturnPress(self) -> bool:
        return self._require_return_press
    def setRequireReturnPress(self, value: bool):
        self._require_return_press = value
        if self._require_return_press:
            self.setPlaceholderText('Enter value, press return...')
        else:
            self.setPlaceholderText('Enter value...')
            
    
    def range(self) -> SiRange:
        return self._range
    def setRange(self, value: SiRange):
        self._range = value
        self._range.attach(self._on_range_changed_externally)
        self._update_text_from_value()
        QtHelper.indicate_error(self, False)

    
    def _on_escape_pressed(self):
        self._update_text_from_value()
        QtHelper.indicate_error(self, False)

    
    def _on_return_pressed(self):
        try:
            if self._require_return_press:
                self._range.parse(self.currentText())
                self._update_text_from_value()
                self.rangeChanged.emit()
            else:
                # was already parsed when text was changed
                self._update_text_from_value()
        except:
            QtHelper.indicate_error(self, True)
        self.lineEdit().selectAll()

    
    def _on_text_change(self):
        try:
            if self._require_return_press:
                # just parse it, so that the error indicator gets updated
                self._range.copy().parse(self.currentText())
                QtHelper.indicate_error(self, False)
            else:
                self._range.parse(self.currentText())
                QtHelper.indicate_error(self, False)
                self.rangeChanged.emit()
        except:
            QtHelper.indicate_error(self, True)


    def _on_range_changed_externally(self, *args, **kwargs):
        self._update_text_from_value()
