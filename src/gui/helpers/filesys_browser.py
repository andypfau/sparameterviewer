from __future__ import annotations

import pathlib
from .qt_helper import QtHelper
from .path_bar import PathBar
from lib import AppPaths, PathExt, is_ext_supported_file, is_ext_supported_archive, find_files_in_archive

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import pathlib
import os
import re
import logging
import enum
from typing import Callable
from types import SimpleNamespace



class FilesysBrowserItemType(enum.Enum):
    File = enum.auto()
    Dir = enum.auto()
    Arch = enum.auto()



class FilesysBrowser(QWidget):

        
    _icon_file: QIcon = None
    _icon_dir: QIcon = None
    _icon_arch: QIcon = None


    class MyFileItem(QStandardItem):

        def __init__(self, path: PathExt, type: FilesysBrowserItemType, *, is_toplevel: bool = False):
            self._path = path
            self._children: list[PathExt]|None = None
            self._type = type
            self._is_toplevel = is_toplevel
            
            # assume any directory or archive has children; this allows us to postpone the directory scan to as late as possible
            self._has_children = type in [FilesysBrowserItemType.Dir, FilesysBrowserItemType.Arch]
            self._children_added = False
            
            if type == FilesysBrowserItemType.Dir:
                icon = FilesysBrowser._icon_dir
            elif type == FilesysBrowserItemType.Arch:
                icon = FilesysBrowser._icon_arch
            else:
                icon = FilesysBrowser._icon_file
            if path.arch_path:
                text = path.arch_path
            elif is_toplevel:
                text = str(path)
            else:
                text = path.name
            super().__init__(icon, text)
            
            if type == FilesysBrowserItemType.File:
                super().setCheckable(True)
                super().setCheckState(QtCore.Qt.CheckState.Unchecked)
        
        def __repr__(self) -> str:
            return f'<MyFileItem({self._path})>'
        
        @property
        def path(self) -> PathExt:
            return self._path
        
        @property
        def checked(self) -> bool:
            if self._type != FilesysBrowserItemType.File:
                return False
            return super().checkState() == QtCore.Qt.CheckState.Checked
        @checked.setter
        def checked(self, value: bool):
            if self._type != FilesysBrowserItemType.File:
                return
            super().setCheckState(QtCore.Qt.CheckState.Checked if value else QtCore.Qt.CheckState.Unchecked)
        
        @property
        def is_toplevel(self) -> bool:
            return self._is_toplevel
        
        @property
        def type(self) -> FilesysBrowserItemType:
            return self._type
                
        def hasChildren(self) -> bool:
            return self._has_children
    
        def add_children_to_tree(self) -> bool:
            if self._children_added:
                return False
            self._children_added = True
            
            if self._type == FilesysBrowserItemType.File:
                return False

            children = []
            if not self._is_dots:
                if self._type == FilesysBrowserItemType.Dir:
                    children = list(self._path.iterdir())
                elif self._type == FilesysBrowserItemType.Arch:
                    children = find_files_in_archive(str(self._path))
            self._has_children = len(children) > 0

            if self._type == FilesysBrowserItemType.Arch:
                for arch_path in children:
                    super().appendRow((FilesysBrowser.MyFileItem(PathExt(self._path, arch_path=arch_path), FilesysBrowserItemType.File), QStandardItem('Not Loaded')))
            else:
                dirs = [p for p in children if p.is_dir()]
                files = [p for p in children if p.is_file()]
                for dir in sorted(dirs, key=lambda p: p.name):
                    super().appendRow(FilesysBrowser.MyFileItem(dir, FilesysBrowserItemType.Dir))
                for arch in sorted([p for p in files if is_ext_supported_archive(p.suffix)], key=lambda p: p.name):
                    super().appendRow(FilesysBrowser.MyFileItem(arch, FilesysBrowserItemType.Arch))
                for file in sorted([p for p in files if is_ext_supported_file(p.suffix)], key=lambda p: p.name):
                    super().appendRow((FilesysBrowser.MyFileItem(file, FilesysBrowserItemType.File), QStandardItem('Not Loaded')))
            
            return self._has_children


    class MyFileItemModel(QStandardItemModel):
        
        filesChanged = pyqtSignal()
    
        def __init__(self, parent, path: PathExt):
            assert path.exists() and path.is_dir()
            super().__init__(parent)
            self._path = path
            self.setHorizontalHeaderLabels(['Files', 'Info'])
            self.root_item = FilesysBrowser.MyFileItem(self._path, FilesysBrowserItemType.Dir, is_toplevel=True)
            self.appendRow((self.root_item, QStandardItem('File System')))
        
        def add_toplevel(self, path: PathExt):

            if len(self.get_row_indices(path)) > 0:
                return  # redundant; ignore

            if path.is_dir():
                item = FilesysBrowser.MyFileItem(path, FilesysBrowserItemType.Dir, is_toplevel=True)
            elif path.is_file() and is_ext_supported_archive(path.suffix):
                item = FilesysBrowser.MyFileItem(path, FilesysBrowserItemType.Arch, is_toplevel=True)
            else:
                return  # files cannot be a top-lvel item; ignore
            
            self.insertRow(0, item)

        def remove_toplevel(self, path: PathExt):
            for i in reversed(self.get_row_indices(path)):
                if self.rowCount() <= 1:
                    return  # always keep at least one top-level item
                item: FilesysBrowser.MyFileItem = self.item(i, 0)
                if item.is_toplevel:
                    self.removeRow(i)
        
        def get_row_indices(self, path: PathExt) -> list[int]:
            result = []
            for i in range(self.rowCount()):
                item: FilesysBrowser.MyFileItem = self.item(i, 0)
                if not item:
                    continue
                if item.path == path:
                    result.append(i)
            return list(sorted(result))

        def update_item_status(self, path: PathExt, status: str):
            for i in self.get_row_indices(path):
                status_item: FilesysBrowser.MyFileItem = self.item(i, 1)
                if not status_item:
                    continue
                status_item.setText(status)
        
        def hasChildren(self, index: QModelIndex = ...):
            item: FilesysBrowser.MyFileItem = self.itemFromIndex(index)
            if not item:
                return True
            return item.hasChildren()

        def canFetchMore(self, index: QModelIndex = ...):
            item: FilesysBrowser.MyFileItem = self.itemFromIndex(index)
            if not item:
                return True
            return item.hasChildren()

        def fetchMore(self, index: QModelIndex = ...):
            item: FilesysBrowser.MyFileItem = self.itemFromIndex(index)
            if not item:
                return
            anything_added = item.add_children_to_tree()
            if anything_added:
                self.filesChanged.emit()


    filesChanged = pyqtSignal()
    selectionChanged = pyqtSignal()
    doubleClicked = pyqtSignal(PathExt, FilesysBrowserItemType)
    contextMenuRequested = pyqtSignal(PathExt, FilesysBrowserItemType)


    def __init__(self, path: PathExt|None = None):
        FilesysBrowser._ensure_icons_loaded()
        super().__init__()

        self._contextmenu_point: QPoint = None
        self._contextmenu_item: FilesysBrowser.MyFileItem = None
        
        # # TODO: remove this debug code
        # path = PathExt(r'C:\MentorGraphics\sparameterviewer')

        if not path:
            path = PathExt(AppPaths.get_default_file_dir())
        if not path.exists():
            path = PathExt(AppPaths.get_default_file_dir())
        if path.is_file():
            path = path.parent
        
        #self._ui_filesys_model.setHorizontalHeaderLabels(['Files'])
        self._ui_filesys_view = QTreeView()
        self._ui_filesys_model = FilesysBrowser.MyFileItemModel(self._ui_filesys_view, path)
        self._ui_filesys_model.dataChanged.connect(self._on_checked_change)
        self._ui_filesys_model.filesChanged.connect(self.filesChanged)
        self._ui_filesys_view.setToolTip('Double-click or right-click an file or directory to add it to the file list')
        self._ui_filesys_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._ui_filesys_view.setModel(self._ui_filesys_model)
        self._ui_filesys_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._ui_filesys_view.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._ui_filesys_view.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._ui_filesys_view.selectionModel().selectionChanged.connect(self._on_selection_change)
        self._ui_filesys_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._ui_filesys_view.customContextMenuRequested.connect(self._on_contextmenu_requested)
        self._ui_filesys_view.doubleClicked.connect(self._on_doubleclick)
        self.setLayout(QtHelper.layout_v(self._ui_filesys_view))
        
        # # TODO: remove this debug code
        # for p in [r'C:\MentorGraphics\sparameterviewer\samples', r'C:\MentorGraphics\sparameterviewer\samples\test\coupler_4port2.s4p']:
        #     self.add_toplevel(PathExt(p))
        # self.update_status(PathExt(r'C:\MentorGraphics\sparameterviewer\samples\test\coupler_4port2.s4p'), '4-Port')
        # self.selected_files = [PathExt(r'C:\MentorGraphics\sparameterviewer\samples\test\coupler_4port2.s4p')]

    
    @property
    def all_files(self) -> list[PathExt]:
        result = set()
        def recurse(parent: FilesysBrowser.MyFileItem):
            nonlocal result
            if parent is None:
                return
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.type == FilesysBrowserItemType.File:
                    result.add(item.path)
                recurse(item)
        recurse(self._ui_filesys_model.invisibleRootItem())
        return list(result)

    @property
    def selected_files(self) -> list[PathExt]:
        result = set()
        def recurse(parent: FilesysBrowser.MyFileItem):
            nonlocal result
            if parent is None:
                return
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.checked:
                    result.add(item.path)
                recurse(item)
        recurse(self._ui_filesys_model.invisibleRootItem())
        return list(result)
    @selected_files.setter
    def selected_files(self, selected_paths: list[PathExt]):
        self._ui_filesys_view.selectionModel().clearSelection()
        for path in selected_paths:
            for i in self._ui_filesys_model.get_row_indices(path):
                index = self._ui_filesys_model.index(i, 0)
                item = self._ui_filesys_model.itemFromIndex(index)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                item.checked = True
    

    def update_status(self, path: PathExt, status: str):
        self._ui_filesys_model.update_item_status(path, status)
    

    def add_toplevel(self, path: PathExt):
        self._ui_filesys_model.add_toplevel(path)
    

    def remove_toplevel(self, path: PathExt):
        self._ui_filesys_model.remove_toplevel(path)
    
    
    def change_root(self, current_root: PathExt, new_root: PathExt):
        return  # TODO: implement


    def show_context_menu(self, items: dict[str,Callable|dict]):
        point = self._contextmenu_point or QCursor().pos()
        QtHelper.show_popup_menu(self, items, point)
    

    def _on_selection_change(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):
        newly_selected_items = list([item for item in [self._ui_filesys_model.itemFromIndex(index) for index in selected.indexes()] if isinstance(item, FilesysBrowser.MyFileItem)])
        
        if len(newly_selected_items)==1:
            if newly_selected_items[0].type != FilesysBrowserItemType.File:
                # the user selected a non-file; ignore this action
                return

        # the user selected or de-selected some files; check them accordingly
        selected_items = [item for item in [self._ui_filesys_model.itemFromIndex(index) for index in self._ui_filesys_view.selectedIndexes()] if isinstance(item, FilesysBrowser.MyFileItem)]
        def recurse(parent: FilesysBrowser.MyFileItem):
            if parent is None:
                return
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                item.checked = item in selected_items
                recurse(item)
        recurse(self._ui_filesys_model.invisibleRootItem())
    

    def _on_checked_change(self, index: QModelIndex, index2: QModelIndex):
        self.selectionChanged.emit()


    def _on_contextmenu_requested(self, point: QPoint):
        self._contextmenu_point = point
        index = self._ui_filesys_view.indexAt(point)
        if not index:
            return
        item: FilesysBrowser.MyFileItem = self._ui_filesys_model.itemFromIndex(index)
        if not isinstance(item, FilesysBrowser.MyFileItem):
            return
        self._contextmenu_item = item
        self.contextMenuRequested(item.path, item.type)
    
    
    def _on_doubleclick(self, index: QModelIndex):
        item: FilesysBrowser.MyFileItem = self._ui_filesys_model.itemFromIndex(index)
        if not isinstance(item, FilesysBrowser.MyFileItem):
            return
        self.doubleClicked.emit(item.path, item.type)


    @staticmethod
    def _ensure_icons_loaded():
        def ensure_icon_loaded(icon: QIcon, filename: str) -> QIcon:
            if icon:
                return icon
            path = os.path.join(AppPaths.get_resource_dir(), filename)
            try:
                return QIcon(path)
            except Exception as ex:
                logging.warning(f'Unable to load icon from <{path}> ({ex})')
                return QIcon()
        
        FilesysBrowser._icon_file = ensure_icon_loaded(FilesysBrowser._icon_file, 'filesys_file.png')
        FilesysBrowser._icon_dir  = ensure_icon_loaded(FilesysBrowser._icon_dir, 'filesys_dir.png')
        FilesysBrowser._icon_arch = ensure_icon_loaded(FilesysBrowser._icon_arch, 'filesys_archive.png')
