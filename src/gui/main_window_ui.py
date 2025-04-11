from .qt_helper import QtHelper
from lib import AppGlobal
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



class MyNavigationToolbar(NavigationToolbar2QT):
    toolitems = [toolitem for toolitem in NavigationToolbar2QT.toolitems if toolitem[0] in ('Home', 'Pan', 'Zoom')]


class Mode(enum.IntEnum):
    All = 0
    AllFwd = 1
    IL = 2
    IlFwd = 3
    S21 = 4
    RL = 5
    S11 = 6
    S22 = 7
    S33 = 8
    S44 = 9
    Expr = 10

MODE_NAMES = {
    Mode.All: 'All S-Parameters',
    Mode.AllFwd: 'All S-Parameters (reciprocal)',
    Mode.IL: 'Insertion Loss',
    Mode.IlFwd: 'Insertion Loss (reciprocal)',
    Mode.S21: 'Insertion Loss S21',
    Mode.RL: 'Return Loss / Impedance',
    Mode.S11: 'Return Loss S11',
    Mode.S22: 'Return Loss S22',
    Mode.S33: 'Return Loss S33',
    Mode.S44: 'Return Loss S44',
    Mode.Expr: 'Expression-Based',
}

class Unit(enum.IntEnum):
    Off = 0
    dB = 1
    LinMag = 2
    LogMag = 3
    ReIm = 4
    Real = 5
    Imag = 6
    ReImPolar = 7
    SmithZ = 8
    SmithY = 9
    Impulse = 10
    Step = 11


UNIT_NAMES = {
    Unit.Off: ' ',
    Unit.dB: 'dB',
    Unit.LinMag: 'Lin Mag',
    Unit.LogMag: 'Log Mag',
    Unit.ReIm: 'Real+Imag',
    Unit.Real: 'Real',
    Unit.Imag: 'Imag',
    Unit.ReImPolar: 'Polar',
    Unit.SmithY: 'Smith (Z)',
    Unit.SmithZ: 'Smith (Y)',
    Unit.Impulse: 'Impulse Resp.',
    Unit.Step: 'Step Resp.',
}

class Unit2(enum.IntEnum):
    Off = 0
    Phase = 1
    Unwrap = 2
    LinRem = 3
    GDelay = 4

UNIT2_NAMES = {
    Unit2.Off: ' ',
    Unit2.Phase: 'Phase',
    Unit2.Unwrap: 'Unwrapped',
    Unit2.LinRem: 'Lin. Removed',
    Unit2.GDelay: 'Group Delay',
}


