from .helpers.qt_helper import QtHelper
from .helpers.plot_widget import PlotWidget
from .helpers.statusbar import StatusBar
from .helpers.syntax_highlight import PythonSyntaxHighlighter
from .helpers.path_bar import PathBar
from .helpers.filesys_browser import FilesysBrowser, FilesysBrowserItemType
from .helpers.range_edit import RangeEdit
from lib import AppPaths, PathExt
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
from typing import Callable, Optional, Union



class MainWindowUi(QMainWindow):

    class Tab(enum.Enum):
        Files = enum.auto()
        Expressions = enum.auto()
        Cursors = enum.auto()


    def __init__(self):
        self._ui_timers: dict[any,tuple[QTimer,Callable]] = {}

        super().__init__()
        QtHelper.set_dialog_icon(self)
        
        self._build_main_menu()

        
        self._ui_ribbon = QTabWidget()
        color_base = QPalette().color(QPalette.ColorRole.Base).name()
        color_dark = QPalette().color(QPalette.ColorRole.Dark).name()
        color_light = QPalette().color(QPalette.ColorRole.Light).name()
        color_hl = QPalette().color(QPalette.ColorRole.Highlight).name()
        color_hl_text = QPalette().color(QPalette.ColorRole.HighlightedText).name()
        self._ui_ribbon.setStyleSheet(f"""
            QTabWidget::pane {{
                background-color: {color_base};
                border: 0;
            }}
            QPushButton {{
                background-color: {color_base};
            }}
            QPushButton:hover {{
                background-color: {color_light};
            }}
            QPushButton:checked {{
                background-color: {color_hl};
                color: {color_hl_text};
            }}
            """)
        self._ui_ribbon.setContentsMargins(0, 0, 0, 0)
        view_ribbon = QWidget()
        view_ribbon.setContentsMargins(0, 0, 0, 0)
        self._ui_ribbon.addTab(view_ribbon, 'View')
        self._ui_logx_button = QtHelper.make_button(self, 'Log X', self.on_logx_changed, flat=True, checked=False)
        self._ui_xaxis_range = RangeEdit(self, any, any, False, True, [(any,any),(0,10e9)])
        self._ui_yaxis_range = RangeEdit(self, any, any, False, True, [(any,any),(+3,-25),(-25,+25),(+3,-50),(+3,-100)])
        view_ribbon.setLayout(QtHelper.layout_h(
            QtHelper.make_button(self, 'Filter...', self.on_show_filter, flat=True, tooltip='Select files that match a filter string (Ctrl+F)', shortcut='Ctrl+F'),
            QtHelper.layout_grid([
                ['X', self._ui_xaxis_range, QtHelper.layout_h(self._ui_logx_button, ...)],
                ['Y', self._ui_yaxis_range, QtHelper.layout_h(...)],
            ]),
            ...,
            dense=True
        ))

        
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter_top = QWidget()
        splitter.addWidget(splitter_top)
        splitter.setCollapsible(0, False)
        splitter_bottom = QWidget()
        splitter.addWidget(splitter_bottom)
        splitter.setCollapsible(1, False)
        self.setCentralWidget(splitter)

        self._ui_plot = PlotWidget()
        
        self._ui_mode_combo = QComboBox()
        self._ui_mode_combo.setToolTip('Select which parameter to plot')
        self._ui_unit_combo = QComboBox()
        self._ui_unit_combo.setToolTip('Select how to plot the selected parameter (primary Y-axis)')
        self._ui_unit2_combo = QComboBox()
        self._ui_unit2_combo.setToolTip('Select how to plot the selected parameter (secondary Y-axis)')
        
        self._ui_tabs = QTabWidget()
        
        files_tab = QWidget()
        self._ui_tabs.addTab(files_tab, 'Files')
        self._ui_filesys_browser = FilesysBrowser()
        self._ui_filesys_browser.doubleClicked.connect(self.on_filesys_doubleclick)
        self._ui_filesys_browser.selectionChanged.connect(self.on_filesys_selection_changed)
        self._ui_filesys_browser.filesChanged.connect(self.on_filesys_files_changed)
        self._ui_filesys_browser.contextMenuRequested.connect(self.on_filesys_contextmenu)
        files_tab.setLayout(QtHelper.layout_h(self._ui_filesys_browser))
        
        expressions_tab = QWidget()
        self._ui_tabs.addTab(expressions_tab, 'Expressions')
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
        expressions_tab.setLayout(QtHelper.layout_h(
            QtHelper.layout_v(
                self._ui_update_button,
                self._ui_template_button,
                5,
                self._ui_help_button,
                ...
            ),
            self._ui_editor
        ))
        
        cursors_tab = QWidget()
        self._ui_tabs.addTab(cursors_tab, 'Cursors')
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
        self._ui_cursor_readout_x1 = QLineEdit()
        self._ui_cursor_readout_x1.setReadOnly(True)
        self._ui_cursor_readout_y1 = QLineEdit()
        self._ui_cursor_readout_y1.setReadOnly(True)
        self._ui_cursor_readout_x2 = QLineEdit()
        self._ui_cursor_readout_x2.setReadOnly(True)
        self._ui_cursor_readout_y2 = QLineEdit()
        self._ui_cursor_readout_y2.setReadOnly(True)
        self._ui_cursor_readout_dx = QLineEdit()
        self._ui_cursor_readout_dx.setReadOnly(True)
        self._ui_cursor_readout_dy = QLineEdit()
        self._ui_cursor_readout_dy.setReadOnly(True)
        cursor_layout = QtHelper.layout_grid([
            [self._ui_cursor1_radio, self._ui_cursor1_trace_combo, 'X1:', self._ui_cursor_readout_x1, 'Y1:', self._ui_cursor_readout_y1],
            [self._ui_cursor2_radio, self._ui_cursor2_trace_combo, 'X2:', self._ui_cursor_readout_x2, 'Y2:', self._ui_cursor_readout_y2],
            [self._ui_auto_cursor_check, self._ui_auto_cursor_trace_check, 'ΔX:', self._ui_cursor_readout_dx, 'ΔY:', self._ui_cursor_readout_dy],
            [None, None, QtHelper.CellSpan(self._ui_cursor_syncx_check, cols=2)],
        ])
        cursor_layout.setColumnStretch(0, 1)
        cursor_layout.setColumnStretch(1, 4)
        cursor_layout.setColumnStretch(2, 0)
        cursor_layout.setColumnStretch(3, 4)
        cursor_layout.setColumnStretch(4, 0)
        cursor_layout.setColumnStretch(5, 4)
        cursors_tab.setLayout(cursor_layout)

        self._ui_status_bar = StatusBar()
        self._ui_status_bar.clicked.connect(self.on_statusbar_click)

        splitter_top.setLayout(QtHelper.layout_v(self._ui_ribbon, self._ui_plot))
        splitter_bottom.setLayout(QtHelper.layout_v(
            QtHelper.layout_h(self._ui_mode_combo, self._ui_unit_combo, self._ui_unit2_combo),
            self._ui_tabs,
            self._ui_status_bar,
        ))
        
        self._ui_tabs.currentChanged.connect(self.on_tab_change)

        #def on_plot_mouse_event(left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float]):
        #    self.on_plot_mouse_event(left_btn_pressed, left_btn_event, x, y)
        self.ui_plot.attach(self.on_plot_mouse_event)


    def _build_main_menu(self):
        self.ui_menu_bar = self.menuBar()
        
        self._ui_mainmenu_file = QtHelper.add_submenu(self.ui_menu_bar, '&File')
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
        
        self._ui_mainmenu_view = QtHelper.add_submenu(self.ui_menu_bar, '&View')
        self._ui_menuitem_filter = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Filter Files...', self.on_show_filter, shortcut='Ctrl+F')
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_show_legend = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Show Legend', self.on_show_legend, checkable=True)
        self._ui_menuitem_hide_single_legend = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Hide Single-Item Legend', self.on_hide_single_legend, checkable=True)
        self._ui_menuitem_shorten_legend = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Shorten Legend Items', self.on_shorten_legend, checkable=True)
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_copy_image = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Copy Image to Clipboard', self.on_copy_image)
        self._ui_menuitem_view_tabular2 = QtHelper.add_menuitem(self._ui_mainmenu_view, 'View/Copy/Export Tabular Data...', self.on_view_tabular)
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_lock_x = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Lock X-Axis Scale', self.on_lock_xaxis, checkable=True)
        self._ui_menuitem_lock_y = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Lock Y-Axis Scale', self.on_lock_yaxis, checkable=True)
        self._ui_menuitem_lock_xy = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Lock Both Axis Scales', self.on_lock_both)
        self._ui_menuitem_unlock_axes = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Unlock Both Axis Scales', self.on_unlock_axes)
        self._ui_menuitem_rescale_axes = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Re-Scale Locked Axis Scales', self.on_rescale_locked_axes)
        self._ui_menuitem_manual_axes = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Manual Axis Scale Limits...', self.on_manual_axes, shortcut='Ctrl+X')
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_logx = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Logarithmic X-Axis', self.on_logx_changed, checkable=True)
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_mark = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Mark Data Points', self.on_mark_datapoints_changed, checkable=True)
        self._ui_menuitem_mark.toggled.connect(self.on_mark_datapoints_changed)
        self._ui_mainmenu_view.addSeparator()
        self._ui_menuitem_update_expr = QtHelper.add_menuitem(self._ui_mainmenu_view, 'Update Plot from Expressions', self.on_update_expressions, shortcut='F5')

        self._ui_mainmenu_tools = QtHelper.add_submenu(self.ui_menu_bar, '&Tools')
        self._ui_menuitem_rlcalc = QtHelper.add_menuitem(self._ui_mainmenu_tools, 'Return Loss Integrator...', self.on_rl_calc)
        self._ui_mainmenu_tools.addSeparator()
        self._ui_menuitem_log = QtHelper.add_menuitem(self._ui_mainmenu_tools, 'Status Log', self.on_log, shortcut='Ctrl+L')
        self._ui_mainmenu_tools.addSeparator()
        self._ui_menuitem_settings = QtHelper.add_menuitem(self._ui_mainmenu_tools, 'Settings...', self.on_settings, shortcut='F4')

        self._ui_mainmenu_help = QtHelper.add_submenu(self.ui_menu_bar, '&Help')
        self._ui_menuitem_help = QtHelper.add_menuitem(self._ui_mainmenu_help, 'Help', self.on_help, shortcut='F1')
        self._ui_menuitem_about = QtHelper.add_menuitem(self._ui_mainmenu_help, 'About', self.on_about)


    def ui_show(self):
        super().show()


    def ui_show_template_menu(self, items: list[tuple[str,Callable|list]]):
        button_pos = self._ui_template_button.mapToGlobal(QPoint(0, self._ui_template_button.height()))
        QtHelper.show_popup_menu(self, items, button_pos)

    
    def ui_set_window_title(self, title: str):
        self.setWindowTitle(title)

    
    def ui_set_modes_list(self, items: list[str]):
        self._ui_mode_combo.clear()
        for item in items:
            self._ui_mode_combo.addItem(item)
        self._ui_mode_combo.currentTextChanged.connect(self.on_select_mode)

    
    def ui_set_units_list(self, items: list[str]):
        self._ui_unit_combo.clear()
        for item in items:
            self._ui_unit_combo.addItem(item)
        self._ui_unit_combo.currentTextChanged.connect(self.on_select_unit)

    
    def ui_set_units2_list(self, items: list[str]):
        self._ui_unit2_combo.clear()
        for item in items:
            self._ui_unit2_combo.addItem(item)
        self._ui_unit2_combo.currentTextChanged.connect(self.on_select_unit2)


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
    def ui_show_legend(self) -> bool:
        return self._ui_menuitem_show_legend.isChecked()
    @ui_show_legend.setter
    def ui_show_legend(self, value: bool):
        self._ui_menuitem_show_legend.setChecked(value)


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
    def ui_lock_x(self) -> bool:
        return self._ui_menuitem_lock_x.isChecked()
    @ui_lock_x.setter
    def ui_lock_x(self, value):
        self._ui_menuitem_lock_x.setChecked(value)
    

    @property
    def ui_lock_y(self) -> bool:
        return self._ui_menuitem_lock_y.isChecked()
    @ui_lock_y.setter
    def ui_lock_y(self, value):
        self._ui_menuitem_lock_y.setChecked(value)
    

    @property
    def ui_mark_datapoints(self) -> bool:
        return self._ui_menuitem_mark.isChecked()
    @ui_mark_datapoints.setter
    def ui_mark_datapoints(self, value):
        self._ui_menuitem_mark.setChecked(value)
    

    @property
    def ui_logx(self) -> bool:
        #return self._ui_menuitem_logx.isChecked()
        return self._ui_logx_button.isChecked()
    @ui_logx.setter
    def ui_logx(self, value):
        #self._ui_menuitem_logx.setChecked(value)
        self._ui_logx_button.setChecked(value)


    @property
    def ui_expression(self) -> str:
        return self._ui_editor.toPlainText()
    @ui_expression.setter
    def ui_expression(self, expression: str):
        self._ui_editor.setText(expression)
        self._ui_editor.document().setDefaultFont(self._ui_editor_font)


    @property
    def ui_mode(self) -> str:
        return self._ui_mode_combo.currentText()
    @ui_mode.setter
    def ui_mode(self, mode: str):
        self._ui_mode_combo.setCurrentText(mode)


    @property
    def ui_unit(self) -> str:
        return self._ui_unit_combo.currentText()
    @ui_unit.setter
    def ui_unit(self, unit: str):
        self._ui_unit_combo.setCurrentText(unit)


    @property
    def ui_unit2(self) -> str:
        return self._ui_unit2_combo.currentText()
    @ui_unit2.setter
    def ui_unit2(self, unit2: str):
        self._ui_unit2_combo.setCurrentText(unit2)


    def ui_set_cursor_trace_list(self, traces: list[str]):
        for combo in [self._ui_cursor1_trace_combo, self._ui_cursor2_trace_combo]:
            combo.clear()
            for trace in traces:
                combo.addItem(trace)
    

    def ui_set_cursor_readouts(self, x1: str = '', y1: str = '', x2: str = '', y2: str = '', dx: str = '', dy: str = ''):
        self._ui_cursor_readout_x1.setText(x1)
        self._ui_cursor_readout_y1.setText(y1)
        self._ui_cursor_readout_x2.setText(x2)
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


    def ui_update_status_message(self, status_message: str):
        if status_message:
            self._ui_status_bar.showMessage(status_message)
        else:
            self._ui_status_bar.clearMessage()


    def ui_update_files_history(self, texts_and_callbacks: list[tuple[str,Callable]]):
        
        self._ui_menuitem_recent_items.clear()
        self._ui_mainmenu_recent.clear()

        for (text,callback) in texts_and_callbacks:
            new_item = QtHelper.add_menuitem(self._ui_mainmenu_recent, text, callback)
            self._ui_menuitem_recent_items.append(new_item)
        
        self._ui_mainmenu_recent.setEnabled(len(self._ui_menuitem_recent_items) > 0)


    # to be implemented in derived class
    def on_select_mode(self):
        pass
    def on_select_unit(self):
        pass
    def on_select_unit2(self):
        pass
    def on_show_filter(self):
        pass
    def on_reload_all_files(self):
        pass
    def on_rl_calc(self):
        pass
    def on_log(self):
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
    def on_lock_both(self):
        pass
    def on_unlock_axes(self):
        pass
    def on_rescale_locked_axes(self):
        pass
    def on_manual_axes(self):
        pass
    def on_update_expressions(self):
        pass
    def on_template_button(self):
        pass
    def on_help_button(self):
        pass
    def on_tab_change(self):
        pass
    def on_cursor_select(self):
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
    def on_timer_timeout(self, identifier):
        pass
    def on_mark_datapoints_changed(self):
        pass
    def on_logx_changed(self):
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
