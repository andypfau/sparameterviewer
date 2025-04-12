from .qt_helper import QtHelper
from .plot_widget import PlotWidget
from lib import AppPaths
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



class MainWindowUi(QMainWindow):

    def __init__(self):
        super().__init__()
        QtHelper.set_dialog_icon(self)
        
        self._build_main_menu()

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
        self._ui_mode_combo.currentTextChanged.connect(self.on_select_mode)
        self._ui_unit_combo = QComboBox()
        self._ui_unit_combo.currentTextChanged.connect(self.on_select_unit)
        self._ui_unit2_combo = QComboBox()
        self._ui_unit2_combo.currentTextChanged.connect(self.on_select_unit2)
        
        tabs = QTabWidget()
        
        files_tab = QWidget()
        tabs.addTab(files_tab, 'Files')
        self._ui_fileview = QTreeView()
        self._ui_filemodel = QStandardItemModel()
        self._ui_filemodel.setHorizontalHeaderLabels(['File', 'Properties'])
        self._ui_fileview_root = self._ui_filemodel.invisibleRootItem()
        self._ui_fileview.setModel(self._ui_filemodel)
        self._ui_fileview.setSelectionMode(QTreeView.SelectionMode.ExtendedSelection)
        self._ui_fileview.selectionModel().selectionChanged.connect(self.on_select_file)
        files_tab.setLayout(QtHelper.layout_v(self._ui_fileview))
        
        expressions_tab = QWidget()
        tabs.addTab(expressions_tab, 'Expressions')
        self._ui_update_button = QPushButton('Update (F5)')
        self._ui_update_button.clicked.connect(self.on_update_button)
        self._ui_template_button = QPushButton('Template...')
        self._ui_update_button.clicked.connect(self.on_template_button)
        self._ui_help_button = QPushButton('Help')
        self._ui_update_button.clicked.connect(self.on_help_button)
        self._ui_editor = QPlainTextEdit()
        self._ui_editor.setFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self._ui_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        expressions_tab.setLayout(QtHelper.layout_h(
            QtHelper.layout_v(
                self._ui_update_button,
                self._ui_template_button,
                #5,
                self._ui_help_button,
                ...
            ),
            self._ui_editor
        ))

        self._ui_status_bar = QStatusBar()

        splitter_top.setLayout(QtHelper.layout_v(self._ui_plot))
        splitter_bottom.setLayout(QtHelper.layout_v(
            QtHelper.layout_h(self._ui_mode_combo, self._ui_unit_combo, self._ui_unit2_combo),
            tabs,
            self._ui_status_bar,
        ))

    

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
        self.ui_menuitem_log = QtHelper.add_menuitem(self.ui_mainmenu_tools, 'Status Log', self.on_log, shortcut='Ctrl+L')
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


    def ui_show(self):
        super().show()


    def ui_show_template_menu(self):
        button_pos = self._ui_template_button.mapToGlobal(QPoint(0, self._ui_template_button.height()))
        self.ui_template_menu.popup(button_pos)

    
    def ui_set_window_title(self, title: str):
        self.setWindowTitle(title)

    
    def ui_set_modes_list(self, items: list[str]):
        self._ui_mode_combo.clear()
        for item in items:
            self._ui_mode_combo.addItem(item)

    
    def ui_set_units_list(self, items: list[str]):
        self._ui_unit_combo.clear()
        for item in items:
            self._ui_unit_combo.addItem(item)

    
    def ui_set_units2_list(self, items: list[str]):
        self._ui_unit2_combo.clear()
        for item in items:
            self._ui_unit2_combo.addItem(item)
    

    @property
    def ui_plot(self) -> PlotWidget:
        return self._ui_plot
    

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
        return self._ui_editor.toPlainText()
    @ui_expression.setter
    def ui_expression(self, expression: str):
        return self._ui_editor.setPlainText(expression)


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


    def ui_update_status_message(self, status_message: str):
        if status_message:
            self._ui_status_bar.showMessage(status_message)
        else:
            self._ui_status_bar.clearMessage()


    def ui_set_fileview_items(self, names_and_contents: list[tuple[str,str]]):
        self._ui_fileview_root.removeRows(0, self._ui_fileview_root.rowCount())
        for name,content in names_and_contents:
            self._ui_fileview_root.appendRow([QStandardItem(name), QStandardItem(content)])
        for column in range(self._ui_fileview.model().columnCount()):
            self._ui_fileview.resizeColumnToContents(column)


    def ui_update_fileview_item(self, index: int, name: str, contents: str):
        self._ui_fileview.model().itemFromIndex(self._ui_fileview.model().index(index, 0)).setText(name)
        self._ui_fileview.model().itemFromIndex(self._ui_fileview.model().index(index, 1)).setText(contents)


    def ui_select_fileview_items(self, indices: list[int]):
        self._ui_fileview.selectionModel().clearSelection()
        for index_to_select in indices:
            index = self._ui_fileview.model().index(index_to_select, 0)
            self._ui_fileview.selectionModel().select(index, QItemSelectionModel.SelectionFlag.Select | QItemSelectionModel.SelectionFlag.Rows)


    def ui_get_selected_fileview_indices(self) -> list[int]:
        sel = self._ui_fileview.selectionModel().selectedIndexes()
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
        pass
    def on_select_unit(self):
        pass
    def on_select_unit2(self):
        pass
    def on_show_filter(self):
        pass
    def on_select_file(self):
        pass
    def on_open_directory(self):
        pass
    def on_append_directory(self):
        pass
    def on_reload_all_files(self):
        pass
    def on_trace_cursors(self):
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
    def on_update_button(self):
        pass
    def on_template_button(self):
        pass
    def on_help_button(self):
        pass
