from .helpers.qt_helper import QtHelper
from info import Info
from lib import AppPaths, PathExt
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import logging
import enum



class FilterDialogUi(QDialog):


    class Action(enum.Enum):
        Cancel = enum.auto()
        Select = enum.auto()
        Add = enum.auto()
        Remove = enum.auto()
        Toggle = enum.auto()

    

    class PathItem(QStandardItem):

        def __init__(self, path: PathExt):
            super().__init__()
            self.path = path
            self.setText(path.final_name)


    def __init__(self, parent):
        super().__init__(parent)
        self._result = FilterDialogUi.Action.Select

        self.setWindowTitle('Filter Files')
        QtHelper.set_dialog_icon(self)
        self.setModal(True)
        self.setSizeGripEnabled(True)

        self._ui_search_text = QLineEdit()
        self._ui_search_text.setPlaceholderText('Enter expression, then press Enter')
        self._ui_search_text.setToolTip('Enter your search expression here, then press Enter (or press Escape to abort)')
        self._ui_search_text.textChanged.connect(self.on_search_change)
        self._ui_search_text.returnPressed.connect(self.accept)

        self._ui_wildcard_radio = QRadioButton('Wildcards')
        self._ui_wildcard_radio.setToolTip('You can use the wildcards "*" (anything) and "?" (any single character)')
        self._ui_wildcard_radio.toggled.connect(self.on_search_mode_change)

        self._ui_regex_radio = QRadioButton('Regex')
        self._ui_regex_radio.setToolTip('You can use regular expressions')
        self._ui_regex_radio.toggled.connect(self.on_search_mode_change)

        self._ui_files_list = QListView()
        self._ui_files_list.setToolTip('Files that match your search are selected here. You may manually change the selection.')
        self._ui_files_list.setMinimumSize(200, 100)
        self._ui_files_model = QtGui.QStandardItemModel()
        self._ui_files_list.setModel(self._ui_files_model)
        self._ui_files_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
        # set more vibrant colors (by default, the selection cannot be distinguished clearly from non-selection)
        palette = QPalette()
        color_text = palette.color(QPalette.ColorRole.HighlightedText).name()
        color_bg = palette.color(QPalette.ColorRole.Highlight).name()
        self._ui_files_list.setStyleSheet(f"""
            QListView::item:selected {{
                background-color: {color_bg};
                color: {color_text};
            }}
        """)

        self.ui_select_button = QtHelper.make_button(self, '', self._on_select, icon='filter_select.svg')
        self.ui_select_button.setToolTip('Only plot selected files')
        self.ui_add_button = QtHelper.make_button(self, '', self._on_add, icon='filter_add.svg')
        self.ui_add_button.setToolTip('Additionally plot selected files')
        self.ui_remove_button = QtHelper.make_button(self, '', self._on_remove, icon='filter_subtract.svg')
        self.ui_remove_button.setToolTip('Don\'t plot selected files')
        self.ui_toggle_button = QtHelper.make_button(self, '', self._on_toggle, icon='filter_toggle.svg')
        self.ui_toggle_button.setToolTip('Toggle plotting of selected files files')
        
        self.setLayout(QtHelper.layout_v(
            QtHelper.layout_h(
                self._ui_search_text,
                self._ui_wildcard_radio,
                self._ui_regex_radio,
            ),
            self._ui_files_list,
            QtHelper.layout_h(
                self.ui_select_button,
                15,
                self.ui_add_button,
                self.ui_remove_button,
                self.ui_toggle_button,
                ...,
            ),
        ))

        self.resize(400, 500)
        

    def ui_show_modal(self) -> Action:
        self._ui_search_text.selectAll()
        self._ui_search_text.focusWidget()
        self._result = FilterDialogUi.Action.Select
        if self.exec() == QDialog.DialogCode.Accepted:
            return self._result
        return FilterDialogUi.Action.Cancel


    @property
    def ui_search_text(self) -> str:
        return self._ui_search_text.text()
    @ui_search_text.setter
    def ui_search_text(self, value: str):
        self._ui_search_text.setText(value)
    

    @property
    def ui_regex_mode(self) -> bool:
        return self._ui_regex_radio.isChecked()
    @ui_regex_mode.setter
    def ui_regex_mode(self, value: bool):
        if value:
            self._ui_regex_radio.setChecked(True)
        else:
            self._ui_wildcard_radio.setChecked(True)
    

    def ui_set_files(self, selected_files: list[PathExt], other_files: list[PathExt]):
        self._ui_files_model.clear()
        for file in [*selected_files, *other_files]:
            item = FilterDialogUi.PathItem(file)
            self._ui_files_model.appendRow(item)
        
        selection = QItemSelection(
            self._ui_files_model.index(0, 0),
            self._ui_files_model.index(len(selected_files)-1, 0),
        )
        self._ui_files_list.selectionModel().select(selection, QItemSelectionModel.SelectionFlag.Select)
    

    def ui_get_selected_files(self) -> list[PathExt]:
        result = []
        for index in self._ui_files_list.selectionModel().selectedRows(0):
            item: FilterDialogUi.PathItem = self._ui_files_model.itemFromIndex(index)
            result.append(item.path)
        return result
    

    def ui_indicate_search_error(self, indicate_error: bool = True):
        QtHelper.indicate_error(self._ui_search_text, indicate_error)


    # to be implemented in derived class
    def on_search_change(self):
        pass
    def on_search_mode_change(self):
        pass


    def _on_select(self):
        self._result = FilterDialogUi.Action.Select
        self.accept()


    def _on_add(self):
        self._result = FilterDialogUi.Action.Add
        self.accept()


    def _on_remove(self):
        self._result = FilterDialogUi.Action.Remove
        self.accept()


    def _on_toggle(self):
        self._result = FilterDialogUi.Action.Toggle
        self.accept()
