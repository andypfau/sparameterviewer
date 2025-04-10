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

        main_layout = QHBoxLayout()
        self._ui_tabs = QTabWidget()
        main_layout.addWidget(self._ui_tabs)
        self.setLayout(main_layout)

        tb_widget = QWidget()
        self._ui_tabs.addTab(tb_widget, 'Time-Domaain')
        td_grid = QGridLayout()
        tb_widget.setLayout(td_grid)
        td_grid.addWidget(QtHelper.make_label('Window:'), 0, 0)
        self._ui_td_window_combo = QComboBox()
        td_grid.addWidget(self._ui_td_window_combo, 0, 1)
        td_grid.addWidget(QtHelper.make_label('Parameter:'), 1, 0)
        self._ui_td_window_param_spinner = QDoubleSpinBox()
        td_grid.addWidget(self._ui_td_window_param_spinner, 1, 1)
        td_grid.addWidget(QtHelper.make_label('Min. Size:'), 2, 0)
        self._ui_td_minsize_combo = QComboBox()
        td_grid.addWidget(self._ui_td_minsize_combo, 2, 1)
        td_grid.addWidget(QtHelper.make_label('Shift:'), 3, 0)
        layout_td_shift = QHBoxLayout()
        layout_td_shift_widget = QWidget()
        layout_td_shift_widget.setLayout(layout_td_shift)
        td_grid.addWidget(layout_td_shift_widget, 3, 1)
        self._ui_td_shift_spinner = QDoubleSpinBox()
        layout_td_shift.addWidget(self._ui_td_shift_spinner)
        layout_td_shift.addWidget(QtHelper.make_label('ps'))
        self._ui_td_z_checkbox = QCheckBox('Convert to Impedance')
        td_grid.addWidget(self._ui_td_z_checkbox, 4, 1)

        format_widget = QWidget()
        self._ui_tabs.addTab(format_widget, 'Format')
        fmt_grid = QGridLayout()
        format_widget.setLayout(fmt_grid)
        fmt_grid.addWidget(QtHelper.make_label('Phase:'), 0, 0)
        layout_fmt_phase = QHBoxLayout()
        layout_fmt_phase_widget = QWidget()
        layout_fmt_phase_widget.setLayout(layout_fmt_phase)
        fmt_grid.addWidget(layout_fmt_phase_widget, 0, 1)
        self._ui_deg_radio = QRadioButton('Degrees')
        self._ui_deg_radio.toggled.connect(self.on_phase_unit_change)
        layout_fmt_phase.addWidget(self._ui_deg_radio)
        self._ui_rad_radio = QRadioButton('Radians')
        layout_fmt_phase.addWidget(self._ui_rad_radio)
        fmt_grid.addWidget(QtHelper.make_label('CSV Separator:'), 1, 0)
        self._ui_csvsep_combo = QComboBox()
        fmt_grid.addWidget(self._ui_csvsep_combo, 1, 1)

        misc_widget = QWidget()
        self._ui_tabs.addTab(misc_widget, 'Misc')
        misc_grid = QGridLayout()
        misc_widget.setLayout(misc_grid)
        self._oi_extract_zip_combo = QCheckBox('Extract .zip-Files')
        misc_grid.addWidget(self._oi_extract_zip_combo, 0, 0)
        self._oi_comment_expr_combo = QCheckBox('Commend-Out Existing Expressions')
        misc_grid.addWidget(self._oi_comment_expr_combo, 1, 0)
        misc_grid.addWidget(QtHelper.make_label('External Editor:'), 2, 0)
        layout_misc_ed = QHBoxLayout()
        layout_misc_ed_widget = QWidget()
        layout_misc_ed_widget.setLayout(layout_misc_ed)
        misc_grid.addWidget(layout_misc_ed_widget, 2, 1)
        self._ui_exted_edit = QLineEdit()
        layout_misc_ed.addWidget(self._ui_exted_edit)
        self._ui_exted_btn = QtHelper.make_button('...', self.on_browse_ext_ed)
        layout_misc_ed.addWidget(self._ui_exted_btn)

        self.adjustSize()
    

    def ui_select_tab(self, tab: SettingsTab):
        self._ui_tabs.setCurrentIndex(int(tab))
    

    def ui_show(self):
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

    
    # to be implemented in derived class
    def on_browse_ext_ed(self):
        pass
    def on_phase_unit_change(self):
        pass
