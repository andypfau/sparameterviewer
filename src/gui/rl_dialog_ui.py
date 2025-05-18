from .helpers.qt_helper import QtHelper
from .components.plot_widget import PlotWidget

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



class RlDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Return Loss Integrator')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        help = QShortcut(QKeySequence('F1'), self)
        help.activated.connect(self.on_help)

        group_file = QGroupBox('File and Port')
        self._ui_file_combo = QComboBox()
        self._ui_file_combo.currentTextChanged.connect(self.on_file_changed)
        self._ui_port_spinner = QSpinBox()
        self._ui_port_spinner.setMinimum(1)
        self._ui_port_spinner.setMaximumWidth(80)
        self._ui_port_spinner.valueChanged.connect(self.on_port_changed)
        group_file.setLayout(QtHelper.layout_h(self._ui_file_combo, 'Port:', self._ui_port_spinner))

        group_freq = QGroupBox('Frequency Ranges')
        self._ui_intrange_combo = QComboBox()
        self._ui_intrange_combo.setEditable(True)
        self._ui_intrange_combo.currentTextChanged.connect(self.on_intrange_changed)
        self._ui_tgtrange_combo = QComboBox()
        self._ui_tgtrange_combo.setEditable(True)
        self._ui_tgtrange_combo.currentTextChanged.connect(self.on_tgtrange_changed)
        group_freq.setLayout(QtHelper.layout_h('Integration:', self._ui_intrange_combo, 'Target:', self._ui_tgtrange_combo))

        group_result = QGroupBox('Result')
        self._ui_result_text = QPlainTextEdit()
        self._ui_result_text.setMinimumSize(400, 80)
        self._ui_result_text.setReadOnly(True)
        self._ui_result_text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self._ui_plot = PlotWidget()
        self._ui_plot.setMinimumSize(400, 300)
        self._ui_cartesian_radio = QRadioButton('Cartesian')
        self._ui_cartesian_radio.toggled.connect(self.on_plottype_changed)
        self._ui_cartesian_radio.setChecked(True)
        self._ui_histogram_radio = QRadioButton('Histogram')
        self._ui_histogram_radio.toggled.connect(self.on_plottype_changed)
        group_result.setLayout(QtHelper.layout_v(
            self._ui_result_text,
            QtHelper.layout_h(self._ui_cartesian_radio, self._ui_histogram_radio, ...),
            self._ui_plot,
        ))

        self.setLayout(QtHelper.layout_v(group_file, group_freq, group_result))
        self.adjustSize()
    

    def ui_show_modal(self):
        self.exec()

    
    def ui_set_files_list(self, files: list[str], selected: str = None):
        self._ui_file_combo.clear()
        for file in files:
            self._ui_file_combo.addItem(file)
        if selected:
            self._ui_file_combo.setCurrentText(selected)

    
    def ui_intrange_presets(self, presets: list[str], selected: str = None):
        self._ui_intrange_combo.clear()
        for preset in presets:
            self._ui_intrange_combo.addItem(preset)
        if selected:
            self._ui_intrange_combo.setCurrentText(selected)

    
    def ui_tgtrange_presets(self, files: list[str], selected: str = None):
        self._ui_tgtrange_combo.clear()
        for file in files:
            self._ui_tgtrange_combo.addItem(file)
        if selected:
            self._ui_tgtrange_combo.setCurrentText(selected)


    @property
    def ui_plot(self) -> PlotWidget:
        return self._ui_plot


    @property
    def ui_port(self) -> int:
        return self._ui_port_spinner.value()
    

    @property
    def ui_file(self) -> str:
        return self._ui_file_combo.currentText()
    

    @property
    def ui_intrange(self) -> str:
        return self._ui_intrange_combo.currentText()
    

    @property
    def ui_tgtrange(self) -> str:
        return self._ui_tgtrange_combo.currentText()


    @property
    def ui_histogram(self) -> bool:
        return self._ui_histogram_radio.isChecked()
    

    def ui_set_result(self, text: str, indicate_error: bool = False):
        self._ui_result_text.setPlainText(text)
        QtHelper.indicate_error(self._ui_result_text, indicate_error)
    

    def ui_inidicate_port_error(self, indicate_error: bool = False):
        QtHelper.indicate_error(self._ui_port_spinner, indicate_error)
    

    def ui_inidicate_intrange_error(self, indicate_error: bool = False):
        QtHelper.indicate_error(self._ui_intrange_combo, indicate_error)
    

    def ui_inidicate_tgtrange_error(self, indicate_error: bool = False):
        QtHelper.indicate_error(self._ui_tgtrange_combo, indicate_error)


    # to be implemented in derived class
    def on_file_changed(self):
        pass
    def on_port_changed(self):
        pass
    def on_intrange_changed(self):
        pass
    def on_tgtrange_changed(self):
        pass
    def on_plottype_changed(self):
        pass
    def on_help(self):
        pass
