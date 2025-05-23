from .helpers.qt_helper import QtHelper
from .components.plot_widget import PlotWidget
from .components.statusbar import StatusBar
from .components.syntax_highlight import PythonSyntaxHighlighter
from .components.path_bar import PathBar
from .components.filesys_browser import FilesysBrowser, FilesysBrowserItemType
from .components.range_edit import RangeEdit
from .components.param_selector import ParamSelector
from .components.plot_selector import PlotSelector
from .components.sivalue_edit import SiValueEdit
from lib import AppPaths, PathExt, Parameters, Si, MainWindowLayout

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
        self._allow_plot_tool = True
        self._show_expressions = True
        self._layout = MainWindowLayout.Wide

        super().__init__()
        QtHelper.set_dialog_icon(self)
        
        self._build_main_menu()

        self._ui_ribbon = QWidget()

        palette = QPalette()
        color_base = palette.color(QPalette.ColorRole.Base).name()
        color_dark = palette.color(QPalette.ColorRole.Dark).name()
        color_light = palette.color(QPalette.ColorRole.Light).name()
        color_hl = palette.color(QPalette.ColorRole.Highlight).name()
        color_hl_text = palette.color(QPalette.ColorRole.HighlightedText).name()
        combo_arrow_image_url = os.path.join(AppPaths.get_resource_dir(), 'combo_arrow.svg').replace('\\', '/')
        print(combo_arrow_image_url)
        self._ui_ribbon.setStyleSheet(f"""
            QWidget {{
                background-color: {color_base};
                border-radius: 2px;
            }}
            QToolButton {{
                background-color: {color_base};
            }}
            QToolButton:checked {{
                background-color: {color_hl};
            }}
            QToolButton:hover {{
                background-color: {color_light};
            }}
            QToolButton:disabled {{
                background-color: {color_base};
                border-color: {color_base};
            }}
            QComboBox {{
                border-bottom: 1px solid {color_dark};
                border-radius: 0px;
            }}
            QComboBox:editable {{
                border: 1px solid {color_dark};
            }}
            QComboBox:editable:focus {{
                background-color: {color_light};
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
            frame.setStyleSheet(f'background: {color_dark};')
            frame.setFixedWidth(1)
            return frame
        self._ui_param_selector = ParamSelector(self)
        self._ui_param_selector.paramsChanged.connect(self.on_params_change)
        self._ui_param_selector.setGridSize(100)
        self._ui_plot_selector = PlotSelector(self)
        self._ui_plot_selector.valueChanged.connect(self.on_plottype_changed)
        self._ui_filter_button = QtHelper.make_button(self, None, self.on_show_filter, icon='toolbar_filter.svg', toolbar=True, tooltip='Select files that match a filter string (Ctrl+F)', shortcut='Ctrl+F')
        self._ui_refresh_button = QtHelper.make_button(self, None, self.on_update_plot, icon='toolbar_refresh.svg', toolbar=True, tooltip='Refresh Plot (F5)', shortcut='F5')
        self._ui_legend_button = QtHelper.make_button(self, None, self.on_show_legend, icon='toolbar_legend.svg', tooltip='Show Legend', toolbar=True, checked=False)
        self._ui_logx_button = QtHelper.make_button(self, None, self.on_logx_changed, icon='toolbar_log-x.svg', tooltip='Logarithmic X-Axis', toolbar=True, checked=False)
        self._ui_logy_button = QtHelper.make_button(self, None, self.on_logy_changed, icon='toolbar_log-y.svg', tooltip='Logarithmic Y-Axis', toolbar=True, checked=False)
        self._ui_lockx_button = QtHelper.make_button(self, None, self.on_lock_xaxis, icon='toolbar_lock-x.svg', tooltip='Lock X-Axis Scale', toolbar=True)
        self._ui_locky_button = QtHelper.make_button(self, None, self.on_lock_yaxis, icon='toolbar_lock-y.svg', tooltip='Lock Y-Axis Scale', toolbar=True)
        self._ui_lockboth_button = QtHelper.make_button(self, None, self.on_lock_both_axes, icon='toolbar_lock-both.svg', tooltip='Toggle X- and Y-Axis Scale Lock', toolbar=True)
        self._ui_pan_button = QtHelper.make_button(self, None, self._on_plottool_pan, icon='toolbar_pan.svg', tooltip='Pan-Tool for Plot', toolbar=True, checked=False)
        self._ui_zoom_button = QtHelper.make_button(self, None, self._on_plottool_zoom, icon='toolbar_zoom.svg', tooltip='Zoom-Tool for Plot', toolbar=True, checked=False)
        self._ui_mark_button = QtHelper.make_button(self, None, self.on_mark_datapoints_changed, icon='toolbar_mark-points.svg', tooltip='Mark Data Points', toolbar=True, checked=False)
        self._ui_save_image_button = QtHelper.make_button(self, None, self.on_save_plot_image, icon='toolbar_save-image.svg', tooltip='Save Image to File', toolbar=True)
        self._ui_copy_image_button = QtHelper.make_button(self, None, self.on_copy_image, icon='toolbar_copy-image.svg', tooltip='Copy Image to Clipboard', toolbar=True)
        self._ui_tabular_button = QtHelper.make_button(self, None, self.on_view_tabular, icon='toolbar_tabular.svg', tooltip='View/Copy/Save Tabular Data (Ctrl+T)', toolbar=True)
        self._ui_plaintext_button = QtHelper.make_button(self, None, self.on_view_plaintext, icon='toolbar_plaintext.svg', tooltip='View/Copy/Save Plaintext Data (Ctrl+P)', toolbar=True)
        self._ui_fileinfo_button = QtHelper.make_button(self, None, self.on_file_info, icon='toolbar_fileinfo.svg', tooltip='View Info About File (Ctrl+I)', toolbar=True)
        self._ui_xaxis_range = RangeEdit(self, any, any, False, True, [(any,any),(0,10e9)])
        self._ui_xaxis_range.rangeChanged.connect(self.on_xaxis_range_change)
        self._ui_yaxis_range = RangeEdit(self, any, any, False, True, [(any,any),(-25,+3),(-25,+25),(-50,+3),(-100,+3)])
        self._ui_yaxis_range.rangeChanged.connect(self.on_yaxis_range_change)
        self._ui_color_combo = QComboBox()
        self._ui_color_combo.setStyleSheet('QComboBox QAbstractItemView { min-width: 25ex; }')
        default_spacing, wide_spacing = 3, 10
        self._ui_ribbon.setLayout(QtHelper.layout_h(
            QtHelper.layout_v(...,
                self._ui_param_selector,
                ..., spacing=default_spacing,
            ),
            vline(),
            self._ui_plot_selector,
            vline(),
            QtHelper.layout_v(...,
                QtHelper.layout_h(self._ui_locky_button, self._ui_yaxis_range, self._ui_logy_button, ..., spacing=default_spacing),
                QtHelper.layout_h(self._ui_lockx_button, self._ui_xaxis_range, self._ui_logx_button, ..., spacing=default_spacing),
                QtHelper.layout_h(self._ui_lockboth_button, ..., spacing=default_spacing),
                ...,spacing=default_spacing
            ),
            vline(),
            QtHelper.layout_v(...,
                QtHelper.layout_h(
                    self._ui_legend_button,
                    self._ui_mark_button,
                    wide_spacing,
                    self._ui_refresh_button,
                    ...,spacing=default_spacing
                ),
                QtHelper.layout_h(
                    self._ui_pan_button,
                    self._ui_zoom_button,
                    ..., spacing=default_spacing
                ),
                QtHelper.layout_h(
                    'Color', self._ui_color_combo,
                    ...,spacing=default_spacing
                ),
                ...,spacing=default_spacing
            ),
            vline(),
            QtHelper.layout_v(...,
                QtHelper.layout_h(
                    self._ui_filter_button,
                    ...,spacing=default_spacing
                ),
                QtHelper.layout_h(
                    self._ui_tabular_button,
                    self._ui_plaintext_button,
                    self._ui_fileinfo_button,
                    ...,spacing=default_spacing
                ),
                QtHelper.layout_h(
                    self._ui_copy_image_button,
                    self._ui_save_image_button,
                    ...,spacing=default_spacing
                ),
                ..., spacing=default_spacing
            ),
            ..., spacing=wide_spacing
        ))
        self._ui_ribbon.setContentsMargins(0, 0, 0, 0)
        self._ui_ribbon.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._ui_plot = PlotWidget()
        self._ui_plot.setMinimumSize(150, 100)
        
        self._ui_tabs = QTabWidget()
        
        self._ui_files_tab = QWidget()
        self._ui_tabs.addTab(self._ui_files_tab, 'Files')
        self._ui_filesys_browser = FilesysBrowser()
        self._ui_filesys_browser.doubleClicked.connect(self.on_filesys_doubleclick)
        self._ui_filesys_browser.selectionChanged.connect(self.on_filesys_selection_changed)
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
        self._ui_editor = QTextEdit()
        self._ui_editor.document().setDefaultFont(self._ui_editor_font)
        self._ui_editor.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._ui_editor_highlighter = PythonSyntaxHighlighter(self._ui_editor.document())
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
        self._ui_auto_cursor_trace_check = QCheckBox('Auto Trace')
        self._ui_auto_cursor_trace_check.setChecked(True)
        self._ui_auto_cursor_trace_check.toggled.connect(self.on_auto_cursor_trace_changed)
        self._ui_cursor_syncx_check = QCheckBox('Sync X')
        self._ui_cursor_syncx_check.toggled.connect(self.on_cursor_syncx_changed)
        self._ui_cursor_edit_x1 = SiValueEdit(require_return_press=True)
        self._ui_cursor_edit_x1.setReadOnly(True)
        self._ui_cursor_edit_x1.valueChanged.connect(self.on_cursor_x1_changed)
        self._ui_cursor_readout_y1 = QLineEdit()
        self._ui_cursor_readout_y1.setReadOnly(True)
        self._ui_cursor_edit_x2 = SiValueEdit(require_return_press=True)
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
            [None, None, QtHelper.CellSpan(self._ui_cursor_syncx_check, cols=2)],
        ])
        cursor_layout.setColumnStretch(0, 1)
        cursor_layout.setColumnStretch(1, 4)
        cursor_layout.setColumnStretch(2, 0)
        cursor_layout.setColumnStretch(3, 4)
        cursor_layout.setColumnStretch(4, 0)
        cursor_layout.setColumnStretch(5, 4)
        self._ui_cursors_tab.setLayout(QtHelper.layout_v(cursor_layout,...))

        self._ui_status_bar = StatusBar()

        self._ui_main_container = QWidget()
        self._ui_main_container.setLayout(QVBoxLayout())
        self._ui_splitter = QSplitter()
        self._ui_splitter.addWidget(QWidget())
        self._ui_splitter.addWidget(QWidget())
        self._ui_secondary_container = QWidget()
        self._ui_secondary_container.setLayout(QVBoxLayout())

        self.setCentralWidget(QtHelper.layout_widget_v(
            self._ui_main_container,
            self._ui_status_bar,
        ))
        
        self._ui_splitter.splitterMoved.connect(self.on_resize)
        self._ui_tabs.currentChanged.connect(self.on_tab_change)
        self._ui_plot.attach(self.on_plot_mouse_event)
        self._ui_status_bar.clicked.connect(self.on_statusbar_click)

        self._update_layout()
    

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


    def resizeEvent(self, arg):
        result = super().resizeEvent(arg)
        self.on_resize()
        return result


    def _build_main_menu(self):
        self._ui_menu_bar = self.menuBar()
        self._ui_menu_bar.setContentsMargins(0, 0, 0, 0)
        
        self._ui_mainmenu_file = QtHelper.add_submenu(self._ui_menu_bar, '&File')
        self._ui_menuitem_loaddir_files = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Open Directory...', self.on_load_dir, shortcut='Ctrl+O')
        self._ui_menuitem_reload_all_files = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Reload All Files', self.on_reload_all_files, shortcut='Ctrl+F5')
        self._ui_mainmenu_recent = QtHelper.add_submenu(self._ui_mainmenu_file, 'Recent Directories', visible=False)
        self._ui_menuitem_recent_items = []
        self._ui_mainmenu_file.addSeparator()
        self._ui_menuitem_save_plot_image = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Save Plot Image...', self.on_save_plot_image)
        self._ui_mainmenu_file.addSeparator()
        self._ui_menuitem_file_info = QtHelper.add_menuitem(self._ui_mainmenu_file, 'File Info', self.on_file_info, shortcut='Ctrl+I')
        self._ui_menuitem_view_tabular = QtHelper.add_menuitem(self._ui_mainmenu_file, 'View/Copy/Export Tabular Data', self.on_view_tabular, shortcut='Ctrl+T')
        self._ui_menuitem_view_plain = QtHelper.add_menuitem(self._ui_mainmenu_file, 'View Plaintext Data', self.on_view_plaintext, shortcut='Ctrl+P')
        self._ui_menuitem_open_ext = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Open Externally', self.on_open_externally, shortcut='Ctrl+E')
        self._ui_mainmenu_file.addSeparator()
        self._ui_menuitem_load_expr = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Load Expressions...', self.on_load_expressions)
        self._ui_menuitem_save_expr = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Save Expressions...', self.on_save_expressions)
        self._ui_mainmenu_file.addSeparator()
        self._ui_menuitem_exit = QtHelper.add_menuitem(self._ui_mainmenu_file, 'Exit', self.close)
        
        self._ui_mainmenu_view = QtHelper.add_submenu(self._ui_menu_bar, '&View')
        self._ui_menuitem_hide_single_legend = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Hide Single-Item Legend', self.on_hide_single_legend, checkable=True)
        self._ui_menuitem_shorten_legend = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Shorten Legend Items', self.on_shorten_legend, checkable=True)
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_copy_image = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Copy Image to Clipboard', self.on_copy_image)
        self._ui_menuitem_view_tabular2 = QtHelper.add_menuitem(self._ui_mainmenu_view, 'View/Copy/Export Tabular Data...', self.on_view_tabular)

        self._ui_mainmenu_tools = QtHelper.add_submenu(self._ui_menu_bar, '&Tools')
        self._ui_menuitem_rlcalc = QtHelper.add_menuitem(self._ui_mainmenu_tools, 'Return Loss Integrator...', self.on_rl_calc)
        self._ui_mainmenu_tools.addSeparator()
        self._ui_menuitem_log = QtHelper.add_menuitem(self._ui_mainmenu_tools, 'Status Log', self.on_show_log, shortcut='Ctrl+L')
        self._ui_mainmenu_tools.addSeparator()
        self._ui_menuitem_settings = QtHelper.add_menuitem(self._ui_mainmenu_tools, 'Settings...', self.on_settings, shortcut='F4')

        self._ui_mainmenu_help = QtHelper.add_submenu(self._ui_menu_bar, '&Help')
        self._ui_menuitem_help = QtHelper.add_menuitem(self._ui_mainmenu_help, 'Help', self.on_help, shortcut='F1')
        self._ui_menuitem_about = QtHelper.add_menuitem(self._ui_mainmenu_help, 'About', self.on_about)
    
    
    def _on_plottool_pan(self):
        if not self._allow_plot_tool:
            self._ui_pan_button.setChecked(False)
            self._ui_zoom_button.setChecked(False)
            self._ui_plot.setTool(PlotWidget.Tool.Off)
            return
        self._ui_zoom_button.setChecked(False)
        self._ui_plot.setTool(self.ui_plot_tool)
    
    def _on_plottool_zoom(self):
        if not self._allow_plot_tool:
            self._ui_pan_button.setChecked(False)
            self._ui_zoom_button.setChecked(False)
            self._ui_plot.setTool(PlotWidget.Tool.Off)
            return
        self._ui_pan_button.setChecked(False)
        self._ui_plot.setTool(self.ui_plot_tool)


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


    @property
    def ui_allow_plot_tool(self) -> bool:
        return self._allow_plot_tool
    @ui_allow_plot_tool.setter
    def ui_allow_plot_tool(self, value: bool):
        self._allow_plot_tool = value
        if not value:
            self._ui_pan_button.setChecked(False)
            self._ui_zoom_button.setChecked(False)
            self._ui_plot.setTool(PlotWidget.Tool.Off)

    

    @property
    def ui_show_legend(self) -> bool:
        return self._ui_legend_button.isChecked()
    @ui_show_legend.setter
    def ui_show_legend(self, value: bool):
        self._ui_legend_button.setChecked(value)


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
        return self._ui_menuitem_shorten_legend.isChecked()
    @ui_shorten_legend.setter
    def ui_shorten_legend(self, value):
        self._ui_menuitem_shorten_legend.setChecked(value)
    

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
    def ui_xaxis_range(self) -> tuple[float,float]:
        return self._ui_xaxis_range.range()
    @ui_xaxis_range.setter
    def ui_xaxis_range(self, value: tuple[float,float]):
        self._ui_xaxis_range.setRange(*value)
    

    @property
    def ui_yaxis_range(self) -> tuple[float,float]:
        return self._ui_yaxis_range.range()
    @ui_yaxis_range.setter
    def ui_yaxis_range(self, value: tuple[float,float]):
        self._ui_yaxis_range.setRange(*value)


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
    def ui_cursor_x1(self) -> Si:
        return self._ui_cursor_edit_x1.value()

    
    @property
    def ui_cursor_x2(self) -> Si:
        return self._ui_cursor_edit_x2.value()

    
    def ui_set_cursor_readouts(self, x1: Si|None = None, y1: str = '', x2: Si|None = None, y2: str = '', dx: str = '', dy: str = ''):
        self._ui_cursor_edit_x1.setValue(x1)
        self._ui_cursor_edit_x1.setReadOnly(x1 is None)
        self._ui_cursor_readout_y1.setText(y1)
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
        self._ui_cursor1_trace_combo.setCurrentText(value)

    
    @property
    def ui_cursor2_trace(self) -> str:
        return self._ui_cursor2_trace_combo.currentText()
    @ui_cursor2_trace.setter
    def ui_cursor2_trace(self, value: int):
        self._ui_cursor2_trace_combo.setCurrentText(value)

    
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


    def ui_show_status_message(self, message: str|None = None, level: int = logging.INFO):
        self._ui_status_bar.setMessage(message, level)


    def ui_update_files_history(self, texts_and_callbacks: list[tuple[str,Callable]]):
        
        self._ui_menuitem_recent_items.clear()
        self._ui_mainmenu_recent.clear()

        for (text,callback) in texts_and_callbacks:
            new_item = QtHelper.add_menuitem(self._ui_mainmenu_recent, text, callback)
            self._ui_menuitem_recent_items.append(new_item)
        
        self._ui_mainmenu_recent.setEnabled(len(self._ui_menuitem_recent_items) > 0)


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
    def on_plot_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float], x2: Optional[float], y2: Optional[float]):
        pass
    def on_mark_datapoints_changed(self):
        pass
    def on_logx_changed(self):
        pass
    def on_logy_changed(self):
        pass
    def on_statusbar_click(self):
        pass
    def on_filesys_files_changed(self):
        pass
    def on_filesys_selection_changed(self):
        pass
    def on_filesys_doubleclick(self, path: PathExt, toplevel_path: PathExt, item_type: FilesysBrowserItemType):
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
