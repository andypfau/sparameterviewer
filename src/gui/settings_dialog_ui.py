from .helpers.qt_helper import QtHelper
from .components.sivalue_edit import SiValueEdit
from lib import get_next_1_2_5_10, format_minute_seconds, SiValue
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
    Gui = 0
    Formats = 1
    Files = 2
    Misc = 3



class SettingsDialogUi(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle('Settings')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)

        self._warn_timeout_values = [2]
        while self._warn_timeout_values[-1] < 100:
            self._warn_timeout_values.append(get_next_1_2_5_10(self._warn_timeout_values[-1], nice_minutes=True))

        main_layout = QHBoxLayout()
        self._ui_tabs = QTabWidget()
        main_layout.addWidget(self._ui_tabs)
        self.setLayout(main_layout)

        gui_widget = QWidget()
        self._ui_tabs.addTab(gui_widget, 'GUI')
        self._ui_mainwinlayout_combo = QComboBox()
        self._ui_mainwinlayout_combo.setToolTip('Layout of the toolbar, filesysem browser, and plot in the main window.')
        self._ui_simple_params_check = QCheckBox('Simple Drop-Down Parameter Selection')
        self._ui_simple_params_check.setToolTip('Show a simple drop-down to select the plotted parameters, instead of the buttons and the parameter matrix in the main window toolbar.')
        self._ui_simple_params_check.toggled.connect(self.on_simple_params_changed)
        self._ui_simple_noexpr_check = QCheckBox('Do Not Use Expressions')
        self._ui_simple_noexpr_check.setToolTip('Disable and hide all expressions-related features.')
        self._ui_simple_noexpr_check.toggled.connect(self.on_simple_noexpr_changed)
        self._ui_simple_plot_check = QCheckBox('Simple Drop-Down Plot Selection')
        self._ui_simple_plot_check.setToolTip('Show two simple drop-downs (Y1 and Y2) instead of the buttons in the main window toolbar.')
        self._ui_simple_plot_check.toggled.connect(self.on_simple_plot_changed)
        self._ui_simple_browser_check = QCheckBox('Simplified Filesystem Browser')
        self._ui_simple_browser_check.setToolTip('Only allows one single root-directory in the filesystem browser (no pinning of additional directories).')
        self._ui_simple_browser_check.toggled.connect(self.on_simple_browser_changed)
        self._ui_largematrix_combo = QComboBox()
        self._ui_largematrix_combo.setToolTip('How the S-parameter matrix behaves when there are too many parameters to be displayed.')
        self._ui_selecttocheck_check = QCheckBox('Selected Files Are Automatically Checked')
        self._ui_selecttocheck_check.setToolTip('Only files that have their checkbox checked will be plotted. When this option is enabled, you can click anywhere on the file, or just multi-select it, and its checkbox will be checked. Regardless of this option, you cal aways click the checkbox directly, or use the spacebar to toggle the checkboxes.')
        self._ui_selecttocheck_check.toggled.connect(self.on_selecttocheck_changed)
        self._ui_guicolorscheme_combo = QComboBox()
        self._ui_guicolorscheme_combo.setToolTip('Global GUI color scheme. Will only be applied after re-starting the application.')
        self._ui_restore_geometry_check = QCheckBox('Restore main window geometry on startup')
        self._ui_restore_geometry_check.setToolTip('When starting the application, restore the last window size and splitter position. Can be temporarily disabled by holding the SHIFT key during startup.')
        self._ui_restore_geometry_check.toggled.connect(self.on_restore_geometry_changed)
        gui_widget.setLayout(
            QtHelper.layout_v(
                QtHelper.layout_h('Main Window Layout:', self._ui_mainwinlayout_combo,...),
                self._ui_simple_params_check,
                self._ui_simple_noexpr_check,
                self._ui_simple_plot_check,
                self._ui_simple_browser_check,
                self._ui_restore_geometry_check,
                QtHelper.layout_h('Large S-Param Matrix:', self._ui_largematrix_combo,...),
                self._ui_selecttocheck_check,
                QtHelper.layout_h('Color Scheme (requires re-start):', self._ui_guicolorscheme_combo,...),
                ...
            )
        )

        format_widget = QWidget()
        self._ui_tabs.addTab(format_widget, 'Formats')
        self._ui_allcomplex_check = QCheckBox('Process All Traces As Complex Data')
        self._ui_allcomplex_check.setToolTip('If enabled, real-values traces can be time-domain transformed, plotted in Smith or polar plots, and dB/mag/real/imag/phase/group delay is applied. If disabled, real-valued data is plotted as-is.')
        self._ui_allcomplex_check.toggled.connect(self.on_allcomplex_changed)
        self._ui_logxneg_combo = QComboBox()
        self._ui_logxneg_combo.setToolTip('What to do when there are negative values on a logarithmic X-axis.')
        self._ui_logyneg_combo = QComboBox()
        self._ui_logyneg_combo.setToolTip('What to do when there are negative values on a logarithmic X-axis.')
        self._ui_singletracecolor_check = QCheckBox('Individual Trace Colors When Single File Selected')
        self._ui_singletracecolor_check.setToolTip('When enabled, and only one single file is selected, then it is always plotted with individual colors for each trace. Otherwise, the combobox in the main window toolbar can be used to define a color scheme.')
        self._ui_singletracecolor_check.setToolTip('When this option is enabled, the trace colors are set to individual colors when only one single file is selected.')
        self._ui_singletracecolor_check.toggled.connect(self.on_singletracecolor_changed)
        format_widget.setLayout(
            QtHelper.layout_v(
                QtHelper.layout_h(
                    QtHelper.layout_grid([
                            ['Log. Y-Axis:', QtHelper.layout_h(self._ui_logyneg_combo, ...)],
                            ['Log. X-Axis:', QtHelper.layout_h(self._ui_logxneg_combo, ...)],
                    ]), ...
                ),
                self._ui_allcomplex_check,
                self._ui_singletracecolor_check,
                ...
            )
        )

        files_widget = QWidget()
        self._ui_tabs.addTab(files_widget, 'Files')
        self._ui_extract_zip_check = QCheckBox('Extract .zip-Files')
        self._ui_extract_zip_check.setToolTip('Reads .zip-files, and allows to directly plot S-parameter files inside them. If disabled, .zip-files are not shown.')
        self._ui_extract_zip_check.toggled.connect(self.on_zip_change)
        self._ui_warn_timeout_combo = QComboBox()
        self._ui_warn_timeout_combo.setToolTip('If loading files takes longer than the specified timeout, an "abort" button is shown in the toolbar. The user has then a chance to abort the operation and stop waiting. May be useful for slow network drives.')
        for secs in self._warn_timeout_values:
            self._ui_warn_timeout_combo.addItem(format_minute_seconds(secs))
        self._ui_warn_timeout_combo.currentIndexChanged.connect(self._on_warn_timeout_changed)
        self._ui_warn_timeout_combo.setCurrentIndex(0)
        self._ui_csvsep_combo = QComboBox()
        self._ui_csvsep_combo.setToolTip('The column separator used when exporting .csv-files.')
        self._ui_deg_radio = QRadioButton('Degrees')
        self._ui_deg_radio.setToolTip('When exporting data to file, express phase in degrees.')
        self._ui_deg_radio.toggled.connect(self.on_phase_unit_change)
        self._ui_rad_radio = QRadioButton('Radians')
        self._ui_rad_radio.setToolTip('When exporting data to file, express phase in radians.')
        self._ui_rad_radio.toggled.connect(self.on_phase_unit_change)
        self._ui_maxhist_spin = QSpinBox()
        self._ui_maxhist_spin.setMinimum(1)
        self._ui_maxhist_spin.setMaximum(30)
        self._ui_maxhist_spin.setToolTip('Maximum number of directories in file history (in main window main menu)')
        self._ui_maxhist_spin.valueChanged.connect(self.on_maxhist_change)
        files_widget.setLayout(
            QtHelper.layout_v(
                self._ui_extract_zip_check,
                QtHelper.layout_h('Warn When Loading Takes Longer Than', self._ui_warn_timeout_combo, ...),
                QtHelper.layout_h('CSV Separator:', self._ui_csvsep_combo, ...),
                QtHelper.layout_h('Export Phase Unit:', self._ui_deg_radio, self._ui_rad_radio, ...),
                QtHelper.layout_h('Max. History Size:', self._ui_maxhist_spin, ...),
                ...
            )
        )

        expr_widget = QWidget()
        self._ui_tabs.addTab(expr_widget, 'Expressions')
        self._ui_comment_expr_combo = QCheckBox('Commend-Out Existing Expressions')
        self._ui_comment_expr_combo.setToolTip('When adding expression templates, comment out all other existing expressions.')
        self._ui_comment_expr_combo.toggled.connect(self.on_comment_change)
        self._ui_static_template_radio = QRadioButton('Static')
        self._ui_static_template_radio.setToolTip('Templates that operate on specific networks use `nw("name")` to statically refer to the network.')
        self._ui_static_template_radio.toggled.connect(self.on_template_ref_changed)
        self._ui_dynamic_template_radio = QRadioButton('Dynamic')
        self._ui_dynamic_template_radio.setToolTip('Templates that operate on specific networks use `sel_nws()` to dynamically refer to any selected network.')
        self._ui_dynamic_template_radio.toggled.connect(self.on_template_ref_changed)
        expr_widget.setLayout(
            QtHelper.layout_v(
                self._ui_comment_expr_combo,
                QtHelper.layout_h('Template References', self._ui_static_template_radio, self._ui_dynamic_template_radio, ...),
                ...
            )
        )

        misc_widget = QWidget()
        self._ui_tabs.addTab(misc_widget, 'Misc')
        self._ui_cursor_snap = QComboBox()
        self._ui_cursor_snap.setToolTip('How to map the mouse-pointer position to a cursor position (use X-coordinate, or find closest point).')
        self._ui_plot_style_combo = QComboBox()
        self._ui_plot_style_combo.setToolTip('The matplotlib style for the plot. Requires re-start to take effect.')
        self._ui_plot_style_combo.setMinimumWidth(150)
        self._ui_font_combo = QComboBox()
        self._ui_font_combo.setToolTip('The font used in all text viewers/editors.')
        self._ui_font_combo.setMinimumWidth(250)
        self._ui_exted_edit = QLineEdit()
        self._ui_exted_edit.setToolTip('Path to an external editor, which is used by the "open in external editor" command.')
        self._ui_exted_edit.textChanged.connect(self.on_ext_ed_change)
        self._ui_exted_edit.setMinimumWidth(120)
        self._ui_exted_btn = QtHelper.make_button(self, '...', self.on_browse_ext_ed)
        self._ui_exted_btn.setToolTip('Browse for external text editor, which is used by the "open in external editor" command.')
        self._ui_verbose_check = QCheckBox('Verbose Log Output')
        self._ui_verbose_check.setToolTip('Adds additional log messages; might be helpful to  expressions.')
        self._ui_verbose_check.toggled.connect(self.on_verbose_changed)
        self._ui_resetall_btn = QPushButton('Reset all Settings')
        self._ui_resetall_btn.setToolTip('Reset all settings to their default values.')
        self._ui_resetall_btn.clicked.connect(self.on_reset_all_settings)
        misc_widget.setLayout(
            QtHelper.layout_v(
                QtHelper.layout_grid([
                        ['Cursor Snap:', QtHelper.layout_h(self._ui_cursor_snap, ...)],
                        ['Plot Style:', QtHelper.layout_h(self._ui_plot_style_combo, '(requires restart)')],
                        ['Editor Font:', QtHelper.layout_h(self._ui_font_combo)],
                        ['External Editor:', QtHelper.layout_h(self._ui_exted_edit, self._ui_exted_btn)],
                ]),
                self._ui_verbose_check,
                QtHelper.layout_h(self._ui_resetall_btn, ...),
                ...
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
    def ui_simplified_plot(self) -> bool:
        return self._ui_simple_plot_check.isChecked()
    @ui_simplified_plot.setter
    def ui_simplified_plot(self, value: bool):
        self._ui_simple_plot_check.setChecked(value)

    
    @property
    def ui_singletrace_individualcolor(self) -> bool:
        return self._ui_singletracecolor_check.isChecked()
    @ui_singletrace_individualcolor.setter
    def ui_singletrace_individualcolor(self, value: bool):
        self._ui_singletracecolor_check.setChecked(value)

    
    @property
    def ui_simplified_params(self) -> bool:
        return self._ui_simple_params_check.isChecked()
    @ui_simplified_params.setter
    def ui_simplified_params(self, value: bool):
        self._ui_simple_params_check.setChecked(value)

    
    @property
    def ui_simplified_noexpr(self) -> bool:
        return self._ui_simple_noexpr_check.isChecked()
    @ui_simplified_noexpr.setter
    def ui_simplified_noexpr(self, value: bool):
        self._ui_simple_noexpr_check.setChecked(value)

    
    @property
    def ui_simplified_browser(self) -> bool:
        return self._ui_simple_browser_check.isChecked()
    @ui_simplified_browser.setter
    def ui_simplified_browser(self, value: bool):
        self._ui_simple_browser_check.setChecked(value)

    
    @property
    def ui_mainwin_layout(self) -> str:
        return self._ui_mainwinlayout_combo.currentText()
    @ui_mainwin_layout.setter
    def ui_mainwin_layout(self, value: str):
        self._ui_mainwinlayout_combo.setCurrentText(value)

    
    @property
    def ui_largematrix_layout(self) -> str:
        return self._ui_largematrix_combo.currentText()
    @ui_largematrix_layout.setter
    def ui_largematrix_layout(self, value: str):
        self._ui_largematrix_combo.setCurrentText(value)

    
    @property
    def ui_guicolorscheme(self) -> str:
        return self._ui_guicolorscheme_combo.currentText()
    @ui_guicolorscheme.setter
    def ui_guicolorscheme(self, value: str):
        self._ui_guicolorscheme_combo.setCurrentText(value)

    
    @property
    def ui_logxneg(self) -> str:
        return self._ui_logxneg_combo.currentText()
    @ui_logxneg.setter
    def ui_logxneg(self, value: str):
        self._ui_logxneg_combo.setCurrentText(value)


    def ui_set_logxneg_options(self, options: list[str]):
        self._ui_logxneg_combo.clear()
        for option in options:
            self._ui_logxneg_combo.addItem(option)
        self._ui_logxneg_combo.currentIndexChanged.connect(self.on_logxneg_changed)

    
    @property
    def ui_logyneg(self) -> str:
        return self._ui_logyneg_combo.currentText()
    @ui_logyneg.setter
    def ui_logyneg(self, value: str):
        self._ui_logyneg_combo.setCurrentText(value)


    def ui_set_logyneg_options(self, options: list[str]):
        self._ui_logyneg_combo.clear()
        for option in options:
            self._ui_logyneg_combo.addItem(option)
        self._ui_logyneg_combo.currentIndexChanged.connect(self.on_logyneg_changed)


    def ui_set_mainwinlayout_options(self, options: list[str]):
        self._ui_mainwinlayout_combo.clear()
        for option in options:
            self._ui_mainwinlayout_combo.addItem(option)
        self._ui_mainwinlayout_combo.currentIndexChanged.connect(self.on_mainwinlayout_changed)


    def ui_set_largematrix_options(self, options: list[str]):
        self._ui_largematrix_combo.clear()
        for option in options:
            self._ui_largematrix_combo.addItem(option)
        self._ui_largematrix_combo.currentIndexChanged.connect(self.on_largematrix_changed)


    def ui_set_guicolorscheme_options(self, options: list[str]):
        self._ui_guicolorscheme_combo.clear()
        for option in options:
            self._ui_guicolorscheme_combo.addItem(option)
        self._ui_guicolorscheme_combo.currentIndexChanged.connect(self.on_guicolorscheme_changed)

    
    @property
    def ui_verbose(self) -> bool:
        return self._ui_verbose_check.isChecked()
    @ui_verbose.setter
    def ui_verbose(self, value: bool):
        self._ui_verbose_check.setChecked(value)

    
    @property
    def ui_selecttocheck(self) -> bool:
        return self._ui_selecttocheck_check.isChecked()
    @ui_selecttocheck.setter
    def ui_selecttocheck(self, value: bool):
        self._ui_selecttocheck_check.setChecked(value)

    
    @property
    def ui_maxhist(self) -> int:
        return self._ui_maxhist_spin.value()
    @ui_maxhist.setter
    def ui_maxhist(self, value: bool):
        self._ui_maxhist_spin.setValue(value)

    
    @property
    def ui_all_complex(self) -> bool:
        return self._ui_allcomplex_check.isChecked()
    @ui_all_complex.setter
    def ui_all_complex(self, value: bool):
        self._ui_allcomplex_check.setChecked(value)

    
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
    def ui_dynamic_template_ref(self) -> bool:
        return self._ui_dynamic_template_radio.isChecked()
    @ui_dynamic_template_ref.setter
    def ui_dynamic_template_ref(self, value: bool):
        if value:
            self._ui_dynamic_template_radio.setChecked(True)
        else:
            self._ui_static_template_radio.setChecked(True)

    
    @property
    def ui_extract_zip(self) -> bool:
        return self._ui_extract_zip_check.isChecked()
    @ui_extract_zip.setter
    def ui_extract_zip(self, value: bool):
        self._ui_extract_zip_check.setChecked(value)

    
    @property
    def ui_restore_geometry(self) -> bool:
        return self._ui_restore_geometry_check.isChecked()
    @ui_restore_geometry.setter
    def ui_restore_geometry(self, value: bool):
        self._ui_restore_geometry_check.setChecked(value)
    
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
    def ui_warn_timeout(self) -> float:
        try:
            return self._warn_timeout_values[self._ui_warn_timeout_combo.currentIndex()]
        except:
            return self._warn_timeout_values[0]
    @ui_warn_timeout.setter
    def ui_warn_timeout(self, value: float):
        try:
            idx = np.argmin(np.abs(np.array(self._warn_timeout_values) - value))
            self._ui_warn_timeout_combo.setCurrentIndex(idx)
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
    def on_zip_change(self):
        pass
    def on_comment_change(self):
        pass
    def on_template_ref_changed(self):
        pass
    def on_ext_ed_change(self):
        pass
    def on_browse_ext_ed(self):
        pass
    def on_plotstyle_change(self):
        pass
    def on_font_change(self):
        pass
    def on_cursor_snap_changed(self):
        pass
    def _on_warn_timeout_changed(self):
        pass
    def on_colorassignments_changed(self):
        pass
    def on_allcomplex_changed(self):
        pass
    def on_verbose_changed(self):
        pass
    def on_logxneg_changed(self):
        pass
    def on_logyneg_changed(self):
        pass
    def on_simple_params_changed(self):
        pass
    def on_simple_plot_changed(self):
        pass
    def on_simple_noexpr_changed(self):
        pass
    def on_simple_browser_changed(self):
        pass
    def on_mainwinlayout_changed(self):
        pass
    def on_largematrix_changed(self):
        pass
    def on_guicolorscheme_changed(self):
        pass
    def on_selecttocheck_changed(self):
        pass
    def on_singletracecolor_changed(self):
        pass
    def on_maxhist_change(self):
        pass
    def on_reset_all_settings(self):
        pass
    def on_restore_geometry_changed(self):
        pass
