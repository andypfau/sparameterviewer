from .qt_helper import QtHelper
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
from typing import Callable, Union



class CursorDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Trace Cursors')
        QtHelper.set_dialog_icon(self)
        self.setSizeGripEnabled(True)

        help = QShortcut(QKeySequence('F1'), self)
        help.activated.connect(self.on_help)

        option_group = QGroupBox('Selection')
        self._ui_cursor1_radio = QRadioButton('Cursor 1')
        self._ui_cursor1_radio.toggled.connect(self.on_cursor_select)
        self._ui_cursor2_radio = QRadioButton('Cursor 2')
        self._ui_cursor2_radio.toggled.connect(self.on_cursor_select)
        self._ui_trace1_combo = QComboBox()
        self._ui_trace1_combo.currentIndexChanged.connect(self.on_trace1_change)
        self._ui_trace2_combo = QComboBox()
        self._ui_trace2_combo.currentIndexChanged.connect(self.on_trace2_change)
        self._ui_auto_cursor_check = QCheckBox('Auto Cursor')
        self._ui_auto_cursor_check.toggled.connect(self.on_auto_cursor_changed)
        self._ui_auto_trace_check = QCheckBox('Auto Trace')
        self._ui_auto_trace_check.toggled.connect(self.on_auto_trace_changed)
        self._ui_syncx_check = QCheckBox('Sync X')
        self._ui_syncx_check.toggled.connect(self.on_syncx_changed)

        readout_group= QGroupBox('Readout')
        self._ui_result_text = QPlainTextEdit()
        self._ui_result_text.setMinimumSize(400, 100)
        self._ui_result_text.setReadOnly(True)
        self._ui_result_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        option_group.setLayout(QtHelper.layout_grid([
            [self._ui_cursor1_radio, self._ui_trace1_combo],
            [self._ui_cursor2_radio, self._ui_trace2_combo],
            [self._ui_auto_cursor_check, self._ui_auto_trace_check, self._ui_syncx_check],
        ]))

        readout_group.setLayout(QtHelper.layout_v(
            self._ui_result_text
        ))

        self.setLayout(QtHelper.layout_v(
            option_group,
            readout_group
        ))

        self.resize(500, 400)
    

    def ui_set_trace_list(self, traces: list[str]):
        for combo in [self._ui_trace1_combo, self._ui_trace2_combo]:
            combo.clear()
            for trace in traces:
                combo.addItem(trace)
    

    def ui_set_readout(self, text: str):
        self._ui_result_text.setPlainText(text)

    
    @property
    def ui_cursor(self) -> int:
        return 2 if self._ui_cursor1_radio.isChecked() else 1
    @ui_cursor.setter
    def ui_cursor(self, value: int):
        if value == 1:
            self._ui_cursor1_radio.setChecked(True)
        elif value == 2:
            self._ui_cursor2_radio.setChecked(True)

    
    @property
    def ui_trace1(self) -> str:
        return self._ui_trace1_combo.currentText()
    @ui_trace1.setter
    def ui_trace1(self, value: int):
        self._ui_trace1_combo.setCurrentText(value)

    
    @property
    def ui_trace2(self) -> str:
        return self._ui_trace2_combo.currentText()
    @ui_trace2.setter
    def ui_trace2(self, value: int):
        self._ui_trace2_combo.setCurrentText(value)

    
    @property
    def ui_auto_cursor(self) -> int:
        return self._ui_auto_cursor_check.isChecked()
    @ui_auto_cursor.setter
    def ui_auto_cursor(self, value: int):
        self._ui_auto_cursor_check.setChecked(value)

    
    @property
    def ui_auto_trace(self) -> int:
        return self._ui_auto_trace_check.isChecked()
    @ui_auto_trace.setter
    def ui_auto_trace(self, value: int):
        self._ui_auto_trace_check.setChecked(value)

    
    @property
    def ui_syncx(self) -> int:
        return self._ui_syncx_check.isChecked()
    @ui_syncx.setter
    def ui_syncx(self, value: int):
        self._ui_syncx_check.setChecked(value)
    

    def ui_show(self):
        self.show()


    # to be implemented in derived class
    def on_cursor_select(self):
        pass
    def on_cursor_select(self):
        pass
    def on_trace1_change(self):
        pass
    def on_trace2_change(self):
        pass
    def on_auto_cursor_changed(self):
        pass
    def on_auto_trace_changed(self):
        pass
    def on_syncx_changed(self):
        pass
    def on_help(self):
        pass
