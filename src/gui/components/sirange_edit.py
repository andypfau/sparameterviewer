from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths, SiFormat, SiRange, Lock

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class SiRangeEdit(QComboBox):

    rangeChanged = pyqtSignal()

    def __init__(self, parent: QWidget, range: SiRange, presets: list[tuple[any,any]]):
        super().__init__(parent)
        self._event_lock = Lock(initially_locked=True)
        self._edit_in_progress = False
        
        self.setPlaceholderText('Enter range...')
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
        
        self._event_lock.force_unlock()
    

    def keyPressEvent(self, event: QtGui.QKeyEvent|None):
        self._edit_in_progress = True
        if event:
            if event.key() == Qt.Key.Key_Escape:
                self._on_escape_pressed()
            elif event.key() == Qt.Key.Key_Return:
                self._on_return_pressed()
        return super().keyPressEvent(event)

    
    def focusOutEvent(self, event: QtGui.QFocusEvent|None):
        self._edit_in_progress = False
        self._update_text_from_value()
        return super().focusOutEvent(event)
    

    def _update_text_from_value(self):
        with self._event_lock:
            self.setCurrentText(self._range.format())
            QtHelper.indicate_error(self, False)
            
    
    def range(self) -> SiRange:
        return self._range
    def setRange(self, value: SiRange):
        self._range = value
        self._range.attach(self._on_range_changed_externally)
        if self.hasFocus() and self._edit_in_progress:
            return  # user is entering text -> do not overwrite user-input
        self._update_text_from_value()

    
    def _on_escape_pressed(self):
        self._edit_in_progress = False
        self._update_text_from_value()

    
    def _on_return_pressed(self):
        # was already parsed when text was changed
        self._edit_in_progress = False
        self._update_text_from_value()
        self.lineEdit().selectAll()

    
    def _on_text_change(self):
        try:
            old_low, old_high = self._range.low, self._range.high
            self._range.parse(self.currentText())
            QtHelper.indicate_error(self, False)
            if self._range.low == old_low and self._range.high == old_high:
                return
            if not self._event_lock.locked:
                self.rangeChanged.emit()
        except:
            QtHelper.indicate_error(self, True)


    def _on_range_changed_externally(self, *args, **kwargs):
        if self.hasFocus() and self._edit_in_progress:
            return  # user is entering text -> do not overwrite user-input
        self._update_text_from_value()
