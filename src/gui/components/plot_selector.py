from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths, PathExt, PhaseUnit, PlotType, YQuantity, PhaseProcessing, SmithNorm, TdResponse
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
        self._simplified = False
        
        self._ui_simple = QWidget()
        self._ui_simple.setVisible(self._simplified)
        # TODO: implement simplified UI
        self._ui_simple.setLayout(QtHelper.layout_v('Simplified plot selector comes here...'))

        self._ui_advanced = QWidget()
        self._ui_advanced.setVisible(not self._simplified)
        self._ui_cartesian_button = QtHelper.make_button(self, None, self._on_select_cartesian, icon='plot_cartesian.svg', tooltip='Cartesian Plot', toolbar=True, checked=False)
        self._ui_tdr_button = QtHelper.make_button(self, None, self._on_select_tdr, icon='plot_tdr.svg', tooltip='Cartesian Plot of Time-Domain Transform', toolbar=True, checked=False)
        self._ui_smith_button = QtHelper.make_button(self, None, self._on_select_smith, icon='plot_smith.svg', tooltip='Smith Plot', toolbar=True, checked=False)
        self._ui_polar_button = QtHelper.make_button(self, None, self._on_select_polar, icon='plot_polar.svg', tooltip='Polar Plot', toolbar=True, checked=False)
        self._ui_db_button = QtHelper.make_button(self, None, self._on_select_db, icon='plot_db.svg', tooltip='Plot Decibels (dB) on Y-Axis', toolbar=True, checked=False)
        self._ui_mag_button = QtHelper.make_button(self, None, self._on_select_mag, icon='plot_mag.svg', tooltip='Plot Magnitude on Y-Axis', toolbar=True, checked=False)
        self._ui_real_button = QtHelper.make_button(self, None, self._on_select_re, icon='plot_real.svg', tooltip='Plot Real Part on Y-Axis', toolbar=True, checked=False)
        self._ui_imag_button = QtHelper.make_button(self, None, self._on_select_im, icon='plot_imag.svg', tooltip='Plot Imaginary Part on Y-Axis', toolbar=True, checked=False)
        self._ui_phase_button = QtHelper.make_button(self, None, self._on_select_phase, icon='plot_phase.svg', tooltip='Plot Phase on Y-Axis', toolbar=True, checked=False)
        self._ui_gdelay_button = QtHelper.make_button(self, None, self._on_select_gdelay, icon='plot_gdelay.svg', tooltip='Plot Group Delay on Y-Axis', toolbar=True, checked=False)
        self._ui_unwrap_button = QtHelper.make_button(self, None, self._on_select_unwrap, icon='plot_phase-unwrap.svg', tooltip='Unwrap Phase', toolbar=True, checked=False)
        self._ui_detrend_button = QtHelper.make_button(self, None, self._on_select_detrend, icon='plot_phase-detrend.svg', tooltip='Unwrap and De-Trend Phase', toolbar=True, checked=False)
        self._ui_impulse_button = QtHelper.make_button(self, None, self._on_select_impulse, icon='plot_tdr-impulse.svg', tooltip='Show Impulse Response', toolbar=True, checked=False)
        self._ui_step_button = QtHelper.make_button(self, None, self._on_select_step, icon='plot_tdr-step.svg', tooltip='Show Step Response', toolbar=True, checked=False)
        self._ui_impeance_button = QtHelper.make_button(self, None, self._on_select_z, icon='plot_impedance.svg', tooltip='Show Impedance (Z) Smith Chart', toolbar=True, checked=False)
        self._ui_admittance_button = QtHelper.make_button(self, None, self._on_select_y, icon='plot_admittance.svg', tooltip='Show Admittance (Y) Smith Chart', toolbar=True, checked=False)
        self._ui_degrees_button = QtHelper.make_button(self, None, self._on_select_other, icon='plot_degree.svg', tooltip='Plot Phase in Degrees (°) Instad of Radians', toolbar=True, checked=False)
        self._ui_tdz_button = QtHelper.make_button(self, None, self._on_select_other, icon='plot_ohms.svg', tooltip='Transform Y-Axis to Impedance', toolbar=True, checked=False)
        default_spacing, medium_spacing, wide_spacing = 1, 12, 12
        self._ui_advanced.setLayout(QtHelper.layout_v(
            QtHelper.layout_h(
                self._ui_cartesian_button, self._ui_tdr_button, self._ui_smith_button, self._ui_polar_button,
            ..., spacing=default_spacing),
            wide_spacing,
            QtHelper.layout_h(
                self._ui_impeance_button, self._ui_admittance_button, self._ui_db_button, self._ui_mag_button, self._ui_real_button, self._ui_imag_button, self._ui_impulse_button, self._ui_step_button, medium_spacing, self._ui_tdz_button,
            ..., spacing=default_spacing),
            QtHelper.layout_h(
                self._ui_phase_button, self._ui_unwrap_button, self._ui_detrend_button, self._ui_degrees_button, self._ui_gdelay_button,
            ..., spacing=default_spacing),
            ..., spacing=default_spacing
        ))
        self.setContentsMargins(0, 0, 0, 0)
        self._ui_simple.setContentsMargins(0, 0, 0, 0)
        self._ui_advanced.setContentsMargins(0, 0, 0, 0)
        self.setLayout(QtHelper.layout_v(self._ui_simple, self._ui_advanced))

        self._update_controls()
    

    def simplified(self) -> bool:
        return self._simplified
    def setSimplified(self, value: bool):
        self._simplified = value
        self._ui_simple.setVisible(self._simplified)
        self._ui_advanced.setVisible(not self._simplified)
    

    def plotType(self) -> PlotType:
        return self._plot_type
    def setPlotType(self, value: PlotType):
        self._plot_type = value
        self._update_controls()
    

    def yQuantity(self) -> YQuantity:
        return self._y1
    def setYQuantity(self, value: YQuantity):
        if value in[YQuantity.Phase, YQuantity.GroupDelay]:
            return
        self._y1 = value
        self._update_controls()
    

    def y2Quantity(self) -> YQuantity:
        return self._y2
    def setY2Quantity(self, value: YQuantity):
        if value in [YQuantity.Decibels, YQuantity.Magnitude, YQuantity.Real, YQuantity.Imag, YQuantity.RealImag]:
            return
        self._y2 = value
        self._update_controls()
    

    def tdr(self) -> bool:
        return self._tdr
    def setTdr(self, value: bool):
        self._tdr = value
        self._update_controls()
    

    def tdResponse(self) -> TdResponse:
        return self._td_response
    def setTdResponse(self, value: TdResponse):
        self._td_response = value
        self._update_controls()
    

    def tdImpedance(self) -> bool:
        return self._td_z
    def setTdImpedance(self, value: bool):
        self._td_z = value
        self._update_controls()
    

    def smithNorm(self) -> SmithNorm:
        return self._smith_norm
    def setSmithNorm(self, value: SmithNorm):
        self._smith_norm = value
        self._update_controls()
    

    def phaseProcessing(self) -> PhaseProcessing:
        return self._phase_processing
    def setPhaseProcessing(self, value: PhaseProcessing):
        self._phase_processing = value
        self._update_controls()
    

    def phaseUnit(self) -> PhaseUnit:
        return self._phase_unit
    def setPhaseUnit(self, value: PhaseUnit):
        self._phase_unit = value
        self._update_controls()
    

    def _update_controls(self):
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
        self._ui_degrees_button.setChecked(self._phase_unit == PhaseUnit.Degrees)
        self._ui_impeance_button.setChecked(self._smith_norm == SmithNorm.Impedance)
        self._ui_admittance_button.setChecked(self._smith_norm == SmithNorm.Admittance)
        self._ui_tdz_button.setChecked(self._td_z)
        self._ui_unwrap_button.setChecked(self._phase_processing == PhaseProcessing.Unwrap)
        self._ui_detrend_button.setChecked(self._phase_processing == PhaseProcessing.UnwrapDetrend)

        self._ui_db_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_mag_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_real_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_imag_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_phase_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_gdelay_button.setVisible(self._plot_type == PlotType.Cartesian)
        self._ui_unwrap_button.setVisible(self._plot_type == PlotType.Cartesian and self._y2 == YQuantity.Phase)
        self._ui_detrend_button.setVisible(self._plot_type == PlotType.Cartesian and self._y2 == YQuantity.Phase)
        self._ui_degrees_button.setVisible(self._plot_type == PlotType.Cartesian and self._y2 == YQuantity.Phase)
        self._ui_step_button.setVisible(self._plot_type == PlotType.TimeDomain)
        self._ui_impulse_button.setVisible(self._plot_type == PlotType.TimeDomain)
        self._ui_tdz_button.setVisible(self._plot_type == PlotType.TimeDomain)
        self._ui_impeance_button.setVisible(self._plot_type == PlotType.Smith)
        self._ui_admittance_button.setVisible(self._plot_type == PlotType.Smith)
    

    def _on_select_cartesian(self):
        self._plot_type = PlotType.Cartesian
        self._update_controls()
        self.valueChanged.emit()
    

    def _on_select_tdr(self):
        self._plot_type = PlotType.TimeDomain
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_smith(self):
        self._plot_type = PlotType.Smith
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_polar(self):
        self._plot_type = PlotType.Polar
        self._update_controls()
        self.valueChanged.emit()
    

    def _on_select_db(self):
        if self._y1 == YQuantity.Decibels:
            self._y1 = YQuantity.Off
        else:
            self._y1 = YQuantity.Decibels
        self._update_controls()
        self.valueChanged.emit()
    

    def _on_select_mag(self):
        if self._y1 == YQuantity.Magnitude:
            self._y1 = YQuantity.Off
        else:
            self._y1 = YQuantity.Magnitude
        self._update_controls()
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
        self._update_controls()
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
        self._update_controls()
        self.valueChanged.emit()
    

    def _on_select_phase(self):
        if self._y2 == YQuantity.Phase:
            self._y2 = YQuantity.Off
        else:
            self._y2 = YQuantity.Phase
        self._update_controls()
        self.valueChanged.emit()
    

    def _on_select_gdelay(self):
        if self._y2 == YQuantity.GroupDelay:
            self._y2 = YQuantity.Off
        else:
            self._y2 = YQuantity.GroupDelay
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_impulse(self):
        self._td_response = TdResponse.ImpulseResponse
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_step(self):
        self._td_response = TdResponse.StepResponse
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_z(self):
        self._smith_norm = SmithNorm.Impedance
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_y(self):
        self._smith_norm = SmithNorm.Admittance
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_unwrap(self):
        if self._phase_processing == PhaseProcessing.Unwrap:
            self._phase_processing = PhaseProcessing.Off
        else:
            self._phase_processing = PhaseProcessing.Unwrap
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_detrend(self):
        if self._phase_processing == PhaseProcessing.UnwrapDetrend:
            self._phase_processing = PhaseProcessing.Off
        else:
            self._phase_processing = PhaseProcessing.UnwrapDetrend
        self._update_controls()
        self.valueChanged.emit()


    def _on_select_other(self):
        self._phase_unit = PhaseUnit.Degrees if self._ui_degrees_button.isChecked() else PhaseUnit.Radians
        self._td_z = self._ui_tdz_button.isChecked()
        self._update_controls()
        self.valueChanged.emit()