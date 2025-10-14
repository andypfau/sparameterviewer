from .helpers.qt_helper import QtHelper
from .components.plot_widget import PlotWidget
from .components.statusbar import StatusBar
from .components.path_bar import PathBar
from .components.filesys_browser import FilesysBrowser, FilesysBrowserItemType
from .components.sirange_edit import SiRangeEdit
from .components.param_selector import ParamSelector
from .components.plot_selector import PlotSelector
from .components.sivalue_edit import SiValueEdit
from .components.py_editor import PyEditor
from lib import AppPaths, PathExt, Parameters, SiValue, SiRange, SiFormat, MainWindowLayout, PlotType, YQuantity

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
import numpy as np
from typing import Callable, Optional, Union



class MainWindowUi(QMainWindow):


    class Tab(enum.Enum):
        Files = enum.auto()
        Expressions = enum.auto()
        Cursors = enum.auto()


    def __init__(self):
        self._ui_timers: dict[any,tuple[QTimer,Callable]] = {}
        self._show_expressions = True
        self._layout = MainWindowLayout.Wide
        self._show_menu = False

        super().__init__()
        QtHelper.set_dialog_icon(self)

        self._ui_ribbon = QWidget()

        palette = QPalette()
        color_bg = palette.color(QPalette.ColorRole.Window).name()
        color_border = palette.color(QPalette.ColorRole.Dark).name()
        color_edit_bg = palette.color(QPalette.ColorRole.Light).name()
        color_hover_bg = palette.color(QPalette.ColorRole.Window).lighter(150).name()
        color_active_bg = palette.color(QPalette.ColorRole.Highlight).name()
        color_active_hover_bg = palette.color(QPalette.ColorRole.Highlight).lighter(150).name()
        color_active_hover_border = color_active_bg
        color_disabled_bg = palette.color(QPalette.ColorRole.Window).name()
        
        combo_arrow_image_url = os.path.join(AppPaths.get_resource_dir(), 'combo_arrow.svg').replace('\\', '/')
        self._ui_ribbon.setStyleSheet(f"""
            QWidget {{
                background-color: {color_bg};
                border: none;
                border-radius: 2px;
            }}
            QWidget.linesep {{
                background-color: {color_border};
            }}
            QToolButton {{
                background-color: {color_bg};
            }}
            QToolButton:checked {{
                background-color: {color_active_bg};
            }}
            QToolButton:hover {{
                background-color: {color_hover_bg};
                border: 1px solid {color_border}
            }}
            QToolButton:checked:hover {{
                background-color: {color_active_hover_bg};
                border: 1px solid {color_active_hover_border}
            }}
            QToolButton:disabled {{
                background-color: {color_disabled_bg};
            }}
            QToolButton::menu-indicator {{
                image: none;
            }}
            QComboBox {{
                border-bottom: 1px solid {color_border};
                border-radius: 0px;
            }}
            QComboBox:editable {{
                border: 1px solid {color_border};
            }}
            QComboBox:editable:focus {{
                background-color: {color_edit_bg};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: url({combo_arrow_image_url});
            }}
            """)
        def vline():
            frame = QFrame()
            frame.setProperty('class', 'linesep')
            frame.setFixedWidth(1)
            frame.setContentsMargins(0, 0, 0, 0)
            return frame
        self._ui_param_selector = ParamSelector(self)
        self._ui_param_selector.paramsChanged.connect(self.on_params_change)
        self._ui_param_selector.setGridSize(100)
        self._ui_plot_selector = PlotSelector(self)
        self._ui_plot_selector.valueChanged.connect(self.on_plottype_changed)
        self._ui_menu_button = QtHelper.make_toolbutton(self, None, icon='toolbar_menu.svg', tooltip='Show Main Menu (Alt)')
        self._ui_filter_button = QtHelper.make_toolbutton(self, None, self.on_show_filter, icon='toolbar_filter.svg', tooltip='Select files that match a filter string (Ctrl+F)', shortcut='Ctrl+F')
        self._ui_refresh_button = QtHelper.make_toolbutton(self, None, self.on_update_plot, icon='toolbar_refresh.svg', tooltip='Refresh Plot (F5)', shortcut='F5')
        self._ui_legend_button = QtHelper.make_toolbutton(self, None, self._on_show_legend, icon='toolbar_legend.svg', tooltip='Show Legend', checked=False)
        self._ui_short_legend_button = QtHelper.make_toolbutton(self, None, self.on_shorten_legend, icon='toolbar_short_legend.svg', tooltip='Shorten Legend Text', checked=False)
        self._ui_semitrans_button = QtHelper.make_toolbutton(self, None, self._on_semitrans_changed, icon='toolbar_transparent.svg', tooltip='Semi-Transparent Traces', checked=False)
        self._ui_logx_button = QtHelper.make_toolbutton(self, None, self.on_logx_changed, icon='toolbar_log-x.svg', tooltip='Logarithmic X-Axis', checked=False)
        self._ui_logy_button = QtHelper.make_toolbutton(self, None, self.on_logy_changed, icon='toolbar_log-y.svg', tooltip='Logarithmic Y-Axis', checked=False)
        self._ui_lockx_button = QtHelper.make_toolbutton(self, None, self.on_lock_xaxis, icon='toolbar_lock-x.svg', tooltip='Lock/unlock X-Axis Scale')
        self._ui_locky_button = QtHelper.make_toolbutton(self, None, self.on_lock_yaxis, icon='toolbar_lock-y.svg', tooltip='Lock/unlock Y-Axis Scale')
        self._ui_lockboth_button = QtHelper.make_toolbutton(self, None, self.on_lock_both_axes, icon='toolbar_lock-both.svg', tooltip='Lock/unlock both X- and Y-Axis Scales')
        self._ui_smartdb_button = QtHelper.make_toolbutton(self, None, self.on_smart_db, icon='toolbar_smart-db.svg', tooltip='Attempt Smart Scaling of dB-Values', checked=False)
        self._ui_pan_button = QtHelper.make_toolbutton(self, None, self._on_plottool_pan, icon='toolbar_pan.svg', tooltip='Pan-Tool for Plot; while this is active, you cannot move cursors', checked=False)
        self._ui_zoom_button = QtHelper.make_toolbutton(self, None, self._on_plottool_zoom, icon='toolbar_zoom.svg', tooltip='Zoom-Tool for Plot; while this is active, you cannot move cursors', checked=False)
        self._ui_zoom_xp_button = QtHelper.make_toolbutton(self, None, self._on_plottool_zoom_xp, icon='toolbar_zoom_xp.svg', tooltip='X-Axis Zoom In ')
        self._ui_zoom_xm_button = QtHelper.make_toolbutton(self, None, self._on_plottool_zoom_xm, icon='toolbar_zoom_xm.svg', tooltip='X-Axis Zoom Out')
        self._ui_zoom_yp_button = QtHelper.make_toolbutton(self, None, self._on_plottool_zoom_yp, icon='toolbar_zoom_yp.svg', tooltip='Y-Axis Zoom In')
        self._ui_zoom_ym_button = QtHelper.make_toolbutton(self, None, self._on_plottool_zoom_ym, icon='toolbar_zoom_ym.svg', tooltip='Y-Axis Zoom Out')
        self._ui_mark_button = QtHelper.make_toolbutton(self, None, self.on_mark_datapoints_changed, icon='toolbar_mark-points.svg', tooltip='Mark Data Points', checked=False)
        self._ui_save_image_button = QtHelper.make_toolbutton(self, None, self.on_save_plot_image, icon='toolbar_save-image.svg', tooltip='Save Image to File')
        self._ui_copy_image_button = QtHelper.make_toolbutton(self, None, self.on_copy_image, icon='toolbar_copy-image.svg', tooltip='Copy Image to Clipboard')
        self._ui_tabular_button = QtHelper.make_toolbutton(self, None, self.on_view_tabular, icon='toolbar_tabular.svg', tooltip='View/Copy/Save Tabular Data (Ctrl+T)', shortcut='Ctrl+T')
        self._ui_plaintext_button = QtHelper.make_toolbutton(self, None, self.on_view_plaintext, icon='toolbar_plaintext.svg', tooltip='View/Copy/Save Plaintext Data (Ctrl+P)', shortcut='Ctrl+P')
        self._ui_fileinfo_button = QtHelper.make_toolbutton(self, None, self.on_file_info, icon='toolbar_fileinfo.svg', tooltip='View Info About File (Ctrl+I)', shortcut='Ctrl+I')
        self._ui_settings_button = QtHelper.make_toolbutton(self, None, self.on_settings, icon='toolbar_settings.svg', tooltip='Open Settings (F4)', shortcut='F4')
        self._ui_toolmenu_button = QtHelper.make_toolbutton(self, None, None, icon='toolbar_menu-small.svg', tooltip='Show Tool Menu')
        self._ui_plotmenu_button = QtHelper.make_toolbutton(self, None, None, icon='toolbar_menu-small.svg', tooltip='Show Plot Menu')
        self._ui_help_button = QtHelper.make_toolbutton(self, None, self.on_help, icon='toolbar_help.svg', tooltip='Show Help (F1)', shortcut='F1')
        self._ui_abort_button = QtHelper.make_toolbutton(self, None, self.on_abort, icon='toolbar_abort.svg', tooltip='Abort Loading')
        self._ui_xaxis_range = SiRangeEdit(self, SiRange(allow_individual_wildcards=False), [(any,any),(0,10e9)])
        self._ui_xaxis_range.setToolTip('Set X-axis range, e.g. "0..20G" for 0 to 20 GHz, or "*" for auto-scale.')
        self._ui_xaxis_range.setMinimumWidth(120)
        self._ui_xaxis_range.setMaximumWidth(120)
        self._ui_xaxis_range.setStyleSheet('QComboBox QAbstractItemView { min-width: 30ex; }')
        self._ui_xaxis_range.rangeChanged.connect(self.on_xaxis_range_change)
        self._ui_yaxis_range = SiRangeEdit(self, SiRange(allow_individual_wildcards=False), [(any,any),(-25,+3),(-25,+25),(-50,+3),(-100,+3)])
        self._ui_yaxis_range.setToolTip('Set Y-axis range, e.g. "-20..5" for -20 to +5 dB, or "*" for auto-scale.')
        self._ui_yaxis_range.setMinimumWidth(120)
        self._ui_yaxis_range.setMaximumWidth(120)
        self._ui_yaxis_range.setStyleSheet('QComboBox QAbstractItemView { min-width: 30ex; }')
        self._ui_yaxis_range.rangeChanged.connect(self.on_yaxis_range_change)
        self._ui_color_combo = QComboBox()
        self._ui_color_combo.setStyleSheet('QComboBox QAbstractItemView { min-width: 25ex; }')
        margins, default_spacing, wide_spacing = 0, 2, 6
        self._ui_colors_layout = QtHelper.layout_widget_h('Color', self._ui_color_combo, ...,spacing=default_spacing, margins=0)
        self._ui_ribbon.setLayout(QtHelper.layout_h(
            QtHelper.layout_v(
                self._ui_menu_button,
                ..., margins=margins, spacing=default_spacing,
            ),
            vline(),
            QtHelper.layout_v(...,
                self._ui_param_selector,
                ..., margins=margins, spacing=default_spacing,
            ),
            vline(),
            QtHelper.layout_v(default_spacing,
                self._ui_plot_selector,
                ..., margins=margins, spacing=default_spacing,
            ),
            vline(),
            QtHelper.layout_v(...,
                QtHelper.layout_h(self._ui_locky_button, self._ui_yaxis_range, self._ui_logy_button, ..., spacing=default_spacing),
                QtHelper.layout_h(self._ui_lockx_button, self._ui_xaxis_range, self._ui_logx_button, ..., spacing=default_spacing),
                QtHelper.layout_h(self._ui_lockboth_button, wide_spacing, self._ui_zoom_xm_button, self._ui_zoom_xp_button, wide_spacing, self._ui_zoom_ym_button, self._ui_zoom_yp_button, wide_spacing, self._ui_smartdb_button, ..., spacing=default_spacing),
                ..., margins=margins, spacing=default_spacing
            ),
            vline(),
            QtHelper.layout_v(
                QtHelper.layout_h(
                    self._ui_legend_button,
                    self._ui_short_legend_button,
                    wide_spacing,
                    self._ui_semitrans_button,
                    self._ui_mark_button,
                    wide_spacing,
                    ...,
                    self._ui_plotmenu_button,
                    margins=margins, spacing=default_spacing
                ),
                QtHelper.layout_h(
                    self._ui_pan_button,
                    self._ui_zoom_button,
                    wide_spacing,
                    self._ui_refresh_button,
                    ..., margins=margins, spacing=default_spacing
                ),
                self._ui_colors_layout,
                ..., margins=margins, spacing=default_spacing
            ),
            vline(),
            QtHelper.layout_v(
                QtHelper.layout_h(
                    self._ui_filter_button,
                    ...,
                    QtHelper.layout_v(self._ui_toolmenu_button, ..., spacing=0),
                    margins=margins, spacing=default_spacing
                ),
                QtHelper.layout_h(
                    self._ui_tabular_button,
                    self._ui_plaintext_button,
                    self._ui_fileinfo_button,
                    ..., margins=margins, spacing=default_spacing
                ),
                QtHelper.layout_h(
                    self._ui_copy_image_button,
                    self._ui_save_image_button,
                    ..., margins=margins, spacing=default_spacing
                ),
                ..., margins=margins, spacing=default_spacing
            ),
            vline(),
            QtHelper.layout_v(
                self._ui_help_button,
                self._ui_settings_button,
                self._ui_abort_button,
                ..., margins=margins, spacing=default_spacing
            ),
            ..., margins=margins, spacing=wide_spacing
        ))
        self.setTabOrder(self._ui_yaxis_range, self._ui_xaxis_range)
        self._ui_ribbon.setContentsMargins(0, 0, 0, 0)
        self._ui_ribbon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._ui_plot = PlotWidget()
        self._ui_plot.setMinimumSize(150, 100)
        
        self._ui_tabs = QTabWidget()

        self._ui_files_tab = QWidget()
        self._ui_tabs.addTab(self._ui_files_tab, 'Files')
        self._ui_filesys_browser = FilesysBrowser()
        self._ui_filesys_browser.selectionChanged.connect(self.on_filesys_selection_changed)
        self._ui_filesys_browser.topLevelsChanged.connect(self.on_filesys_toplevels_changed)
        self._ui_filesys_browser.filesChanged.connect(self.on_filesys_files_changed)
        self._ui_filesys_browser.contextMenuRequested.connect(self.on_filesys_contextmenu)
        self._ui_files_tab.setLayout(QtHelper.layout_h(self._ui_filesys_browser))
        
        self._ui_expressions_tab = QWidget()
        self._ui_tabs.addTab(self._ui_expressions_tab, 'Expressions')
        self._ui_update_button = QPushButton('Update (F5)')
        self._ui_update_button.clicked.connect(self.on_update_expressions)
        self._ui_template_button = QPushButton('Template...')
        self._ui_template_button.clicked.connect(self.on_template_button)
        self._ui_help_button = QPushButton('Help')
        self._ui_help_button.clicked.connect(self.on_help_button)
        self._ui_editor_font = QtHelper.make_font(family=QtHelper.get_monospace_font())
        self._ui_editor = PyEditor()
        self._ui_expressions_tab.setLayout(QtHelper.layout_h(
            QtHelper.layout_v(
                self._ui_update_button,
                self._ui_template_button,
                5,
                self._ui_help_button,
                ...
            ),
            self._ui_editor
        ))
        
        self._ui_cursors_tab = QWidget()
        self._ui_tabs.addTab(self._ui_cursors_tab, 'Cursors')
        self._ui_cursor1_radio = QRadioButton('Cursor 1')
        self._ui_cursor1_radio.setChecked(True)
        self._ui_cursor1_radio.toggled.connect(self.on_cursor_select)
        self._ui_cursor2_radio = QRadioButton('Cursor 2')
        self._ui_cursor2_radio.toggled.connect(self.on_cursor_select)
        self._ui_cursor1_trace_combo = QComboBox()
        self._ui_cursor1_trace_combo.currentIndexChanged.connect(self.on_cursor_trace_change)
        self._ui_cursor2_trace_combo = QComboBox()
        self._ui_cursor2_trace_combo.currentIndexChanged.connect(self.on_cursor_trace_change)
        self._ui_auto_cursor_check = QCheckBox('Auto Cursor')
        self._ui_auto_cursor_check.toggled.connect(self.on_auto_cursor_changed)
        self._ui_auto_cursor_check.setToolTip('When clicking into the plot, automatically select the cursors that is closest to the clicked point')
        self._ui_auto_cursor_trace_check = QCheckBox('Auto Trace')
        self._ui_auto_cursor_trace_check.setChecked(True)
        self._ui_auto_cursor_trace_check.toggled.connect(self.on_auto_cursor_trace_changed)
        self._ui_auto_cursor_trace_check.setToolTip('When clicking into the plot, automatically put the cursor onto the trace that is closest to the clicked point')
        self._ui_zoompan_label = QtHelper.make_label('Disable Zoom/Pan To Move Cursors')
        self._ui_zoompan_label.setVisible(False)
        self._ui_zoompan_label.setToolTip('The zoom or pan tool is activated in the toolbar. De-activate it to move cursors with the mouse')
        self._ui_cursor_syncx_check = QCheckBox('Sync X')
        self._ui_cursor_syncx_check.toggled.connect(self.on_cursor_syncx_changed)
        self._ui_cursor_syncx_check.setToolTip('Set both cursors to the same x-position')
        self._ui_cursor_finex_check = QCheckBox('Fine X')
        self._ui_cursor_finex_check.toggled.connect(self.on_cursor_finex_changed)
        self._ui_cursor_finex_check.setToolTip('Interpolate between points in the plot; if disabled, cursors can only be placed on discrete points that actually are in the raw data of the plot')
        self._ui_cursor_edit_x1 = SiValueEdit()
        self._ui_cursor_edit_x1.setReadOnly(True)
        self._ui_cursor_edit_x1.valueChanged.connect(self.on_cursor_x1_changed)
        self._ui_cursor_readout_y1 = QLineEdit()
        self._ui_cursor_readout_y1.setReadOnly(True)
        self._ui_cursor_edit_x2 = SiValueEdit()
        self._ui_cursor_edit_x2.setReadOnly(True)
        self._ui_cursor_edit_x2.valueChanged.connect(self.on_cursor_x2_changed)
        self._ui_cursor_readout_y2 = QLineEdit()
        self._ui_cursor_readout_y2.setReadOnly(True)
        self._ui_cursor_readout_dx = QLineEdit()
        self._ui_cursor_readout_dx.setReadOnly(True)
        self._ui_cursor_readout_dy = QLineEdit()
        self._ui_cursor_readout_dy.setReadOnly(True)
        cursor_layout = QtHelper.layout_grid([
            [self._ui_cursor1_radio, self._ui_cursor1_trace_combo, 'X1:', self._ui_cursor_edit_x1, 'Y1:', self._ui_cursor_readout_y1],
            [self._ui_cursor2_radio, self._ui_cursor2_trace_combo, 'X2:', self._ui_cursor_edit_x2, 'Y2:', self._ui_cursor_readout_y2],
            [self._ui_auto_cursor_check, self._ui_auto_cursor_trace_check, 'ΔX:', self._ui_cursor_readout_dx, 'ΔY:', self._ui_cursor_readout_dy],
            [QtHelper.CellSpan(self._ui_zoompan_label, cols=2), None, QtHelper.CellSpan(QtHelper.layout_h(self._ui_cursor_syncx_check, self._ui_cursor_finex_check), cols=2)],
        ])
        cursor_layout.setColumnStretch(0, 0)
        cursor_layout.setColumnStretch(1, 2)
        cursor_layout.setColumnStretch(2, 0)
        cursor_layout.setColumnStretch(3, 1)
        cursor_layout.setColumnStretch(4, 0)
        cursor_layout.setColumnStretch(5, 1)
        self._ui_cursors_tab.setLayout(QtHelper.layout_v(cursor_layout,...))

        self._ui_status_bar = StatusBar()

        self._ui_main_container = QWidget()
        self._ui_main_container.setContentsMargins(0, 0, 0, 0)
        self._ui_main_container.setLayout(QVBoxLayout())
        self._ui_splitter = QSplitter()
        self._ui_splitter.addWidget(QWidget())
        self._ui_splitter.addWidget(QWidget())
        self._ui_secondary_container = QWidget()
        self._ui_secondary_container.setContentsMargins(0, 0, 0, 0)
        self._ui_secondary_container.setLayout(QVBoxLayout())
        self._ui_secondary_container.layout().setContentsMargins(0, 0, 0, 0)

        self.setCentralWidget(QtHelper.layout_widget_v(
            self._ui_main_container,
            self._ui_status_bar,
            margins=0
        ))
        
        self._ui_splitter.splitterMoved.connect(self.on_resize)
        self._ui_tabs.currentChanged.connect(self.on_tab_change)
        self._ui_plot.attach(self.on_plot_mouse_event)
        self._ui_status_bar.clicked.connect(self.on_statusbar_click)

        self._build_menus()
        self._update_layout()
        self._update_enabled()
        self.ui_enable_expressions(True)


    def keyPressEvent(self, event: QtGui.QKeyEvent|None):  # overloaded from QTextEdit
        if event.key()==Qt.Key.Key_Alt and event.modifiers()==QtCore.Qt.KeyboardModifier.AltModifier:
            self._ui_menu_button.showMenu()
        super().keyPressEvent(event)


    def _update_layout(self):

        # erase current layout
        for i in reversed(range(self._ui_main_container.layout().count())):
            self._ui_main_container.layout().takeAt(0)
        for i in reversed(range(self._ui_secondary_container.layout().count())):
            self._ui_secondary_container.layout().takeAt(0)
        self._ui_splitter.replaceWidget(0, QWidget())
        self._ui_splitter.replaceWidget(1, QWidget())

        if self._layout == MainWindowLayout.Wide:
            self._ui_main_container.layout().addWidget(self._ui_ribbon)
            self._ui_main_container.layout().addWidget(self._ui_splitter)
            self._ui_splitter.replaceWidget(0, self._ui_tabs)
            self._ui_splitter.replaceWidget(1, self._ui_plot)
            self._ui_splitter.setStretchFactor(0, 1)
            self._ui_splitter.setStretchFactor(1, 2)
            self._ui_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)

        elif self._layout == MainWindowLayout.Vertical:
            self._ui_main_container.layout().addWidget(self._ui_ribbon)
            self._ui_main_container.layout().addWidget(self._ui_splitter)
            self._ui_splitter.replaceWidget(0, self._ui_plot)
            self._ui_splitter.replaceWidget(1, self._ui_tabs)
            self._ui_splitter.setStretchFactor(0, 2)
            self._ui_splitter.setStretchFactor(1, 1)
            self._ui_splitter.setOrientation(QtCore.Qt.Orientation.Vertical)

        elif self._layout == MainWindowLayout.Ultrawide:
            self._ui_main_container.layout().addWidget(self._ui_splitter)
            self._ui_secondary_container.layout().addWidget(self._ui_ribbon)
            self._ui_secondary_container.layout().addWidget(self._ui_tabs)
            self._ui_splitter.replaceWidget(0, self._ui_secondary_container)
            self._ui_splitter.replaceWidget(1, self._ui_plot)
            self._ui_splitter.setStretchFactor(0, 1)
            self._ui_splitter.setStretchFactor(1, 2)
            self._ui_splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)

        else:
            raise ValueError()

        self._ui_splitter.setCollapsible(0, False)
        self._ui_splitter.setCollapsible(1, False)


    def resizeEvent(self, arg):
        result = super().resizeEvent(arg)
        self.on_resize()
        return result


    def _build_menus(self):
        self._ui_mainmenu = QMenu(self)
        self._ui_menuitem_loaddir_files = QtHelper.add_menuitem(self._ui_mainmenu, 'Open Directory...', self.on_load_dir, shortcut='Ctrl+O')
        self._ui_menuitem_reload_all_files = QtHelper.add_menuitem(self._ui_mainmenu, 'Reload All Files', self.on_reload_all_files, shortcut='Ctrl+F5')
        self._ui_mainmenu_recent = QtHelper.add_submenu(self._ui_mainmenu, 'Recent Directories', visible=False)
        self._ui_menuitem_recent_items = []
        self._ui_mainmenu.addSeparator()
        self._ui_menuitem_load_expr = QtHelper.add_menuitem(self._ui_mainmenu, 'Load Expressions...', self.on_load_expressions)
        self._ui_menuitem_save_expr = QtHelper.add_menuitem(self._ui_mainmenu, 'Save Expressions...', self.on_save_expressions)
        self._ui_mainmenu.addSeparator()
        self._ui_menuitem_about = QtHelper.add_menuitem(self._ui_mainmenu, 'About', self.on_about)
        self._ui_mainmenu.addSeparator()
        self._ui_menuitem_exit = QtHelper.add_menuitem(self._ui_mainmenu, 'Exit', self.close)
        self._ui_menu_button.setMenu(self._ui_mainmenu)
        self._ui_menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self._ui_viewmenu = QMenu()
        self._ui_opacity_slider = QSlider(QtCore.Qt.Orientation.Horizontal)
        self._ui_opacity_slider.setMinimumWidth(150)
        self._ui_opacity_slider.setMinimum(0)
        self._ui_opacity_slider.setMaximum(1000)
        self._ui_opacity_slider.valueChanged.connect(self.on_traceopacity_changed)
        self._ui_opacity_menuwidget = QtHelper.add_menu_action(self._ui_viewmenu, QtHelper.layout_widget_h('Trace Opacity:', self._ui_opacity_slider))
        self._ui_viewmenu.addSeparator()
        self._ui_max_legend_spin = QSpinBox()
        self._ui_max_legend_spin.setMinimum(1)
        self._ui_max_legend_spin.setMaximum(999)
        self._ui_max_legend_spin.setMinimumWidth(50)
        self._ui_max_legend_spin.valueChanged.connect(self.on_maxlegend_changed)
        self._ui_max_legend_menuwidget = QtHelper.add_menu_action(self._ui_viewmenu, QtHelper.layout_widget_h('Max. Legend Items:', self._ui_max_legend_spin))
        self._ui_menuitem_hide_single_legend = QtHelper.add_menuitem(self._ui_viewmenu, 'Hide Single-Item Legend', self.on_hide_single_legend, checkable=True)
        self._ui_plotmenu_button.setMenu(self._ui_viewmenu)
        self._ui_plotmenu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self._ui_toolmenu = QMenu()
        self._ui_menuitem_open_ext = QtHelper.add_menuitem(self._ui_toolmenu, 'Open Selected Files Externally', self.on_open_externally, shortcut='Ctrl+E')
        self._ui_toolmenu.addSeparator()
        self._ui_menuitem_rlcalc = QtHelper.add_menuitem(self._ui_toolmenu, 'Return Loss Integrator...', self.on_rl_calc)
        self._ui_menuitem_log = QtHelper.add_menuitem(self._ui_toolmenu, 'Status Log', self.on_show_log, shortcut='Ctrl+L')
        self._ui_toolmenu_button.setMenu(self._ui_toolmenu)
        self._ui_toolmenu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
    

    def _update_enabled(self):
        self._ui_opacity_menuwidget.setEnabled(self.ui_semitrans_traces)
        self._ui_max_legend_menuwidget.setEnabled(self.ui_show_legend)
        self._ui_menuitem_hide_single_legend.setEnabled(self.ui_show_legend)
        self._ui_short_legend_button.setVisible(self.ui_show_legend)

    
    def _on_plottool_pan(self):
        self._ui_zoom_button.setChecked(False)
        self._ui_plot.setTool(self.ui_plot_tool)
        self._enable_cursors(self.ui_plot_tool == PlotWidget.Tool.Off)
    

    def _on_plottool_zoom(self):
        self._ui_pan_button.setChecked(False)
        self._ui_plot.setTool(self.ui_plot_tool)
        self._enable_cursors(self.ui_plot_tool == PlotWidget.Tool.Off)
    

    def _on_plottool_zoom_xp(self):
        self.on_zoom_clicked(dx=+1, dy=0)
    

    def _on_plottool_zoom_xm(self):
        self.on_zoom_clicked(dx=-1, dy=0)
    

    def _on_plottool_zoom_yp(self):
        self.on_zoom_clicked(dx=0, dy=+1)
    

    def _on_plottool_zoom_ym(self):
        self.on_zoom_clicked(dx=0, dy=-1)


    def ui_show(self):
        super().show()


    def ui_set_color_assignment_options(self, options: list[str]):
        self._ui_color_combo.clear()
        for option in options:
            self._ui_color_combo.addItem(option)
        self._ui_color_combo.currentIndexChanged.connect(self.on_color_change)

    
    @property
    def ui_filesys_browser(self) -> FilesysBrowser:
        return self._ui_filesys_browser

    
    @property
    def ui_plot_selector(self) -> PlotSelector:
        return self._ui_plot_selector

    
    @property
    def ui_param_selector(self) -> ParamSelector:
        return self._ui_param_selector

    
    @property
    def ui_layout(self) -> MainWindowLayout:
        return self._layout
    @ui_layout.setter
    def ui_layout(self, value: MainWindowLayout):
        if self._layout == value:
            return
        self._layout = value
        self._update_layout()

    
    @property
    def ui_color_assignment(self) -> str:
        return self._ui_color_combo.currentText()
    @ui_color_assignment.setter
    def ui_color_assignment(self, value: str):
        self._ui_color_combo.setCurrentText(value)

    
    def ui_enable_expressions(self, enable: bool):
        if not self._show_expressions:
            return
        
        def make_icon(enable: bool) -> QIcon:
            SIZE = 16
            palette = QPalette()
            if enable:
                pixmap = QPixmap(SIZE, SIZE)
            else:
                pixmap = QPixmap(1, 1)
            pixmap.fill(QColorConstants.Transparent)
            if enable:
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setPen(QColorConstants.Transparent)
                painter.setBrush(palette.color(QPalette.ColorRole.Highlight))
                painter.drawEllipse(0, 0, SIZE, SIZE)
                painter.end()
            return QIcon(pixmap)

        self._ui_tabs.setTabIcon(1, make_icon(enable))
        self._ui_update_button.setText('Update (F5)' if enable else 'Turn On\nExpressions\n(F5)')
        self._ui_editor.setInactive(not enable)

    
    def ui_show_expressions(self, value: bool):
        if self._show_expressions == value:
            return
        self._show_expressions = value
        if self._show_expressions:
            self._ui_tabs.insertTab(1, self._ui_expressions_tab, 'Expressions')
        else:
            if self.ui_tab == MainWindowUi.Tab.Expressions:
                self.ui_tab = MainWindowUi.Tab.Files
            self._ui_tabs.removeTab(1)

    
    def ui_show_abort_button(self, value: bool):
        self._ui_abort_button.setVisible(value)

    
    def ui_update(self):
        QApplication.processEvents()


    def ui_show_template_menu(self, items: list[tuple[str,Callable|list]]):
        button_pos = self._ui_template_button.mapToGlobal(QPoint(0, self._ui_template_button.height()))
        QtHelper.show_popup_menu(self, items, button_pos)

    
    def ui_set_window_title(self, title: str):
        self.setWindowTitle(title)


    def ui_schedule_oneshot_timer(self, identifier: any, seconds: float, callback: Callable, retrigger_behavior: str = 'keep'):
        
        msec = max(1,int(round(seconds*1e3)))
        
        if identifier in self._ui_timers:
            if retrigger_behavior == 'keep':
                return
            elif retrigger_behavior == 'postpone':
                timer = self._ui_timers[identifier][0]
                timer.stop()
                timer.start(msec)
                return
        
        self._ui_timers[identifier] = (QTimer(), callback)
        def make_timeout_function(identifier):
            def timeout_function():
                callback = self._ui_timers[identifier][1]
                del self._ui_timers[identifier]
                callback()
            return timeout_function
        self._ui_timers[identifier][0].timeout.connect(make_timeout_function(identifier))
        
        self._ui_timers[identifier][0].setSingleShot(True)
        self._ui_timers[identifier][0].start(msec)
        
    
    def ui_abort_oneshot_timer(self, identifier: any):
        if identifier not in self._ui_timers:
            return
        timer = self._ui_timers[identifier][0]
        timer.stop()
        del self._ui_timers[identifier]
    

    @property
    def ui_plot(self) -> PlotWidget:
        return self._ui_plot
    

    @property
    def ui_tab(self) -> Tab:
        match self._ui_tabs.currentIndex():
            case 0: return MainWindowUi.Tab.Files
            case 1: return MainWindowUi.Tab.Expressions
            case 2: return MainWindowUi.Tab.Cursors
        raise RuntimeError()
    @ui_tab.setter
    def ui_tab(self, value: Tab):
        match value:
            case MainWindowUi.Tab.Files: self._ui_tabs.setCurrentIndex(0)
            case MainWindowUi.Tab.Expressions: self._ui_tabs.setCurrentIndex(1)
            case MainWindowUi.Tab.Cursors: self._ui_tabs.setCurrentIndex(2)
    

    @property
    def ui_plot_tool(self) -> PlotWidget.Tool:
        if self._ui_pan_button.isChecked():
            return PlotWidget.Tool.Pan
        elif self._ui_zoom_button.isChecked():
            return PlotWidget.Tool.Zoom
        else:
            return PlotWidget.Tool.Off
    @ui_plot_tool.setter
    def ui_plot_tool(self, value: PlotWidget.Tool):
        self._ui_pan_button.setChecked(value == PlotWidget.Tool.Pan)
        self._ui_zoom_button.setChecked(value == PlotWidget.Tool.Zoom)
        self._ui_plot.setTool(value)
        self._enable_cursors(value == PlotWidget.Tool.Off)


    @property
    def ui_smart_db(self) -> bool:
        return self._ui_smartdb_button.isChecked()
    @ui_smart_db.setter
    def ui_smart_db(self, value: bool):
        self._ui_smartdb_button.setChecked(value)


    @property
    def ui_enable_trace_color_selector(self) -> bool:
        return self._ui_colors_layout.isEnabled()
    @ui_enable_trace_color_selector.setter
    def ui_enable_trace_color_selector(self, value: bool):
        if value:
            self._ui_colors_layout.setEnabled(True)
            self._ui_color_combo.setToolTip('Select how trace colors are assigned.')
        else:
            self._ui_colors_layout.setEnabled(False)
            self._ui_color_combo.setToolTip('Trace colors are assigned individually per trace, because only one file is plotted (this behavior can be changed in the Settings dialog).')



    @property
    def ui_show_smart_db(self) -> bool:
        return self._ui_smartdb_button.isVisible()
    @ui_show_smart_db.setter
    def ui_show_smart_db(self, value: bool):
        self._ui_smartdb_button.setVisible(value)


    @property
    def ui_show_legend(self) -> bool:
        return self._ui_legend_button.isChecked()
    @ui_show_legend.setter
    def ui_show_legend(self, value: bool):
        self._ui_legend_button.setChecked(value)
        self._update_enabled()


    @property
    def ui_semitrans_traces(self) -> bool:
        return self._ui_semitrans_button.isChecked()
    @ui_semitrans_traces.setter
    def ui_semitrans_traces(self, value: bool):
        self._ui_semitrans_button.setChecked(value)
        self._update_enabled()


    @property
    def ui_trace_opacity(self) -> float:
        return self._ui_opacity_slider.value()/1000.0
    @ui_trace_opacity.setter
    def ui_trace_opacity(self, value: float):
        self._ui_opacity_slider.setValue(round(value*1000))


    @property
    def ui_maxlegend(self) -> int:
        return self._ui_max_legend_spin.value()
    @ui_maxlegend.setter
    def ui_maxlegend(self, value: int):
        self._ui_max_legend_spin.setValue(value)


    def ui_filesys_navigate(self, path: str):
        self._ui_filesys_browser.navigate(path)
    

    def ui_filesys_show_contextmenu(self, items: list[tuple[str,Callable|list]]):
        self._ui_filesys_browser.show_context_menu(items)
    

    @property
    def ui_hide_single_item_legend(self) -> bool:
        return self._ui_menuitem_hide_single_legend.isChecked()
    @ui_hide_single_item_legend.setter
    def ui_hide_single_item_legend(self, value):
        self._ui_menuitem_hide_single_legend.setChecked(value)
    

    @property
    def ui_shorten_legend(self) -> bool:
        return self._ui_short_legend_button.isChecked()
    @ui_shorten_legend.setter
    def ui_shorten_legend(self, value):
        self._ui_short_legend_button.setChecked(value)
    

    @property
    def ui_mark_datapoints(self) -> bool:
        return self._ui_mark_button.isChecked()
    @ui_mark_datapoints.setter
    def ui_mark_datapoints(self, value):
        self._ui_mark_button.setChecked(value)
    

    @property
    def ui_logx(self) -> bool:
        return self._ui_logx_button.isChecked()
    @ui_logx.setter
    def ui_logx(self, value):
        self._ui_logx_button.setChecked(value)
    

    @property
    def ui_logx(self) -> bool:
        return self._ui_logx_button.isChecked()
    @ui_logx.setter
    def ui_logx(self, value: bool):
        self._ui_logx_button.setChecked(value)
    

    @property
    def ui_logy(self) -> bool:
        return self._ui_logy_button.isChecked()
    @ui_logy.setter
    def ui_logy(self, value: bool):
        self._ui_logy_button.setChecked(value)
    

    @property
    def ui_xaxis_range(self) -> SiRange:
        return self._ui_xaxis_range.range()
    @ui_xaxis_range.setter
    def ui_xaxis_range(self, value: SiRange):
        self._ui_xaxis_range.setRange(value)
    

    @property
    def ui_yaxis_range(self) -> SiRange:
        return self._ui_yaxis_range.range()
    @ui_yaxis_range.setter
    def ui_yaxis_range(self, value: SiRange):
        self._ui_yaxis_range.setRange(value)


    @property
    def ui_expression(self) -> str:
        return self._ui_editor.toPlainText()
    @ui_expression.setter
    def ui_expression(self, expression: str):
        self._ui_editor.setText(expression)
        self._ui_editor.document().setDefaultFont(self._ui_editor_font)


    @property
    def ui_params_size(self) -> int:
        return self._ui_param_selector.matrixDimensions()
    @ui_params_size.setter
    def ui_params_size(self, value: int):
        self._ui_param_selector.setMatrixDimensions(value)


    def ui_set_cursor_trace_list(self, traces: list[str]):
        for combo in [self._ui_cursor1_trace_combo, self._ui_cursor2_trace_combo]:
            combo.clear()
            for trace in traces:
                combo.addItem(trace)


    @property
    def ui_cursor_x1(self) -> SiValue:
        return self._ui_cursor_edit_x1.value()

    
    @property
    def ui_cursor_x2(self) -> SiValue:
        return self._ui_cursor_edit_x2.value()

    
    def ui_set_cursor_readouts(self, x1: SiValue|None = None, y1: str = '', x2: SiValue|None = None, y2: str = '', dx: str = '', dy: str = ''):
        if x1 is None:
            self._ui_cursor_edit_x1.setBlank(True)
        else:
            self._ui_cursor_edit_x1.setBlank(False)
            self._ui_cursor_edit_x1.setValue(x1)
        self._ui_cursor_edit_x1.setReadOnly(x1 is None)
        self._ui_cursor_readout_y1.setText(y1)
        if x2 is None:
            self._ui_cursor_edit_x2.setBlank(True)
        else:
            self._ui_cursor_edit_x2.setBlank(False)
            self._ui_cursor_edit_x2.setValue(x2)
        self._ui_cursor_edit_x2.setReadOnly(x2 is None)
        self._ui_cursor_readout_y2.setText(y2)
        self._ui_cursor_readout_dx.setText(dx)
        self._ui_cursor_readout_dy.setText(dy)

    
    @property
    def ui_cursor_index(self) -> int:
        return 1 if self._ui_cursor2_radio.isChecked() else 0
    @ui_cursor_index.setter
    def ui_cursor_index(self, value: int):
        if value == 0:
            self._ui_cursor1_radio.setChecked(True)
        elif value == 1:
            self._ui_cursor2_radio.setChecked(True)

    
    @property
    def ui_cursor1_trace(self) -> str:
        return self._ui_cursor1_trace_combo.currentText()
    @ui_cursor1_trace.setter
    def ui_cursor1_trace(self, value: int):
        try:
            self._ui_cursor1_trace_combo.setCurrentText(value)
        except:
            pass

    
    @property
    def ui_cursor2_trace(self) -> str:
        return self._ui_cursor2_trace_combo.currentText()
    @ui_cursor2_trace.setter
    def ui_cursor2_trace(self, value: int):
        try:
            self._ui_cursor2_trace_combo.setCurrentText(value)
        except:
            pass

    
    @property
    def ui_auto_cursor(self) -> bool:
        return self._ui_auto_cursor_check.isChecked()
    @ui_auto_cursor.setter
    def ui_auto_cursor(self, value: bool):
        self._ui_auto_cursor_check.setChecked(value)

    
    @property
    def ui_auto_cursor_trace(self) -> bool:
        return self._ui_auto_cursor_trace_check.isChecked()
    @ui_auto_cursor_trace.setter
    def ui_auto_cursor_trace(self, value: bool):
        self._ui_auto_cursor_trace_check.setChecked(value)

    
    @property
    def ui_cursor_syncx(self) -> bool:
        return self._ui_cursor_syncx_check.isChecked()
    @ui_cursor_syncx.setter
    def ui_cursor_syncx(self, value: bool):
        self._ui_cursor_syncx_check.setChecked(value)

    
    @property
    def ui_cursor_finex(self) -> bool:
        return self._ui_cursor_finex_check.isChecked()
    @ui_cursor_finex.setter
    def ui_cursor_finex(self, value: bool):
        self._ui_cursor_finex_check.setChecked(value)


    def ui_show_status_message(self, message: str|None = None, level: int = logging.INFO):
        self._ui_status_bar.setMessage(message, level)


    def ui_update_files_history(self, texts_and_callbacks: list[tuple[str,Callable]]):
        
        self._ui_menuitem_recent_items.clear()
        self._ui_mainmenu_recent.clear()

        for (text,callback) in texts_and_callbacks:
            new_item = QtHelper.add_menuitem(self._ui_mainmenu_recent, text, callback)
            self._ui_menuitem_recent_items.append(new_item)
        
        self._ui_mainmenu_recent.setEnabled(len(self._ui_menuitem_recent_items) > 0)
    

    def _on_show_legend(self):
        self._update_enabled()
        self.on_show_legend()


    def _on_semitrans_changed(self):
        self._update_enabled()
        self.on_semitrans_changed()
    

    def _enable_cursors(self, enable: bool = True):
        self._ui_cursor1_radio.setEnabled(enable)
        self._ui_cursor2_radio.setEnabled(enable)
        self._ui_auto_cursor_check.setEnabled(enable)
        self._ui_cursor1_trace_combo.setEnabled(enable)
        self._ui_cursor2_trace_combo.setEnabled(enable)
        self._ui_auto_cursor_trace_check.setEnabled(enable)
        self._ui_cursor_syncx_check.setEnabled(enable)
        self._ui_zoompan_label.setVisible(not enable)


    # to be implemented in derived class
    def on_params_change(self):
        pass
    def on_plottype_changed(self):
        pass
    def on_show_filter(self):
        pass
    def on_load_dir(self):
        pass
    def on_reload_all_files(self):
        pass
    def on_rl_calc(self):
        pass
    def on_show_log(self):
        pass
    def on_settings(self):
        pass
    def on_help(self):
        pass
    def on_abort(self):
        pass
    def on_about(self):
        pass
    def on_save_plot_image(self):
        pass
    def on_file_info(self):
        pass
    def on_view_tabular(self):
        pass
    def on_open_externally(self):
        pass
    def on_view_plaintext(self):
        pass
    def on_load_expressions(self):
        pass
    def on_save_expressions(self):
        pass
    def on_show_legend(self):
        pass
    def on_hide_single_legend(self):
        pass
    def on_shorten_legend(self):
        pass
    def on_copy_image(self):
        pass
    def on_lock_xaxis(self):
        pass
    def on_lock_yaxis(self):
        pass
    def on_lock_both_axes(self):
        pass
    def on_smart_db(self):
        pass
    def on_turnon_expressions(self):
        pass
    def on_update_expressions(self):
        pass
    def on_update_plot(self):
        pass
    def on_template_button(self):
        pass
    def on_help_button(self):
        pass
    def on_tab_change(self):
        pass
    def on_cursor_select(self):
        pass
    def on_cursor_x1_changed(self):
        pass
    def on_cursor_x2_changed(self):
        pass
    def on_cursor_trace_change(self):
        pass
    def on_auto_cursor_changed(self):
        pass
    def on_auto_cursor_trace_changed(self):
        pass
    def on_cursor_syncx_changed(self):
        pass
    def on_cursor_finex_changed(self):
        pass
    def on_plot_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float], x2: Optional[float], y2: Optional[float]):
        pass
    def on_mark_datapoints_changed(self):
        pass
    def on_logx_changed(self):
        pass
    def on_logy_changed(self):
        pass
    def on_zoom_clicked(self, dx: int, dy: int):
        pass
    def on_statusbar_click(self):
        pass
    def on_filesys_toplevels_changed(self, paths: list[str]):
        pass
    def on_filesys_files_changed(self):
        pass
    def on_filesys_selection_changed(self):
        pass
    def on_filesys_contextmenu(self, path: PathExt, toplevel_path: PathExt, item_type: FilesysBrowserItemType):
        pass
    def on_xaxis_range_change(self):
        pass
    def on_yaxis_range_change(self):
        pass
    def on_color_change(self):
        pass
    def on_resize(self):
        pass
    def on_semitrans_changed(self):
        pass
    def on_traceopacity_changed(self):
        pass
    def on_maxlegend_changed(self):
        pass
