from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths
from lib import parse_si_range, format_si_range

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class RangeEdit(QComboBox):

    rangeChanged = pyqtSignal()

    def __init__(self, parent: QWidget, wildcard_low: any, wildcard_high: any, allow_individual_wildcards: bool, allow_both_wildcards: bool, presets: list[tuple[any,any]]):
        super().__init__(parent)
        self.setPlaceholderText('Enter range...')
        self.setMinimumWidth(150)
        self.setEditable(True)
        self.currentTextChanged.connect(self._on_text_change)

        self._start = any
        self._end = any
        self._wildcard_low = wildcard_low
        self._wildcard_high = wildcard_high
        self._allow_individual_wildcards = allow_individual_wildcards
        self._allow_both_wildcards = allow_both_wildcards
        
        self.clear()
        preset_texts: list[str] = [format_si_range(a,b,allow_both_wildcards) for (a,b) in presets]
        for text in preset_texts:
            self.addItem(text)
        
        if len(preset_texts) >= 1:
            self.setCurrentText(preset_texts[0])
        else:
            self._update_text_from_value()
    

    def _update_text_from_value(self):
        QtHelper.indicate_error(self, False)
        self.setCurrentText(format_si_range(self._start, self._end, self._allow_both_wildcards))


    def range(self) -> tuple[float|any,float|any]:
        return (self._start, self._end)
    def setRange(self, start: float|any, end: float|any):
        self._start, self._end = start, end
        self._update_text_from_value()

    
    def _on_text_change(self):
        try:
            self._start, self._end = parse_si_range(self.currentText(), wildcard_low=self._wildcard_low, wildcard_high=self._wildcard_high, allow_both_wildcards=self._allow_both_wildcards, allow_individual_wildcards=self._allow_individual_wildcards)
            self.rangeChanged.emit()
            QtHelper.indicate_error(self, False)
        except:
            QtHelper.indicate_error(self, True)
