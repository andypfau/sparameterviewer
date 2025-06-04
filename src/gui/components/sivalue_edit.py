from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths, SiValue, SiFormat, Lock

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class SiValueEdit(QLineEdit):

    valueChanged = pyqtSignal()

    def __init__(self, parent: QWidget = None, si: SiValue = None):
        super().__init__(parent)
        self.setMinimumWidth(150)
        self._value: SiValue = si or SiValue(0)
        self._blank = False
        self._event_lock = Lock(initially_locked=True)
        self._edit_in_progress = False
        
        self.setPlaceholderText('Enter value...')
        
        self._value.attach(self._on_value_changed_externally)
        self._update_text_from_value()
        
        self.textChanged.connect(self._on_text_changed)
        
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
            if self._blank:
                self.setText('')
            else:
                self.setText(str(self._value))
            QtHelper.indicate_error(self, False)


    def blank(self) -> bool:
        return self._blank
    def setBlank(self, value: bool):
        self._blank = value
        if self.hasFocus() and self._edit_in_progress:
            return  # user is entering text -> do not overwrite user-input
        self._update_text_from_value()


    def value(self) -> SiValue:
        return self._value
    def setValue(self, value: SiValue):
        self._value = value
        self._value.attach(self._on_value_changed_externally)
        if self.hasFocus() and self._edit_in_progress:
            return  # user is entering text -> do not overwrite user-input
        self._update_text_from_value()

    
    def _on_escape_pressed(self):
        self._edit_in_progress = False
        self._update_text_from_value()

    
    def _on_return_pressed(self):
        self._edit_in_progress = False
        if self.isReadOnly():
            return
        
        # was already parsed when text was changed
        self._update_text_from_value()
        self.selectAll()

    
    def _on_text_changed(self):
        if self.isReadOnly():
            return

        try:
            old_value = self._value.value
            self._value.parse(self.text())
            QtHelper.indicate_error(self, False)
            if self._value == old_value:
                return
            if not self._event_lock.locked:
                self.valueChanged.emit()
        except:
            QtHelper.indicate_error(self, True)



    def _on_value_changed_externally(self, *args, **kwargs):
        if self.hasFocus() and self._edit_in_progress:
            return  # user is entering text -> do not overwrite user-input
        self._update_text_from_value()
