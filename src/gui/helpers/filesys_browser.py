import pathlib
from .qt_helper import QtHelper
from .path_bar import PathBar
from lib import AppPaths

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import pathlib, os
from typing import Callable



class FilesysBrowser(QWidget):


    class MyTreeView(QTreeView):
        
        backClicked = pyqtSignal()

        def mouseReleaseEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.BackButton:
                self.backClicked.emit()
            super().mouseReleaseEvent(event)
    
    
    doubleClick = pyqtSignal(str)
    contextMenuRequest = pyqtSignal(str)


    def __init__(self, path: str|None = None):
        super().__init__()
        self._context_menu_location = None
        self._history: list[str] = []

        if not path:
            path = AppPaths.get_default_file_dir()
        self._append_history(path)

        self._ui_path_bar = PathBar(path)
        def _pathbar_change(path: str):
            self._update_tree(path)
        self._ui_path_bar.pathChanged.connect(_pathbar_change)
        self._ui_path_bar.backClicked.connect(self._on_back_click)
        
        self._ui_filesysview = FilesysBrowser.MyTreeView()
        self._ui_filesysview.setToolTip('Double-click or right-click an file or directory to add it to the file list')
        self._ui_filesysmodel = QFileSystemModel()
        self._ui_filesysmodel.setRootPath('')
        self._ui_filesysmodel.setFilter(QtCore.QDir.Filter.AllDirs | QtCore.QDir.Filter.NoDotAndDotDot)
        self._ui_filesysview.setModel(self._ui_filesysmodel)
        self._ui_filesysview.resizeColumnToContents(0)
        def _filesys_doubleclick(index: QModelIndex):
            path = self._ui_filesysmodel.filePath(index)
            self.doubleClick.emit(os.path.abspath(path))
        self._ui_filesysview.doubleClicked.connect(_filesys_doubleclick)
        self._ui_filesysview.backClicked.connect(self._on_back_click)
        self._ui_filesysview.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        def _filesys_rightclick(point: QPoint):
            self._context_menu_location = self._ui_filesysview.mapToGlobal(point)
            index = self._ui_filesysview.indexAt(point)
            if not index.isValid():
                return
            path = self._ui_filesysmodel.filePath(index)
            self.contextMenuRequest.emit(os.path.abspath(path))
        self._ui_filesysview.customContextMenuRequested.connect(_filesys_rightclick)
        def _filesys_select(newsel: QItemSelection, oldset: QItemSelection):
            sel = self._ui_filesysview.selectedIndexes()
            if len(sel) < 1:
                return
            path = self._ui_filesysmodel.filePath(sel[0])
            self._update_text(path)
        self._ui_filesysview.selectionModel().selectionChanged.connect(_filesys_select)
        self._update_tree(path)
        
        self.setLayout(QtHelper.layout_v(self._ui_path_bar, self._ui_filesysview))
    

    @property
    def show_files(self) -> bool:
        return QDir.Filter.Files in self._ui_filesysmodel.filter()
    @show_files.setter
    def show_files(self, value: bool):
        flags = QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot
        if value:
            flags |= QDir.Filter.Files
        self._ui_filesysmodel.setFilter(flags)


    def navigate(self, path: str):
        self._update_text(path)
        self._update_tree(path)
        self._append_history(path)


    def show_context_menu(self, items: dict[str,Callable|dict]):
        point = self._context_menu_location or QCursor().pos()
        QtHelper.show_popup_menu(self, items, point)


    def _update_text(self, path: str):
        self._ui_path_bar.path = os.path.abspath(path)


    def _update_tree(self, path: str):
        index = self._ui_filesysmodel.index(os.path.abspath(path))
        if not index.isValid():
            return
        self._ui_filesysview.setCurrentIndex(index)
        self._ui_filesysview.scrollTo(index, QAbstractItemView.ScrollHint.EnsureVisible)
        self._ui_filesysview.resizeColumnToContents(0)

    
    def _append_history(self, path_str: str):
        path = pathlib.Path(path_str)
        if not path.exists():
            return
        if path.is_file():
            path = path.parent
        abspath = str(path.absolute())
        if len(self._history) >= 1:
            if self._history[-1] == abspath:
                return
        MAX_LEN = 100
        self._history.append(abspath)
        while len(self._history) > MAX_LEN:
            del self._history[0]


    def _on_back_click(self):
        if len(self._history) < 1:
            return
        path = self._history.pop()
        self.navigate(path)