class MainWindowUi(QMainWindow):

    def __init__(self):
        super().__init__()
        QtHelper.set_dialog_icon(self)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)
        self._build_main_menu()

        plot_layout = QVBoxLayout()
        self.ui_figure = Figure()
        self.ui_canvas = FigureCanvasQTAgg(self.ui_figure)
        plot_layout.addWidget(self.ui_canvas)
        plot_toolbar = MyNavigationToolbar(self.ui_canvas, self)
        plot_layout.addWidget(plot_toolbar)
        plot_layout_widget = QWidget()
        plot_layout_widget.setLayout(plot_layout)
        plot_layout_widget.setMinimumSize(200, 150)
        splitter.addWidget(plot_layout_widget)
        
        bottom_widget = QWidget()
        bottom_widget_layout = QVBoxLayout()
        bottom_widget.setLayout(bottom_widget_layout)
        splitter.addWidget(bottom_widget)

        self.ui_mode_combo = QComboBox()
        self.ui_unit_combo = QComboBox()
        self.ui_unit2_combo = QComboBox()
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.ui_mode_combo)
        combo_layout.addWidget(self.ui_unit_combo)
        combo_layout.addWidget(self.ui_unit2_combo)
        bottom_widget_layout.addLayout(combo_layout)
        for mode in Mode:
            self.ui_mode_combo.addItem(MODE_NAMES[mode.value])
        self.ui_mode_combo.currentIndexChanged.connect(self.on_select_mode)
        for unit in Unit:
            self.ui_unit_combo.addItem(UNIT_NAMES[unit.value])
        self.ui_unit_combo.currentIndexChanged.connect(self.on_select_unit)
        for unit2 in Unit2:
            self.ui_unit2_combo.addItem(UNIT2_NAMES[unit2.value])
        self.ui_unit2_combo.currentIndexChanged.connect(self.on_select_unit2)
        
        tabs = QTabWidget()
        bottom_widget_layout.addWidget(tabs)
        
        files_tab = QWidget()
        tabs.addTab(files_tab, 'Files')
        expressions_tab = QWidget()
        tabs.addTab(expressions_tab, 'Expressions')

        filesview_layout = QVBoxLayout()
        self.ui_fileview = QTreeView()
        filesview_layout.addWidget(self.ui_fileview)
        files_tab.setLayout(filesview_layout)
        
        self.ui_filemodel = QStandardItemModel()
        self.ui_filemodel.setHorizontalHeaderLabels(['File', 'Properties'])
        self.ui_fileview_root = self.ui_filemodel.invisibleRootItem()
        self.ui_fileview.setModel(self.ui_filemodel)
        self.ui_fileview.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self.ui_fileview.selectionModel().selectionChanged.connect(self.on_select_file)
        
        expressions_layout = QHBoxLayout()
        exprbuttons_layout = QVBoxLayout()
        expressions_layout.addLayout(exprbuttons_layout)
        self.ui_editor = QPlainTextEdit()
        self.template_button = QPushButton('Template...')
        exprbuttons_layout.addWidget(self.template_button)
        exprbuttons_layout.addStretch()
        self.ui_editor.setFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self.ui_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        editor_layout = QVBoxLayout()
        editor_layout.addWidget(self.ui_editor)
        expressions_layout.addLayout(editor_layout)
        expressions_tab.setLayout(expressions_layout)

        self.ui_status_bar = QStatusBar()
        bottom_widget_layout.addWidget(self.ui_status_bar)

        def on_template_button():
            button_pos = self.template_button.mapToGlobal(QPoint(0, self.template_button.height()))
            self.ui_template_menu.popup(button_pos)
        self.template_button.clicked.connect(on_template_button)
        self._build_template_menu()

        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
    

    def _build_main_menu(self):
        self.ui_menu_bar = self.menuBar()
        
        self.ui_mainmenu_file = QtHelper.add_submenu(self, self.ui_menu_bar, '&File')
        self.ui_menuitem_open_dir = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Open Directory...', self.on_open_directory, shortcut='Ctrl+O')
        self.ui_menuitem_append_dir = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Append Directory...', self.on_append_directory)
        self.ui_menuitem_reload_all_files = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Reload All Files', self.on_reload_all_files)
        self.ui_mainmenu_recent = QtHelper.add_submenu(self, self.ui_mainmenu_file, 'Recent Directories', visible=False)
        self.ui_menuitem_recent_items = []
        self.ui_mainmenu_file.addSeparator()
        self.ui_menuitem_save_plot_image = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Save Plot Image...', self.on_save_plot_image)
        self.ui_mainmenu_file.addSeparator()
        self.ui_menuitem_file_info = QtHelper.add_menuitem(self.ui_mainmenu_file, 'File Info', self.on_file_info, shortcut='Ctrl+I')
        self.ui_menuitem_view_tabular = QtHelper.add_menuitem(self.ui_mainmenu_file, 'View/Export Tabular Data', self.on_view_tabular, shortcut='Ctrl+T')
        self.ui_menuitem_open_ext = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Open Externally', self.on_open_externally, shortcut='Ctrl+E')
        self.ui_mainmenu_file.addSeparator()
        self.ui_menuitem_load_expr = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Load Expressions...', self.on_load_expressions)
        self.ui_menuitem_save_expr = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Save Expressions...', self.on_save_expressions)
        self.ui_mainmenu_file.addSeparator()
        self.ui_menuitem_exit = QtHelper.add_menuitem(self.ui_mainmenu_file, 'Exit', self.close)
        
        self.ui_mainmenu_view = QtHelper.add_submenu(self, self.ui_menu_bar, '&View')
        self.ui_menuitem_filter = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Filter Files...', self.on_show_filter, shortcut='Ctrl+F')
        self.ui_mainmenu_view.addSeparator()
        self.ui_menuitem_show_legend: QAction = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Show Legend', self.on_show_legend, checkable=True)
        self.ui_menuitem_hide_single_legend: QAction = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Hide Single-Item Legend', self.on_hide_single_legend, checkable=True)
        self.ui_menuitem_shorten_legend: QAction = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Shorten Legend Items', self.on_shorten_legend, checkable=True)
        self.ui_mainmenu_view.addSeparator()
        self.ui_menuitem_copy_image = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Copy Image to Clipboard', self.on_copy_image)
        self.ui_mainmenu_view.addSeparator()
        self.ui_menuitem_lock_x: QAction = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Lock X-Axis Scale', self.on_lock_xaxis, checkable=True)
        self.ui_menuitem_lock_y: QAction = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Lock Y-Axis Scale', self.on_lock_yaxis, checkable=True)
        self.ui_menuitem_lock_xy = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Lock Both Axis Scales', self.on_lock_both)
        self.ui_menuitem_unlock_axes = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Unlock Both Axis Scales', self.on_unlock_axes)
        self.ui_menuitem_rescale_axes = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Re-Scale Locked Axis Scales', self.on_rescale_locked_axes)
        self.ui_menuitem_manual_axes = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Manual Axis Scale Limits...', self.on_manual_axes, shortcut='Ctrl+X')
        self.ui_mainmenu_view.addSeparator()
        self.ui_menuitem_update_expr = QtHelper.add_menuitem(self.ui_mainmenu_view, 'Update Plot from Expressions', self.on_update_expressions, shortcut='F5')

        self.ui_mainmenu_tools = QtHelper.add_submenu(self, self.ui_menu_bar, '&Tools')
        self.ui_menuitem_cursrs = QtHelper.add_menuitem(self.ui_mainmenu_tools, 'Trace Cursors...', self.on_trace_cursors, shortcut='F3')
        self.ui_menuitem_rlcalc = QtHelper.add_menuitem(self.ui_mainmenu_tools, 'Return Loss Integrator...', self.on_rl_calc)
        self.ui_mainmenu_tools.addSeparator()
        self.ui_menuitem_log = QtHelper.add_menuitem(self.ui_mainmenu_tools, 'Status Log', self.on_log)
        self.ui_mainmenu_tools.addSeparator()
        self.ui_menuitem_settings = QtHelper.add_menuitem(self.ui_mainmenu_tools, 'Settings...', self.on_settings, shortcut='F4')

        self.ui_mainmenu_help = QtHelper.add_submenu(self, self.ui_menu_bar, '&Help')
        self.ui_menuitem_help = QtHelper.add_menuitem(self.ui_mainmenu_help, 'Help', self.on_help, shortcut='F1')
        self.ui_menuitem_about = QtHelper.add_menuitem(self.ui_mainmenu_help, 'About', self.on_about)


    def _build_template_menu(self):
        self.ui_template_menu = QMenu()
        self.ui_template_menuitem_example1 = QtHelper.add_menuitem(self.ui_template_menu, 'Example 1', None)
        self.ui_template_menu.addSeparator()
        self.template_submenu_more = QtHelper.add_submenu(self, self.ui_template_menu, 'More Examples')
        self.ui_template_menuitem_example2 =  QtHelper.add_menuitem(self.ui_template_menu, 'Example 2', None)

    
    def ui_update_window_title(self, title: str):
        self.setWindowTitle(title)
    

    @property
    def ui_show_legend(self) -> bool:
        return self.ui_menuitem_show_legend.isChecked()
    @ui_show_legend.setter
    def ui_show_legend(self, value):
        self.ui_menuitem_show_legend.setChecked(value)
    

    @property
    def ui_hide_single_item_legend(self) -> bool:
        return self.ui_menuitem_hide_single_legend.isChecked()
    @ui_hide_single_item_legend.setter
    def ui_hide_single_item_legend(self, value):
        self.ui_menuitem_hide_single_legend.setChecked(value)
    

    @property
    def ui_shorten_legend(self) -> bool:
        return self.ui_menuitem_shorten_legend.isChecked()
    @ui_shorten_legend.setter
    def ui_shorten_legend(self, value):
        self.ui_menuitem_shorten_legend.setChecked(value)
    

    @property
    def ui_lock_x(self) -> bool:
        return self.ui_menuitem_lock_x.isChecked()
    @ui_lock_x.setter
    def ui_lock_x(self, value):
        self.ui_menuitem_lock_x.setChecked(value)
    

    @property
    def ui_lock_y(self) -> bool:
        return self.ui_menuitem_lock_y.isChecked()
    @ui_lock_y.setter
    def ui_lock_y(self, value):
        self.ui_menuitem_lock_y.setChecked(value)


    @property
    def ui_expression(self) -> str:
        return self.ui_editor.toPlainText()
    @ui_expression.setter
    def ui_expression(self, expression: str):
        return self.ui_editor.setPlainText(expression)


    @property
    def ui_mode(self) -> Mode:
        return Mode(self.ui_mode_combo.currentIndex())
    @ui_mode.setter
    def ui_mode(self, mode: Mode):
        self.ui_mode_combo.setCurrentIndex(int(mode.value))


    @property
    def ui_unit(self) -> Unit:
        return Unit(self.ui_unit_combo.currentIndex())
    @ui_unit.setter
    def ui_unit(self, unit: Unit):
        self.ui_unit_combo.setCurrentIndex(int(unit.value))


    @property
    def ui_unit2(self) -> Unit2:
        return Unit2(self.ui_unit2_combo.currentIndex())
    @ui_unit2.setter
    def ui_unit2(self, unit2: Unit2):
        self.ui_unit2_combo.setCurrentIndex(int(unit2.value))


    def ui_update_status_message(self, status_message: str):
        if status_message:
            self.ui_status_bar.showMessage(status_message)
        else:
            self.ui_status_bar.clearMessage()


    def ui_set_fileview_items(self, names_and_contents: list[tuple[str,str]]):
        self.ui_fileview_root.removeRows(0, self.ui_fileview_root.rowCount())
        for name,content in names_and_contents:
            self.ui_fileview_root.appendRow([QStandardItem(name), QStandardItem(content)])
        for column in range(self.ui_fileview.model().columnCount()):
            self.ui_fileview.resizeColumnToContents(column)


    def ui_update_fileview_item(self, index: int, name: str, contents: str):
        self.ui_fileview.model().itemFromIndex(self.ui_fileview.model().index(index, 0)).setText(name)
        self.ui_fileview.model().itemFromIndex(self.ui_fileview.model().index(index, 1)).setText(contents)


    def ui_select_fileview_items(self, indices: list[int]):
        self.ui_fileview.selectionModel().clearSelection()
        for index_to_select in indices:
            index = self.ui_fileview.model().index(index_to_select, 0)
            self.ui_fileview.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)


    def ui_get_selected_fileview_indices(self) -> list[int]:
        sel = self.ui_fileview.selectionModel().selectedIndexes()
        if not sel:
            return []
        return list(set([item.row() for item in sel]))


    def ui_update_files_history(self, texts_and_callbacks: list[tuple[str,Callable]]):
        self.ui_menuitem_recent_items.clear()
        self.ui_mainmenu_recent.clear()
        if len(texts_and_callbacks) <= 0:
            self.ui_mainmenu_recent.setVisible(False)
            return
        for (text,callback) in texts_and_callbacks:
            item = QtHelper.add_menuitem(self.ui_mainmenu_recent, text, callback)
            self.ui_menuitem_recent_items.append(item)
        self.ui_mainmenu_recent.setVisible(True)


    def on_select_mode(self):
        raise NotImplementedError()
    def on_select_unit(self):
        raise NotImplementedError()
    def on_select_unit2(self):
        raise NotImplementedError()
    def on_show_filter(self):
        raise NotImplementedError()
    def on_select_file(self):
        raise NotImplementedError()
    def on_open_directory(self):
        raise NotImplementedError()
    def on_append_directory(self):
        raise NotImplementedError()
    def on_reload_all_files(self):
        raise NotImplementedError()
    def on_trace_cursors(self):
        raise NotImplementedError()
    def on_rl_calc(self):
        raise NotImplementedError()
    def on_log(self):
        raise NotImplementedError()
    def on_settings(self):
        raise NotImplementedError()
    def on_help(self):
        raise NotImplementedError()
    def on_about(self):
        raise NotImplementedError()
    def on_save_plot_image(self):
        raise NotImplementedError()
    def on_file_info(self):
        raise NotImplementedError()
    def on_view_tabular(self):
        raise NotImplementedError()
    def on_open_externally(self):
        raise NotImplementedError()
    def on_load_expressions(self):
        raise NotImplementedError()
    def on_save_expressions(self):
        raise NotImplementedError()
    def on_show_legend(self):
        raise NotImplementedError()
    def on_hide_single_legend(self):
        raise NotImplementedError()
    def on_shorten_legend(self):
        raise NotImplementedError()
    def on_copy_image(self):
        raise NotImplementedError()
    def on_lock_xaxis(self):
        raise NotImplementedError()
    def on_lock_yaxis(self):
        raise NotImplementedError()
    def on_lock_both(self):
        raise NotImplementedError()
    def on_unlock_axes(self):
        raise NotImplementedError()
    def on_rescale_locked_axes(self):
        raise NotImplementedError()
    def on_manual_axes(self):
        raise NotImplementedError()
    def on_update_expressions(self):
        raise NotImplementedError()
