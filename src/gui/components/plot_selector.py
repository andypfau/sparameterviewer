from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from ..components.sivalue_edit import SiValueEdit
from lib import AppPaths, PathExt, PhaseUnit, PlotType, YQuantity, PhaseProcessing, SmithNorm, TdResponse, SiRange, SiFormat, SiValue, window_has_argument
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
import math
import numpy as np
import enum
from typing import Callable, Optional, Union



class PlotSelector(QWidget):


    valueChanged = pyqtSignal()


    class SimplifiedY(enum.StrEnum):
        Off = '—'
        Decibels = 'dB'
        Magnitude = 'Magnitude'
        Real = 'Real'
        Imag = 'Imag.'
        RealImag = 'Real + Imag.'
        SmithZ = 'Smith (Z)'
        SmithY = 'Smith (Y)'
        Step = 'Step Resp.'
        Impulse = 'Impulse Resp.'


    class SimplifiedY2(enum.StrEnum):
        Off = '—'
        Phase = 'Phase'
        Unwrap = 'Unwrapped'
        Detrend = 'De-Trend'
        GroupDelay = 'Group Delay'


    class SimplifiedY2(enum.StrEnum):
        Off = '—'
        Phase = 'Phase'
        Unwrap = 'Unwrapped'
        Detrend = 'De-Trend'
        GroupDelay = 'Group Delay'


    TD_MINSIZE_NAMES = {
        0: 'No Padding',
        1024: '1k',
        1024*2: '2k',
        1024*4: '4k',
        1024*8: '8k',
        1024*16: '16k',
        1024*32: '32k',
        1024*64: '64k',
        1024*128: '128k',
        1024*256: '256k',
    }


    WINDOW_NAMES = {
        'boxcar': 'Rectangular (Off)',
        'hann': 'Hann',
        'hamming': 'Hamming',
        'kaiser': 'Kaiser',
        'flattop': 'Flat-Top',
        'blackman': 'Blackman',
        'tukey': 'Tukey',
    }


    def __init__(self, parent = None):
        super().__init__(parent)

        self._plot_type = PlotType.Cartesian
        self._y1 = YQuantity.Decibels
        self._y2 = YQuantity.Off
        self._phase_processing = PhaseProcessing.Off
        self._td_response = TdResponse.StepResponse
        self._smith_norm = SmithNorm.Impedance
        self._phase_unit = PhaseUnit.Degrees
        self._td_z = False
        self._td_window = 'boxcar'
        self._td_window_arg = 0
        self._td_shift = 0
        self._td_minsize = 0
        self._simplified = False
        
        default_spacing, medium_spacing, wide_spacing = 1, 12, 12

        self._ui_simple = QWidget()
        self._ui_simple.setVisible(self._simplified)
        self._ui_simple_y_combo = QComboBox()
        self._ui_simple_y_combo.setStyleSheet('QComboBox QAbstractItemView { min-width: 30ex; }')
        for option in PlotSelector.SimplifiedY:
            self._ui_simple_y_combo.addItem(str(option))
        self._ui_simple_y_combo.currentIndexChanged.connect(self._on_simple_y_changed)
        self._ui_simple_y2_combo = QComboBox()
        self._ui_simple_y2_combo.setStyleSheet('QComboBox QAbstractItemView { min-width: 30ex; }')
        for option in PlotSelector.SimplifiedY2:
            self._ui_simple_y2_combo.addItem(str(option))
        self._ui_simple_y2_combo.currentIndexChanged.connect(self._on_simple_y2_changed)
        self._ui_simplemenu_button = QtHelper.make_toolbutton(self, None, None, icon='toolbar_menu-small.svg', tooltip='Show Plot Menu')
        self._ui_simple.setLayout(QtHelper.layout_h(
            QtHelper.layout_v(
                self._ui_simple_y_combo,
                3,
                self._ui_simple_y2_combo,
                ..., margins=0, spacing=default_spacing
            ),
            QtHelper.layout_v(
                self._ui_simplemenu_button,
                ..., margins=0, spacing=default_spacing
            ),
        ))

        self._ui_advanced = QWidget()
        self._ui_advanced.setVisible(not self._simplified)
        self._ui_cartesian_button = QtHelper.make_toolbutton(self, None, self._on_select_cartesian, icon='plot_cartesian.svg', tooltip='Cartesian Plot', checked=False)
        self._ui_tdr_button = QtHelper.make_toolbutton(self, None, self._on_select_tdr, icon='plot_tdr.svg', tooltip='Cartesian Plot of Time-Domain Transform', checked=False)
        self._ui_smith_button = QtHelper.make_toolbutton(self, None, self._on_select_smith, icon='plot_smith.svg', tooltip='Smith Plot', checked=False)
        self._ui_polar_button = QtHelper.make_toolbutton(self, None, self._on_select_polar, icon='plot_polar.svg', tooltip='Polar Plot', checked=False)
        self._ui_db_button = QtHelper.make_toolbutton(self, None, self._on_select_db, icon='plot_db.svg', tooltip='Plot Decibels (dB) on Y-Axis', checked=False)
        self._ui_mag_button = QtHelper.make_toolbutton(self, None, self._on_select_mag, icon='plot_mag.svg', tooltip='Plot Magnitude on Y-Axis', checked=False)
        self._ui_real_button = QtHelper.make_toolbutton(self, None, self._on_select_re, icon='plot_real.svg', tooltip='Plot Real Part on Y-Axis', checked=False)
        self._ui_imag_button = QtHelper.make_toolbutton(self, None, self._on_select_im, icon='plot_imag.svg', tooltip='Plot Imaginary Part on Y-Axis', checked=False)
        self._ui_phase_button = QtHelper.make_toolbutton(self, None, self._on_select_phase, icon='plot_phase.svg', tooltip='Plot Phase on Y-Axis', checked=False)
        self._ui_gdelay_button = QtHelper.make_toolbutton(self, None, self._on_select_gdelay, icon='plot_gdelay.svg', tooltip='Plot Group Delay on Y-Axis', checked=False)
        self._ui_unwrap_button = QtHelper.make_toolbutton(self, None, self._on_select_unwrap, icon='plot_phase-unwrap.svg', tooltip='Unwrap Phase', checked=False)
        self._ui_detrend_button = QtHelper.make_toolbutton(self, None, self._on_select_detrend, icon='plot_phase-detrend.svg', tooltip='Unwrap and De-Trend Phase', checked=False)
        self._ui_impulse_button = QtHelper.make_toolbutton(self, None, self._on_select_impulse, icon='plot_tdr-impulse.svg', tooltip='Show Impulse Response', checked=False)
        self._ui_step_button = QtHelper.make_toolbutton(self, None, self._on_select_step, icon='plot_tdr-step.svg', tooltip='Show Step Response', checked=False)
        self._ui_impeance_button = QtHelper.make_toolbutton(self, None, self._on_select_z, icon='plot_impedance.svg', tooltip='Show Impedance (Z) Smith Chart', checked=False)
        self._ui_admittance_button = QtHelper.make_toolbutton(self, None, self._on_select_y, icon='plot_admittance.svg', tooltip='Show Admittance (Y) Smith Chart', checked=False)
        self._ui_advancedmenu_button = QtHelper.make_toolbutton(self, None, None, icon='toolbar_menu-small.svg', tooltip='Show Plot Menu')
        self._ui_advanced.setLayout(QtHelper.layout_v(
            QtHelper.layout_h(
                self._ui_cartesian_button, self._ui_tdr_button, self._ui_smith_button, self._ui_polar_button,
                QtHelper.layout_v(self._ui_advancedmenu_button,...,margins=0, spacing=0),
            ..., margins=0, spacing=default_spacing),
            wide_spacing,
            QtHelper.layout_h(
                self._ui_impeance_button, self._ui_admittance_button, self._ui_db_button, self._ui_mag_button, self._ui_real_button, self._ui_imag_button, self._ui_impulse_button, self._ui_step_button, medium_spacing,
            ..., margins=0, spacing=default_spacing),
            QtHelper.layout_h(
                self._ui_phase_button, self._ui_unwrap_button, self._ui_detrend_button, self._ui_gdelay_button,
            ..., margins=0, spacing=default_spacing),
            ..., margins=0, spacing=default_spacing
        ))
        self.setLayout(QtHelper.layout_v(self._ui_simple, self._ui_advanced, margins=0, spacing=0))

        self._menu = QMenu()
        self._ui_degrees_menuitem = QtHelper.add_menuitem(self._menu, 'Phase in Degrees', self._on_phaseunit_change, checkable=True)
        self._menu.addSeparator()
        self._ui_td_window_combo = QComboBox()
        for name in PlotSelector.WINDOW_NAMES.values():
            self._ui_td_window_combo.addItem(name)
        self._ui_td_window_combo.currentTextChanged.connect(self._on_change_td_window)
        self._ui_td_window_menuwidget = QtHelper.add_menu_action(self._menu, QtHelper.layout_widget_h('Window:', self._ui_td_window_combo, ...))
        self._ui_td_window_arg_spinner = QDoubleSpinBox()
        self._ui_td_window_arg_spinner.valueChanged.connect(self._on_change_td_window_arg)
        self._ui_td_window_arg_spinner.setMinimum(-1e3)
        self._ui_td_window_arg_spinner.setMaximum(+1e3)
        self._ui_td_window_arg_menuwidget = QtHelper.add_menu_action(self._menu, QtHelper.layout_widget_h('Window Arg.:', self._ui_td_window_arg_spinner, ...))
        self._ui_td_minsize_combo = QComboBox()
        for name in PlotSelector.TD_MINSIZE_NAMES.values():
            self._ui_td_minsize_combo.addItem(name)
        self._ui_td_minsize_combo.currentTextChanged.connect(self._on_change_td_minsize)
        self._ui_td_minsize_menuwidget = self._ui_td_minsize_menuwidget = QtHelper.add_menu_action(self._menu, QtHelper.layout_widget_h('Min. Size:', self._ui_td_minsize_combo, ...))
        self._ui_td_shift_text = SiValueEdit(self, si=SiValue(0, 's'))
        self._ui_td_shift_text.valueChanged.connect(self._on_change_td_shift)
        self._ui_td_shift_menuwidget = QtHelper.add_menu_action(self._menu, QtHelper.layout_widget_h('Shift:', self._ui_td_shift_text, ...))
        self._ui_tdz_menuitem = QtHelper.add_menuitem(self._menu, 'Convert to Impedance', self._on_change_td_z, checkable=True)
        self._ui_simplemenu_button.setMenu(self._menu)
        self._ui_simplemenu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._ui_advancedmenu_button.setMenu(self._menu)
        self._ui_advancedmenu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self._update_control_values()


    def simplified(self) -> bool:
        return self._simplified
    def setSimplified(self, value: bool):
        if self._simplified == value:
            return
        self._simplified = value
        self._ui_simple.setVisible(self._simplified)
        self._ui_advanced.setVisible(not self._simplified)
        self._update_control_values()
    

    def plotType(self) -> PlotType:
        return self._plot_type
    def setPlotType(self, value: PlotType):
        self._plot_type = value
        self._update_control_values()
    

    def yQuantity(self) -> YQuantity:
        return self._y1
    def setYQuantity(self, value: YQuantity):
        if value in[YQuantity.Phase, YQuantity.GroupDelay]:
            return
        self._y1 = value
        self._update_control_values()
    

    def y2Quantity(self) -> YQuantity:
        return self._y2
    def setY2Quantity(self, value: YQuantity):
        if value in [YQuantity.Decibels, YQuantity.Magnitude, YQuantity.Real, YQuantity.Imag, YQuantity.RealImag]:
            return
        self._y2 = value
        self._update_control_values()
    

    def tdr(self) -> bool:
        return self._tdr
    def setTdr(self, value: bool):
        self._tdr = value
        self._update_control_values()
    

    def tdResponse(self) -> TdResponse:
        return self._td_response
    def setTdResponse(self, value: TdResponse):
        self._td_response = value
        self._update_control_values()
    

    def tdImpedance(self) -> bool:
        return self._td_z
    def setTdImpedance(self, value: bool):
        self._td_z = value
        self._update_control_values()
    

    def tdWindow(self) -> str:
        return self._td_window
    def setTdWindow(self, value: str):
        self._td_window = value
        self._update_control_values()
    

    def tdWindowArg(self) -> float:
        return self._td_window_arg
    def setTdWindowArg(self, value: float):
        self._td_window_arg = value
        self._update_control_values()
    

    def tdShift(self) -> float:
        return self._td_shift
    def setTdShift(self, value: float):
        self._td_shift = value
        self._update_control_values()
    

    def tdMinisize(self) -> int:
        return self._td_minsize
    def setTdMinsize(self, value: int):
        self._td_minsize = value
        self._update_control_values()
    

    def smithNorm(self) -> SmithNorm:
        return self._smith_norm
    def setSmithNorm(self, value: SmithNorm):
        self._smith_norm = value
        self._update_control_values()
    

    def phaseProcessing(self) -> PhaseProcessing:
        return self._phase_processing
    def setPhaseProcessing(self, value: PhaseProcessing):
        self._phase_processing = value
        self._update_control_values()
    

    def phaseUnit(self) -> PhaseUnit:
        if self._simplified:
            return PhaseUnit.Degrees
        return self._phase_unit
    def setPhaseUnit(self, value: PhaseUnit):
        self._phase_unit = value
        self._update_control_values()
    

    def _update_control_enabled(self):
        self._ui_db_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_mag_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_real_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_imag_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_phase_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_gdelay_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_unwrap_button.setVisible(self._plot_type == PlotType.Cartesian and self._y2 == YQuantity.Phase)
        self._ui_detrend_button.setVisible(self._plot_type == PlotType.Cartesian and self._y2 == YQuantity.Phase)
        self._ui_step_button.setVisible(self._plot_type == PlotType.TimeDomain)
        self._ui_impulse_button.setVisible(self._plot_type == PlotType.TimeDomain)
        self._ui_impeance_button.setVisible(self._plot_type == PlotType.Smith)
        self._ui_admittance_button.setVisible(self._plot_type == PlotType.Smith)
        
        self._ui_degrees_menuitem.setEnabled(self._plot_type == PlotType.Cartesian and self._y2 == YQuantity.Phase)
        self._ui_tdz_menuitem.setEnabled(self._plot_type == PlotType.TimeDomain)
        self._ui_td_window_menuwidget.setEnabled(self._plot_type == PlotType.TimeDomain)
        self._ui_td_window_arg_menuwidget.setEnabled(self._plot_type == PlotType.TimeDomain and window_has_argument(self._td_window))
        self._ui_td_minsize_menuwidget.setEnabled(self._plot_type == PlotType.TimeDomain)
        self._ui_td_shift_menuwidget.setEnabled(self._plot_type == PlotType.TimeDomain)


    def _update_control_values(self):
        if self._simplified:
            if self._plot_type == PlotType.Cartesian:
                if self._y1 == YQuantity.Decibels:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Decibels))
                elif self._y1 == YQuantity.Magnitude:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Magnitude))
                elif self._y1 == YQuantity.Real:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Real))
                elif self._y1 == YQuantity.Imag:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Imag))
                elif self._y1 == YQuantity.RealImag:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.RealImag))
                else:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Off))
                if self._y2 == YQuantity.Phase:
                    if self._phase_processing == PhaseProcessing.Off:
                        self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Phase))
                    elif self._phase_processing == PhaseProcessing.Unwrap:
                        self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Unwrap))
                    elif self._phase_processing == PhaseProcessing.UnwrapDetrend:
                        self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Detrend))
                    else:
                        self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))
                elif self._y2 == YQuantity.GroupDelay:
                    self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.GroupDelay))
                else:
                    self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))
            elif self._plot_type == PlotType.TimeDomain:
                if self._td_response == TdResponse.ImpulseResponse:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Impulse))
                else:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Step))
                self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))
            elif self._plot_type == PlotType.Smith:
                if self._smith_norm == SmithNorm.Admittance:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.SmithY))
                else:
                    self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.SmithZ))
                self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))
            else:
                self._ui_simple_y_combo.setCurrentText(str(PlotSelector.SimplifiedY.Off))
                self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))

        else:
            self._ui_cartesian_button.setChecked(self._plot_type == PlotType.Cartesian)
            self._ui_tdr_button.setChecked(self._plot_type == PlotType.TimeDomain)
            self._ui_smith_button.setChecked(self._plot_type == PlotType.Smith)
            self._ui_polar_button.setChecked(self._plot_type == PlotType.Polar)

            self._ui_db_button.setChecked(self._y1 == YQuantity.Decibels)
            self._ui_mag_button.setChecked(self._y1 == YQuantity.Magnitude)
            self._ui_real_button.setChecked(self._y1 == YQuantity.Real or self._y1 == YQuantity.RealImag)
            self._ui_imag_button.setChecked(self._y1 == YQuantity.Imag or self._y1 == YQuantity.RealImag)
            self._ui_phase_button.setChecked(self._y2 == YQuantity.Phase)
            self._ui_gdelay_button.setChecked(self._y2 == YQuantity.GroupDelay)
            self._ui_impulse_button.setChecked(self._td_response == TdResponse.ImpulseResponse)
            self._ui_step_button.setChecked(self._td_response == TdResponse.StepResponse)
            self._ui_impeance_button.setChecked(self._smith_norm == SmithNorm.Impedance)
            self._ui_admittance_button.setChecked(self._smith_norm == SmithNorm.Admittance)
            self._ui_unwrap_button.setChecked(self._phase_processing == PhaseProcessing.Unwrap)
            self._ui_detrend_button.setChecked(self._phase_processing == PhaseProcessing.UnwrapDetrend)

        self._ui_degrees_menuitem.setChecked(self._phase_unit == PhaseUnit.Degrees)
        self._ui_tdz_menuitem.setChecked(self._td_z)
        self._ui_td_window_combo.setCurrentText(PlotSelector.WINDOW_NAMES[self._td_window])
        self._ui_td_window_arg_spinner.setValue(self._td_window_arg)
        self._ui_td_minsize_combo.setCurrentText(PlotSelector.TD_MINSIZE_NAMES[self._td_minsize])
        self._ui_td_shift_text.value().value = self._td_shift

        self._update_control_enabled()


    def _on_select_cartesian(self):
        self._plot_type = PlotType.Cartesian
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_tdr(self):
        self._plot_type = PlotType.TimeDomain
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_smith(self):
        self._plot_type = PlotType.Smith
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_polar(self):
        self._plot_type = PlotType.Polar
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_db(self):
        if self._y1 == YQuantity.Decibels:
            self._y1 = YQuantity.Off
        else:
            self._y1 = YQuantity.Decibels
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_mag(self):
        if self._y1 == YQuantity.Magnitude:
            self._y1 = YQuantity.Off
        else:
            self._y1 = YQuantity.Magnitude
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_re(self):
        if self._y1 == YQuantity.Real:
            self._y1 = YQuantity.Off
        elif self._y1 == YQuantity.Imag:
            self._y1 = YQuantity.RealImag
        elif self._y1 == YQuantity.RealImag:
            self._y1 = YQuantity.Imag
        else:
            self._y1 = YQuantity.Real
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_im(self):
        if self._y1 == YQuantity.Real:
            self._y1 = YQuantity.RealImag
        elif self._y1 == YQuantity.Imag:
            self._y1 = YQuantity.Off
        elif self._y1 == YQuantity.RealImag:
            self._y1 = YQuantity.Real
        else:
            self._y1 = YQuantity.Imag
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_phase(self):
        if self._y2 == YQuantity.Phase:
            self._y2 = YQuantity.Off
        else:
            self._y2 = YQuantity.Phase
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_select_gdelay(self):
        if self._y2 == YQuantity.GroupDelay:
            self._y2 = YQuantity.Off
        else:
            self._y2 = YQuantity.GroupDelay
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_impulse(self):
        self._td_response = TdResponse.ImpulseResponse
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_step(self):
        self._td_response = TdResponse.StepResponse
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_z(self):
        self._smith_norm = SmithNorm.Impedance
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_y(self):
        self._smith_norm = SmithNorm.Admittance
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_unwrap(self):
        if self._phase_processing == PhaseProcessing.Unwrap:
            self._phase_processing = PhaseProcessing.Off
        else:
            self._phase_processing = PhaseProcessing.Unwrap
        self._update_control_values()
        self.valueChanged.emit()


    def _on_select_detrend(self):
        if self._phase_processing == PhaseProcessing.UnwrapDetrend:
            self._phase_processing = PhaseProcessing.Off
        else:
            self._phase_processing = PhaseProcessing.UnwrapDetrend
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_simple_y_changed(self):
        
        enable_2nd = True
        match self._ui_simple_y_combo.currentText():
            case str(PlotSelector.SimplifiedY.Off):
                self._plot_type = PlotType.Cartesian
                self._y1 = YQuantity.Off
            case str(PlotSelector.SimplifiedY.Decibels):
                self._plot_type = PlotType.Cartesian
                self._y1 = YQuantity.Decibels
            case str(PlotSelector.SimplifiedY.Magnitude):
                self._plot_type = PlotType.Cartesian
                self._y1 = YQuantity.Magnitude
            case str(PlotSelector.SimplifiedY.Real):
                self._plot_type = PlotType.Cartesian
                self._y1 = YQuantity.Real
            case str(PlotSelector.SimplifiedY.Imag):
                self._plot_type = PlotType.Cartesian
                self._y1 = YQuantity.Imag
            case str(PlotSelector.SimplifiedY.RealImag):
                self._plot_type = PlotType.Cartesian
                self._y1 = YQuantity.RealImag
            case str(PlotSelector.SimplifiedY.SmithZ):
                self._plot_type = PlotType.Smith
                self._smith_norm = SmithNorm.Impedance
                enable_2nd = False
            case str(PlotSelector.SimplifiedY.SmithY):
                self._plot_type = PlotType.Smith
                self._smith_norm = SmithNorm.Admittance
                enable_2nd = False
            case str(PlotSelector.SimplifiedY.Impulse):
                self._plot_type = PlotType.TimeDomain
                self._td_response = TdResponse.ImpulseResponse
                self._td_z = False
                enable_2nd = False
            case str(PlotSelector.SimplifiedY.Step):
                self._plot_type = PlotType.TimeDomain
                self._td_response = TdResponse.StepResponse
                self._td_z = False
                enable_2nd = False
            case _:
                return
        
        if not enable_2nd:
            self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))
        
        self._update_control_values()
        self.valueChanged.emit()
    

    def _on_simple_y2_changed(self):
        
        enable_2nd = True
        match self._ui_simple_y_combo.currentText():
            case str(PlotSelector.SimplifiedY.SmithZ):
                enable_2nd = False
            case str(PlotSelector.SimplifiedY.SmithY):
                enable_2nd = False
            case str(PlotSelector.SimplifiedY.Impulse):
                enable_2nd = False
            case str(PlotSelector.SimplifiedY.Step):
                enable_2nd = False
        
        if enable_2nd:
            match self._ui_simple_y2_combo.currentText():
                case str(PlotSelector.SimplifiedY2.Off):
                    self._y2 = YQuantity.Off
                case str(PlotSelector.SimplifiedY2.Phase):
                    self._y2 = YQuantity.Phase
                    self._phase_processing = PhaseProcessing.Off
                case str(PlotSelector.SimplifiedY2.Unwrap):
                    self._y2 = YQuantity.Phase
                    self._phase_processing = PhaseProcessing.Unwrap
                case str(PlotSelector.SimplifiedY2.Detrend):
                    self._y2 = YQuantity.Phase
                    self._phase_processing = PhaseProcessing.UnwrapDetrend
                case _:
                    return
        else:
            self._ui_simple_y2_combo.setCurrentText(str(PlotSelector.SimplifiedY2.Off))
        
        self._update_control_values()
        self.valueChanged.emit()


    def _on_phaseunit_change(self):
        self._phase_unit = PhaseUnit.Degrees if self._ui_degrees_menuitem.isChecked() else PhaseUnit.Radians
        
        if self.plotType() != PlotType.Cartesian or self.y2Quantity() != YQuantity.Phase:
            return
        self.valueChanged.emit()
    

    def _on_change_td_z(self):
        self._td_z = self._ui_tdz_menuitem.isChecked()
        if self.plotType() != PlotType.TimeDomain:
            return
        self.valueChanged.emit()
    

    def _on_change_td_window(self):
        for window, name in PlotSelector.WINDOW_NAMES.items():
            if name == self._ui_td_window_combo.currentText():
                self._td_window = window
                break
        self._update_control_enabled()
        if self.plotType() != PlotType.TimeDomain:
            return
        self.valueChanged.emit()
    

    def _on_change_td_window_arg(self):
        self._td_window_arg = self._ui_td_window_arg_spinner.value()
        if self.plotType() != PlotType.TimeDomain:
            return
        self.valueChanged.emit()
    

    def _on_change_td_shift(self):
        self._td_shift = self._ui_td_shift_text.value().value
        if self.plotType() != PlotType.TimeDomain:
            return
        self.valueChanged.emit()
    

    def _on_change_td_minsize(self):
        for minsize, name in PlotSelector.TD_MINSIZE_NAMES.items():
            if name == self._ui_td_minsize_combo.currentText():
                self._td_minsize = minsize
                break
        if self.plotType() != PlotType.TimeDomain:
            return
        self.valueChanged.emit()
