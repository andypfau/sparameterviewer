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



class SettingsTab(enum.IntEnum):
    TimeDomain = 0
    Format = 1
    Misc = 2



class SettingsDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)

        main_layout = QHBoxLayout()
        self._ui_tabs = QTabWidget()
        main_layout.addWidget(self._ui_tabs)
        self.setLayout(main_layout)

        tb_widget = QWidget()
        self._ui_tabs.addTab(tb_widget, 'Time-Domain')
        self._ui_td_window_combo = QComboBox()
        self._ui_td_window_model = QStandardItemModel()
        self._ui_td_window_combo.setModel(self._ui_td_window_model)
        self._ui_td_window_combo.currentTextChanged.connect(self.on_td_window_changed)
        self._ui_td_window_param_spinner = QDoubleSpinBox()
        self._ui_td_window_param_spinner.valueChanged.connect(self.on_td_window_param_changed)
        self._ui_td_minsize_combo = QComboBox()
        self._ui_td_minsize_model = QStandardItemModel()
        self._ui_td_minsize_combo.setModel(self._ui_td_minsize_model)
        self._ui_td_minsize_combo.currentTextChanged.connect(self.on_td_minsize_changed)
        self._ui_td_shift_spinner = QDoubleSpinBox()
        self._ui_td_shift_spinner.valueChanged.connect(self.on_td_shift_changed)
        self._ui_td_z_checkbox = QCheckBox('Convert to Impedance')
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

        format_widget = QWidget()
        self._ui_tabs.addTab(format_widget, 'Format')
        self._ui_deg_radio = QRadioButton('Degrees')
        self._ui_deg_radio.toggled.connect(self.on_phase_unit_change)
        self._ui_rad_radio = QRadioButton('Radians')
        self._ui_rad_radio.toggled.connect(self.on_phase_unit_change)
        self._ui_csvsep_combo = QComboBox()
        self._ui_csvsep_model = QStandardItemModel()
        self._ui_csvsep_combo.setModel(self._ui_csvsep_model)
        self._ui_csvsep_combo.currentIndexChanged.connect(self.on_csvsep_change)
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

        misc_widget = QWidget()
        self._ui_tabs.addTab(misc_widget, 'Misc')
        self._oi_extract_zip_combo = QCheckBox('Extract .zip-Files')
        self._oi_extract_zip_combo.toggled.connect(self.on_zip_change)
        self._oi_comment_expr_combo = QCheckBox('Commend-Out Existing Expressions')
        self._oi_comment_expr_combo.toggled.connect(self.on_comment_change)
        self._ui_exted_edit = QLineEdit()
        self._ui_exted_edit.textChanged.connect(self.on_ext_ed_change)
        self._ui_exted_edit.setMinimumWidth(120)
        self._ui_exted_btn = QtHelper.make_button('...', self.on_browse_ext_ed)
        misc_widget.setLayout(
            QtHelper.layout_v(
                self._oi_extract_zip_combo,
                self._oi_comment_expr_combo,
                QtHelper.layout_grid([
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
    def ui_phase_unit(self) -> str:
        if self._ui_rad_radio.isChecked():
            return 'rad'
        else:
            return 'deg'
    @ui_phase_unit.setter
    def ui_phase_unit(self, value: str):
        if value=='deg':
            self._ui_deg_radio.setChecked(True)
        elif value=='rad':
            self._ui_rad_radio.setChecked(True)

    
    @property
    def ui_td_window(self) -> str:
        return self._ui_td_window_combo.currentText()
    @ui_td_window.setter
    def ui_td_window(self, value: str):
        self._ui_td_window_combo.setCurrentText(value)


    def ui_set_td_window_options(self, options: list[str]):
        self._ui_td_window_model.clear()
        for option in options:
            self._ui_td_window_model.appendRow(QStandardItem(option))

    
    @property
    def ui_td_minsize(self) -> str:
        return self._ui_td_minsize_combo.currentText()
    @ui_td_minsize.setter
    def ui_td_minsize(self, value: str):
        self._ui_td_minsize_combo.setCurrentText(value)


    def ui_set_td_minsize_options(self, options: list[str]):
        self._ui_td_minsize_model.clear()
        for option in options:
            self._ui_td_minsize_model.appendRow(QStandardItem(option))

    
    @property
    def ui_csvsep(self) -> str:
        return self._ui_csvsep_combo.currentText()
    @ui_csvsep.setter
    def ui_csvsep(self, value: str):
        self._ui_csvsep_combo.setCurrentText(value)


    def ui_set_csvset_options(self, options: list[str]):
        self._ui_csvsep_model.clear()
        for option in options:
            self._ui_csvsep_model.appendRow(QStandardItem(option))

    
    @property
    def ui_ext_ed(self) -> str:
        return self._ui_exted_edit.text()
    @ui_ext_ed.setter
    def ui_ext_ed(self, value: str):
        self._ui_exted_edit.setText(value)


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
    def on_zip_change(self):
        pass
    def on_comment_change(self):
        pass
    def on_ext_ed_change(self):
        pass
    def on_browse_ext_ed(self):
        pass
