from .helpers.qt_helper import QtHelper
from lib.utils import get_next_1_10_100, get_next_1_2_5_10
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
import numpy as np



class SettingsTab(enum.IntEnum):
    Format = 0
    TimeDomain = 1
    Misc = 2



class SettingsDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)

        self._warncount_list_values = [10]
        while self._warncount_list_values[-1] < 1_000_000:
            self._warncount_list_values.append(get_next_1_10_100(self._warncount_list_values[-1]))
        self._warncount_load_values = [5]
        while self._warncount_load_values[-1] < 1_000_000:
            self._warncount_load_values.append(get_next_1_2_5_10(self._warncount_load_values[-1]))

        help = QShortcut(QKeySequence('F1'), self)
        help.activated.connect(self.on_help)

        main_layout = QHBoxLayout()
        self._ui_tabs = QTabWidget()
        main_layout.addWidget(self._ui_tabs)
        self.setLayout(main_layout)

        format_widget = QWidget()
        self._ui_tabs.addTab(format_widget, 'Formats')
        self._ui_deg_radio = QRadioButton('Degrees')
        self._ui_deg_radio.toggled.connect(self.on_phase_unit_change)
        self._ui_rad_radio = QRadioButton('Radians')
        self._ui_rad_radio.toggled.connect(self.on_phase_unit_change)
        self._ui_csvsep_combo = QComboBox()
        format_widget.setLayout(
            QtHelper.layout_v(
                QtHelper.layout_h(
                    QtHelper.layout_grid([
                            ['Phase:', QtHelper.layout_h(self._ui_deg_radio, self._ui_rad_radio, ...)],
                            ['CSV Separator:', QtHelper.layout_h(self._ui_csvsep_combo, ...)],
                    ]), ...
                ), ...
            )
        )

        tb_widget = QWidget()
        self._ui_tabs.addTab(tb_widget, 'Time-Domain')
        self._ui_td_window_combo = QComboBox()
        self._ui_td_window_param_spinner = QDoubleSpinBox()
        self._ui_td_window_param_spinner.valueChanged.connect(self.on_td_window_param_changed)
        self._ui_td_window_param_spinner.setMinimum(-1e3)
        self._ui_td_window_param_spinner.setMaximum(+1e3)
        self._ui_td_minsize_combo = QComboBox()
        self._ui_td_shift_spinner = QDoubleSpinBox()
        self._ui_td_shift_spinner.setMinimum(-1e9)
        self._ui_td_shift_spinner.setMaximum(+1e9)
        self._ui_td_shift_spinner.valueChanged.connect(self.on_td_shift_changed)
        self._ui_td_z_checkbox = QCheckBox('Convert to Impedance')
        self._ui_td_z_checkbox.toggled.connect(self.on_td_z_changed)
        tb_widget.setLayout(
            QtHelper.layout_v(
                QtHelper.layout_h(
                    QtHelper.layout_grid([
                        ['Window:', QtHelper.layout_h(self._ui_td_window_combo, ...)],
                        ['Parameter:', QtHelper.layout_h(self._ui_td_window_param_spinner, ...)],
                        ['Min. Size:', QtHelper.layout_h(self._ui_td_minsize_combo, ...)],
                        ['Shift:', QtHelper.layout_h(self._ui_td_shift_spinner, 'ps', ...)],
                        [None, QtHelper.layout_h(self._ui_td_z_checkbox, ...)],
                    ]), ...
                ), ...
            )
        )

        files_widget = QWidget()
        self._ui_tabs.addTab(files_widget, 'Files')
        self._ui_extract_zip_check = QCheckBox('Extract .zip-Files')
        self._ui_extract_zip_check.toggled.connect(self.on_zip_change)
        self._ui_warncount_list_combo = QComboBox()
        for i in self._warncount_list_values:
            self._ui_warncount_list_combo.addItem(f'{i:,.0f}')
        self._ui_warncount_list_combo.currentIndexChanged.connect(self._on_warncount_list_changed)
        self._ui_warncount_list_combo.setCurrentIndex(0)
        self._ui_warncount_load_combo = QComboBox()
        for i in self._warncount_load_values:
            self._ui_warncount_load_combo.addItem(f'{i:,.0f}')
        self._ui_warncount_load_combo.setCurrentIndex(0)
        self._ui_warncount_load_combo.currentIndexChanged.connect(self._on_warncount_load_changed)
        files_widget.setLayout(
            QtHelper.layout_v(
                self._ui_extract_zip_check,
                QtHelper.layout_h('Warn When Discovering More Than', self._ui_warncount_list_combo, 'Files'),
                QtHelper.layout_h('Warn When Loading More Than', self._ui_warncount_load_combo, 'Files'),
                ...
            )
        )

        misc_widget = QWidget()
        self._ui_tabs.addTab(misc_widget, 'Misc')
        self._ui_comment_expr_combo = QCheckBox('Commend-Out Existing Expressions')
        self._ui_comment_expr_combo.toggled.connect(self.on_comment_change)
        self._ui_cursor_snap = QComboBox()
        self._ui_plot_style_combo = QComboBox()
        self._ui_plot_style_combo.setMinimumWidth(150)
        self._ui_font_combo = QComboBox()
        self._ui_font_combo.setMinimumWidth(250)
        self._ui_exted_edit = QLineEdit()
        self._ui_exted_edit.textChanged.connect(self.on_ext_ed_change)
        self._ui_exted_edit.setMinimumWidth(120)
        self._ui_exted_btn = QtHelper.make_button('...', self.on_browse_ext_ed)
        misc_widget.setLayout(
            QtHelper.layout_v(
                self._ui_comment_expr_combo,
                QtHelper.layout_grid([
                        ['Cursor Snap:', QtHelper.layout_h(self._ui_cursor_snap, ...)],
                        ['Plot Style:', QtHelper.layout_h(self._ui_plot_style_combo, '(requires restart)')],
                        ['Editor Font:', QtHelper.layout_h(self._ui_font_combo)],
                        ['External Editor:', QtHelper.layout_h(self._ui_exted_edit, self._ui_exted_btn)],
                ]), ...
            )
        )

        self.adjustSize()
    

    def ui_select_tab(self, tab: SettingsTab):
        self._ui_tabs.setCurrentIndex(int(tab))
    

    def ui_show_modal(self):
        self.exec()

    
    @property
    def ui_radians(self) -> bool:
        return self._ui_rad_radio.isChecked()
    @ui_radians.setter
    def ui_radians(self, radians: bool):
        if radians:
            self._ui_rad_radio.setChecked(True)
        else:
            self._ui_deg_radio.setChecked(True)

    
    @property
    def ui_td_window(self) -> str:
        return self._ui_td_window_combo.currentText()
    @ui_td_window.setter
    def ui_td_window(self, value: str):
        self._ui_td_window_combo.setCurrentText(value)


    def ui_set_td_window_options(self, options: list[str]):
        self._ui_td_window_combo.clear()
        for option in options:
            self._ui_td_window_combo.addItem(option)
        self._ui_td_window_combo.currentIndexChanged.connect(self.on_td_window_changed)

    
    @property
    def ui_td_window_param(self) -> float:
        return self._ui_td_window_param_spinner.value()
    @ui_td_window_param.setter
    def ui_td_window_param(self, value: float):
        self._ui_td_window_param_spinner.setValue(value)

    
    @property
    def ui_td_minsize(self) -> str:
        return self._ui_td_minsize_combo.currentText()
    @ui_td_minsize.setter
    def ui_td_minsize(self, value: str):
        self._ui_td_minsize_combo.setCurrentText(value)

    
    @property
    def ui_td_shift(self) -> float:
        return self._ui_td_shift_spinner.value() * 1e-12
    @ui_td_shift.setter
    def ui_td_shift(self, value: float):
        self._ui_td_shift_spinner.setValue(value / 1e-12)

    
    @property
    def ui_td_z(self) -> bool:
        return self._ui_td_z_checkbox.isChecked()
    @ui_td_z.setter
    def ui_td_z(self, value: bool):
        self._ui_td_z_checkbox.setChecked(value)


    def ui_set_td_minsize_options(self, options: list[str]):
        self._ui_td_minsize_combo.clear()
        for option in options:
            self._ui_td_minsize_combo.addItem(option)
        self._ui_td_minsize_combo.currentIndexChanged.connect(self.on_td_minsize_changed)

    
    @property
    def ui_csvsep(self) -> str:
        return self._ui_csvsep_combo.currentText()
    @ui_csvsep.setter
    def ui_csvsep(self, value: str):
        self._ui_csvsep_combo.setCurrentText(value)


    def ui_set_csvset_options(self, options: list[str]):
        self._ui_csvsep_combo.clear()
        for option in options:
            self._ui_csvsep_combo.addItem(option)
        self._ui_csvsep_combo.currentIndexChanged.connect(self.on_csvsep_change)


    def ui_set_plotstysle_options(self, options: list[str]):
        self._ui_plot_style_combo.clear()
        for option in options:
            self._ui_plot_style_combo.addItem(option)
        self._ui_plot_style_combo.currentIndexChanged.connect(self.on_plotstyle_change)


    def ui_set_font_options(self, options: list[str]):
        self._ui_font_combo.clear()
        for option in options:
            self._ui_font_combo.addItem(option)
        self._ui_font_combo.currentIndexChanged.connect(self.on_font_change)

    
    @property
    def ui_cursor_snap(self) -> str:
        return self._ui_cursor_snap.currentText()
    @ui_cursor_snap.setter
    def ui_cursor_snap(self, value: str):
        self._ui_cursor_snap.setCurrentText(value)


    def ui_set_cursor_snap_options(self, options: list[str]):
        self._ui_cursor_snap.clear()
        for option in options:
            self._ui_cursor_snap.addItem(option)
        self._ui_cursor_snap.currentIndexChanged.connect(self.on_cursor_snap_changed)

    
    @property
    def ui_comment_expr(self) -> bool:
        return self._ui_comment_expr_combo.isChecked()
    @ui_comment_expr.setter
    def ui_comment_expr(self, value: bool):
        self._ui_comment_expr_combo.setChecked(value)

    
    @property
    def ui_extract_zip(self) -> bool:
        return self._ui_extract_zip_check.isChecked()
    @ui_extract_zip.setter
    def ui_extract_zip(self, value: bool):
        self._ui_extract_zip_check.setChecked(value)

    
    @property
    def ui_ext_ed(self) -> str:
        return self._ui_exted_edit.text()
    @ui_ext_ed.setter
    def ui_ext_ed(self, value: str):
        self._ui_exted_edit.setText(value)

    
    @property
    def ui_plotstyle(self) -> bool:
        return self._ui_plot_style_combo.currentText()
    @ui_plotstyle.setter
    def ui_plotstyle(self, value: bool):
        self._ui_plot_style_combo.setCurrentText(value)

    
    @property
    def ui_font(self) -> bool:
        return self._ui_font_combo.currentText()
    @ui_font.setter
    def ui_font(self, value: bool):
        self._ui_font_combo.setCurrentText(value)

    
    @property
    def ui_warncount_list(self) -> int:
        try:
            return self._warncount_list_values[self._ui_warncount_list_combo.currentIndex()]
        except:
            return self._warncount_list_values[0]
    @ui_warncount_list.setter
    def ui_warncount_list(self, value: int):
        try:
            idx = np.argmin(np.abs(np.array(self._warncount_list_values) - value))
            self._ui_warncount_list_combo.setCurrentIndex(idx)
        except: pass

    
    @property
    def ui_warncount_load(self) -> int:
        try:
            return self._warncount_load_values[self._ui_warncount_load_combo.currentIndex()]
        except:
            return self._warncount_load_values[0]
    @ui_warncount_load.setter
    def ui_warncount_load(self, value: int):
        try:
            idx = np.argmin(np.abs(np.array(self._warncount_load_values) - value))
            self._ui_warncount_load_combo.setCurrentIndex(idx)
        except: pass


    def ui_indicate_ext_ed_error(self, indicate_error: bool):
        QtHelper.indicate_error(self._ui_exted_edit, indicate_error)

    
    # to be implemented in derived class
    def on_phase_unit_change(self):
        pass
    def on_csvsep_change(self):
        pass
    def on_td_window_changed(self):
        pass
    def on_td_window_param_changed(self):
        pass
    def on_td_minsize_changed(self):
        pass
    def on_td_shift_changed(self):
        pass
    def on_td_z_changed(self):
        pass
    def on_zip_change(self):
        pass
    def on_comment_change(self):
        pass
    def on_ext_ed_change(self):
        pass
    def on_browse_ext_ed(self):
        pass
    def on_help(self):
        pass
    def on_plotstyle_change(self):
        pass
    def on_font_change(self):
        pass
    def on_cursor_snap_changed(self):
        pass
    def _on_warncount_list_changed(self):
        pass
    def _on_warncount_load_changed(self):
        pass
