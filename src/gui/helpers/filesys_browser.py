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
from typing import Callable, overload, override
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
            if is_toplevel:
                text = str(path)
            else:
                text = path.final_name
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
    
        def add_children_to_tree(self, support_archives: bool) -> bool:
            if self._children_added:
                return False
            self._children_added = True
            
            if self._type == FilesysBrowserItemType.File:
                return False

            if self._type == FilesysBrowserItemType.Dir:
                children = list(self._path.iterdir())
            elif self._type == FilesysBrowserItemType.Arch:
                children = find_files_in_archive(str(self._path)) if support_archives else []
            else:
                children = []
            self._has_children = len(children) > 0

            if self._type == FilesysBrowserItemType.Arch:
                for arch_path in children:
                    super().appendRow((FilesysBrowser.MyFileItem(PathExt(self._path, arch_path=arch_path), FilesysBrowserItemType.File), QStandardItem('')))
            else:
                dirs = [p for p in children if p.is_dir()]
                files = [p for p in children if p.is_file()]
                for file in sorted([p for p in files if is_ext_supported_file(p.suffix)], key=lambda p: p.name):
                    super().appendRow((FilesysBrowser.MyFileItem(file, FilesysBrowserItemType.File), QStandardItem('')))
                if support_archives:
                    for arch in sorted([p for p in files if is_ext_supported_archive(p.suffix)], key=lambda p: p.name):
                        super().appendRow(FilesysBrowser.MyFileItem(arch, FilesysBrowserItemType.Arch))
                for dir in sorted(dirs, key=lambda p: p.name):
                    super().appendRow(FilesysBrowser.MyFileItem(dir, FilesysBrowserItemType.Dir))
            
            return self._has_children


    class MyFileItemModel(QStandardItemModel):
        
        filesChanged = pyqtSignal()
    
        def __init__(self, parent):
            super().__init__(parent)
            self.show_archives = False
            self.setHorizontalHeaderLabels(['Files', 'Info'])
        
        @override
        def hasChildren(self, index: QModelIndex = ...):
            item: FilesysBrowser.MyFileItem = self.itemFromIndex(index)
            if not item:
                return True
            return item.hasChildren()

        @override
        def canFetchMore(self, index: QModelIndex = ...):
            item: FilesysBrowser.MyFileItem = self.itemFromIndex(index)
            if not item:
                return True
            return item.hasChildren()

        @override
        def fetchMore(self, index: QModelIndex = ...):
            item: FilesysBrowser.MyFileItem = self.itemFromIndex(index)
            if not item:
                return
            anything_added = item.add_children_to_tree(self.show_archives)
            if anything_added:
                self.filesChanged.emit()


    filesChanged = pyqtSignal()
    selectionChanged = pyqtSignal()
    doubleClicked = pyqtSignal(PathExt, PathExt, FilesysBrowserItemType)
    contextMenuRequested = pyqtSignal(PathExt, PathExt, FilesysBrowserItemType)


    def __init__(self):
        FilesysBrowser._ensure_icons_loaded()
        super().__init__()

        self._contextmenu_point: QPoint = None
        self._contextmenu_item: FilesysBrowser.MyFileItem = None
        self._show_archives = False
        
        self._ui_filesys_view = QTreeView()
        self._ui_filesys_model = FilesysBrowser.MyFileItemModel(self._ui_filesys_view)
        self._ui_filesys_model.dataChanged.connect(self._on_checked_change)
        self._ui_filesys_model.filesChanged.connect(self.filesChanged)
        self._ui_filesys_model.show_archives = self._show_archives
        self._ui_filesys_view.setToolTip('Select files to plot; right-click a directory to navigate')
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
    

    @property
    def show_archives(self) -> bool:
        return self._show_archives
    @show_archives.setter
    def show_archives(self, value: bool):
        if value != self._show_archives:
            self._show_archives = value
            self._ui_filesys_model.show_archives = value
            self.refresh()

    
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

        def recurse(parent: FilesysBrowser.MyFileItem):
            if parent is None:
                return
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.path in selected_paths:
                    item.checked = True
                recurse(item)
        recurse(self._ui_filesys_model.invisibleRootItem())
    

    def update_status(self, path: PathExt, status: str):
        def recurse(parent: FilesysBrowser.MyFileItem):
            if parent is None:
                return
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.path == path:
                    status_item = parent.child(row_index, 1)
                    if not isinstance(status_item, QStandardItem):
                        continue
                    status_item.setText(status)
                recurse(item)
        recurse(self._ui_filesys_model.invisibleRootItem())
    

    def add_toplevel(self, path: PathExt):
        self._add_toplevel(path, 0)
        self.filesChanged.emit()


    def remove_toplevel(self, path: PathExt):
        if self._ui_filesys_model.invisibleRootItem().rowCount() <= 1:
            return #  only one top-level element left; ignore
        for row_index in reversed(range(self._ui_filesys_model.invisibleRootItem().rowCount())):
            item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
            if not isinstance(item, FilesysBrowser.MyFileItem):
                continue
            if item.path == path:
                self._ui_filesys_model.removeRow(row_index)
                    
        self.filesChanged.emit()

    
    def change_root(self, current_root: PathExt, new_root: PathExt):
        toplevel_item: FilesysBrowser.MyFileItem = None
        toplevel_index: int = 0
        for row_index in range(self._ui_filesys_model.invisibleRootItem().rowCount()):
            item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
            if not isinstance(item, FilesysBrowser.MyFileItem):
                continue
            if item.path == current_root:
                toplevel_item = item
                toplevel_index = row_index
                break
        if not isinstance(toplevel_item, FilesysBrowser.MyFileItem):
            return
        self._ui_filesys_model.removeRow(toplevel_index)
        new_item = self._add_toplevel(new_root, toplevel_index)
        self._ui_filesys_view.expand(self._ui_filesys_model.indexFromItem(new_item))
        
        self.filesChanged.emit()


    def show_context_menu(self, items: list[tuple[str,Callable|list]]):
        point = self._contextmenu_point or QCursor().pos()
        QtHelper.show_popup_menu(self, items, point)


    def refresh(self):
        toplevel_paths: list[PathExt] = []
        for row_index in range(self._ui_filesys_model.invisibleRootItem().rowCount()):
            item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
            if not isinstance(item, FilesysBrowser.MyFileItem):
                continue
            toplevel_paths.append(item.path)
        
        self._ui_filesys_model.invisibleRootItem().removeRows(0, self._ui_filesys_model.invisibleRootItem().rowCount())

        for i,path in enumerate(toplevel_paths):
            self._add_toplevel(path, i)
            
        self.filesChanged.emit()

    
    def _add_toplevel(self, path: PathExt, row_index: int):
        for row_index in range(self._ui_filesys_model.invisibleRootItem().rowCount()):
            item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
            if not isinstance(item, FilesysBrowser.MyFileItem):
                continue
            if item.path == path:
                return  # path is already at top-level; ignore

        if path.is_dir():
            new_item = FilesysBrowser.MyFileItem(path, FilesysBrowserItemType.Dir, is_toplevel=True)
        elif path.is_file() and is_ext_supported_archive(path.suffix):
            if not self._show_archives:
                return None
            new_item = FilesysBrowser.MyFileItem(path, FilesysBrowserItemType.Arch, is_toplevel=True)
        else:
            return  # files cannot be a top-lvel item; ignore
        
        self._ui_filesys_model.insertRow(row_index, new_item)
        new_item_index = self._ui_filesys_model.indexFromItem(new_item)
        if new_item_index:
            self._ui_filesys_view.expand(new_item_index)
    

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

    
    def _get_top_item(self, item: FilesysBrowser.MyFileItem) -> FilesysBrowser.MyFileItem:
        def contains_item(parent: FilesysBrowser.MyFileItem, searched_item: FilesysBrowser.MyFileItem) -> bool:
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if item == searched_item:
                    return True
                if contains_item(item, searched_item):
                    return True
            return False
        def find_top_item(searched_item: FilesysBrowser.MyFileItem) -> FilesysBrowser.MyFileItem:
            for row_index in range(self._ui_filesys_model.invisibleRootItem().rowCount()):
                item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
                if item == searched_item:
                    return item
                if contains_item(item, searched_item):
                    return item
            return None
        return find_top_item(item)


    def _on_contextmenu_requested(self, point: QPoint):
        self._contextmenu_point = self._ui_filesys_view.mapToGlobal(point)
        index = self._ui_filesys_view.indexAt(point)
        if not index:
            return
        item: FilesysBrowser.MyFileItem = self._ui_filesys_model.itemFromIndex(index)
        if not isinstance(item, FilesysBrowser.MyFileItem):
            return
        top_item = self._get_top_item(item)
        if not isinstance(top_item, FilesysBrowser.MyFileItem):
            return
        self._contextmenu_item = item
        self.contextMenuRequested.emit(item.path, top_item.path, item.type)
    
    
    def _on_doubleclick(self, index: QModelIndex):
        item: FilesysBrowser.MyFileItem = self._ui_filesys_model.itemFromIndex(index)
        if not isinstance(item, FilesysBrowser.MyFileItem):
            return
        top_item = self._get_top_item(item)
        if not isinstance(top_item, FilesysBrowser.MyFileItem):
            return
        self.doubleClicked.emit(item.path, top_item.path, item.type)


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
