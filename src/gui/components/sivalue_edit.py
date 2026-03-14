from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths, SiValue, SiFormat, Lock

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import math



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
            elif event.key() == Qt.Key.Key_Up:
                self._on_scroll_event(+1)
                return  # no further handling of this keystroke
            elif event.key() == Qt.Key.Key_Down:
                self._on_scroll_event(-1)
                return  # no further handling of this keystroke
        return super().keyPressEvent(event)

    
    def focusOutEvent(self, event: QtGui.QFocusEvent|None):
        self._edit_in_progress = False
        self._update_text_from_value()
        return super().focusOutEvent(event)
    
    
    def wheelEvent(self, event: QtGui.QWheelEvent):
        self._on_scroll_event(1 if event.angleDelta().y() > 0 else -1)
    

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
    

    def _on_scroll_event(self, direction: int):
        assert direction in [-1, 0, +1]

        MIN_DELTA = 1e-15  # one femto

        value = self._value.value
        
        if value == 0:
            new_value = MIN_DELTA * direction

        else:
            lowest_digit_exponent = 10**math.floor(math.log10(abs(value)))

            if direction < 0 and value > 0 and value - lowest_digit_exponent < MIN_DELTA:
                new_value = 0
            elif direction > 0 and value < 0 and value + lowest_digit_exponent > -MIN_DELTA:
                new_value = 0
            else:
                new_value = value + lowest_digit_exponent * direction
        
        self._value.value = new_value
        if not self._event_lock.locked:
            self.valueChanged.emit()
        QtHelper.indicate_error(self, False)
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
