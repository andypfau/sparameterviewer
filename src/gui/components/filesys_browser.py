from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from ..helpers.file_filter import FileFilter
from .path_bar import PathBar
from lib import AppPaths, PathExt, Settings, is_ext_supported_file, is_ext_supported_archive, find_files_in_archive, natural_sort_key, get_callstack_str

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


    MAX_HISTORY = 25

        
    _icon_file: QIcon = None
    _icon_dir: QIcon = None
    _icon_arch: QIcon = None



    class MyFileItem(QStandardItem):

        def __init__(self, model: FilesysBrowser.MyFileItemModel, path: PathExt, type: FilesysBrowserItemType, *, is_toplevel: bool = False, filter: FileFilter = FileFilter()):
            self._last_reported_checked_state = None
            self._model = model
            self._path = path
            self._children: list[PathExt]|None = None
            self._type = type
            self._is_toplevel = is_toplevel
            self._filter: FileFilter = filter
            
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
    
        def add_children_to_tree(self, support_archives: bool) -> bool:
            if self._children_added:
                return False
            self._children_added = True
            
            if self._type == FilesysBrowserItemType.File:
                return False

            if self._type == FilesysBrowserItemType.Dir:
                children = [PathExt(p) for p in self._path.iterdir()]
            elif self._type == FilesysBrowserItemType.Arch:
                children = [p for p in find_files_in_archive(str(self._path)) if is_ext_supported_file(p.arch_path_suffix)] if support_archives else []
            else:
                children = []
            children = [child for child in children if self._filter.apply(child)]
            self._has_children = len(children) > 0

            if self._type == FilesysBrowserItemType.Arch:
                for path in children:
                    super().appendRow((FilesysBrowser.MyFileItem(self._model, path, FilesysBrowserItemType.File), QStandardItem('')))
            else:
                dirs = [p for p in children if p.is_dir()]
                files = [p for p in children if p.is_file()]
                for file in sorted([p for p in files if is_ext_supported_file(p.suffix)], key=lambda p: natural_sort_key(p.final_name)):
                    super().appendRow((FilesysBrowser.MyFileItem(self._model, file, FilesysBrowserItemType.File), QStandardItem('')))
                if support_archives:
                    for arch in sorted([p for p in files if is_ext_supported_archive(p.suffix)], key=lambda p: natural_sort_key(p.final_name)):
                        super().appendRow(FilesysBrowser.MyFileItem(self._model, arch, FilesysBrowserItemType.Arch, filter=self._filter))
                for dir in sorted(dirs, key=lambda p: natural_sort_key(p.final_name)):
                    super().appendRow(FilesysBrowser.MyFileItem(self._model, dir, FilesysBrowserItemType.Dir, filter=self._filter))
            
            return self._has_children
                
        @override
        def hasChildren(self) -> bool:
            return self._has_children

        @override
        def setData(self, value: any, role: int):
            if role == Qt.ItemDataRole.CheckStateRole and value != self._last_reported_checked_state:
                self._last_reported_checked_state = value
                self._model.checkedChanged.emit()
            super().setData(value, role)


    class MyFileItemModel(QStandardItemModel):
        
        checkedChanged = pyqtSignal()
        filesChanged = pyqtSignal()
    
        def __init__(self, parent):
            super().__init__(parent)
            self.show_archives = False
        
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


    class MyTreeView(QTreeView):

        backClicked = pyqtSignal()
        doubleClicked = pyqtSignal(bool, bool)
        spacePressed = pyqtSignal(str, bool, bool)

        def keyPressEvent(self, event: QtGui.QKeyEvent):
            if event.key() == Qt.Key.Key_Space:
                ctrl = Qt.KeyboardModifier.ControlModifier in event.modifiers()
                shift = Qt.KeyboardModifier.ShiftModifier in event.modifiers()
                self.spacePressed.emit(' ', ctrl, shift)
                return
            elif event.key() == Qt.Key.Key_Plus:
                ctrl = Qt.KeyboardModifier.ControlModifier in event.modifiers()
                shift = Qt.KeyboardModifier.ShiftModifier in event.modifiers()
                self.spacePressed.emit('+', ctrl, shift)
                return
            elif event.key() == Qt.Key.Key_Enter or event.key() == Qt.Key.Key_Return:
                ctrl = Qt.KeyboardModifier.ControlModifier in event.modifiers()
                shift = Qt.KeyboardModifier.ShiftModifier in event.modifiers()
                self.spacePressed.emit('\n', ctrl, shift)
                return
            elif event.key() == Qt.Key.Key_Minus:
                ctrl = Qt.KeyboardModifier.ControlModifier in event.modifiers()
                shift = Qt.KeyboardModifier.ShiftModifier in event.modifiers()
                self.spacePressed.emit('-', ctrl, shift)
                return
            super().keyPressEvent(event)

        def mouseDoubleClickEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                ctrl = Qt.KeyboardModifier.ControlModifier in event.modifiers()
                shift = Qt.KeyboardModifier.ShiftModifier in event.modifiers()
                self.doubleClicked.emit(ctrl, shift)
            super().mouseDoubleClickEvent(event)

        def mouseReleaseEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.BackButton:
                self.backClicked.emit()
            super().mouseReleaseEvent(event)


    topLevelsChanged = pyqtSignal(list)
    filesChanged = pyqtSignal()
    selectionChanged = pyqtSignal()
    contextMenuRequested = pyqtSignal(PathExt, PathExt, FilesysBrowserItemType)


    def __init__(self):
        FilesysBrowser._ensure_icons_loaded()
        super().__init__()

        self._simplified = False
        self._contextmenu_point: QPoint = None
        self._contextmenu_item: FilesysBrowser.MyFileItem = None
        self._inhibit_triggers = True
        self._show_archives = False
        self._filter: FileFilter = FileFilter()
        self._history: list[tuple[PathExt,PathExt]] = []
        
        self._ui_filesys_view = FilesysBrowser.MyTreeView()
        self._ui_filesys_model = FilesysBrowser.MyFileItemModel(self._ui_filesys_view)
        self._ui_filesys_model.setHorizontalHeaderLabels(['File', 'Info'])
        self._ui_filesys_model.checkedChanged.connect(self._on_checked_change)
        self._ui_filesys_model.filesChanged.connect(self._on_files_changed)
        self._ui_filesys_model.show_archives = self._show_archives
        self._ui_filesys_view.setToolTip('Select files to plot; right-click a directory to navigate')
        self._ui_filesys_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._ui_filesys_view.setModel(self._ui_filesys_model)
        self._ui_filesys_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._ui_filesys_view.selectionModel().selectionChanged.connect(self._on_selection_change)
        self._ui_filesys_view.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self._ui_filesys_view.customContextMenuRequested.connect(self._on_contextmenu_requested)
        self._ui_filesys_view.backClicked.connect(self._on_navigate_back)
        self._ui_filesys_view.doubleClicked.connect(self._on_doubleclicked)
        self._ui_filesys_view.spacePressed.connect(self._on_space_pressed)
        self._ui_pathbar = PathBar()
        self._ui_pathbar.default_mode = PathBar.Mode.Breadcrumbs
        self._ui_pathbar.backClicked.connect(self._on_navigate_back)
        self._ui_pathbar.pathChanged.connect(self._on_pathbar_change)
        self._ui_pathbar.pathAdded.connect(self._on_pathbar_add)
        self._ui_pathbar.pathClosed.connect(self._on_pathbar_close)
        self.setLayout(QtHelper.layout_v(self._ui_filesys_view, self._ui_pathbar))

        self.update_pathbar()
        self._inhibit_triggers = False


    def simplified(self) -> bool:
        return self._simplified
    def setSimplified(self, value: bool):
        if self._simplified == value:
            return
        self._simplified = value
        if self._simplified:
            toplevel_items = self._get_toplevel_items()
            if len(toplevel_items) < 1:
                return  # probably the tree is not fully constructed yet
            for i in range(1, len(toplevel_items)):
                self.remove_toplevel(toplevel_items[i].path)
        self.update_pathbar()
    

    @property
    def show_archives(self) -> bool:
        return self._show_archives
    @show_archives.setter
    def show_archives(self, value: bool):
        if value == self._show_archives:
            return
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
        def recurse(parent: FilesysBrowser.MyFileItem):
            if parent is None:
                return
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.type == FilesysBrowserItemType.File:
                    do_select = item.path in selected_paths
                    item.checked = do_select
                    if not do_select:
                        # de-select, otherwise the next multi-selection that the user does might behave in an unexpected way
                        self._ui_filesys_view.selectionModel().select(item.index(), QItemSelectionModel.SelectionFlag.Deselect | QItemSelectionModel.SelectionFlag.Rows)
                else:
                    recurse(item)
        try:
            self._inhibit_triggers = True
            recurse(self._ui_filesys_model.invisibleRootItem())
        finally:
            self._inhibit_triggers = False
        self.selectionChanged.emit()
    

    @property
    def filter(self) -> FileFilter:
        return self._filter
    @filter.setter
    def filter(self, value: FileFilter):
        if value == self._filter:
            return
        self._filter = value
        self.refresh()
    

    def select_first_file(self):
        def recurse(parent: FilesysBrowser.MyFileItem) -> bool:
            if parent is None:
                return False
            for row_index in range(parent.rowCount()):
                item = parent.child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.type == FilesysBrowserItemType.File:
                    item.checked = True
                    return True
                if recurse(item):
                    return
            return False
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
        try:
            self._inhibit_triggers = True
            recurse(self._ui_filesys_model.invisibleRootItem())
        finally:
            self._inhibit_triggers = False
    

    def add_toplevel(self, path: PathExt):
        if self._simplified:
            toplevel_items = self._get_toplevel_items()
            if len(toplevel_items) >= 1:
                self.change_root(toplevel_items[0].path, path)
                return
        
        try:
            self._inhibit_triggers = True
            self._add_toplevel(path, 0)
                
            if self._simplified:
                self._ui_pathbar.path = str(path)
                self._ui_pathbar.show_navigation = True
        
            self.update_pathbar()

        finally:
            self._inhibit_triggers = False
        self.topLevelsChanged.emit([str(item.path) for item in self._get_toplevel_items()])
        self.filesChanged.emit()


    def remove_toplevel(self, path: PathExt):
        if len(self._get_toplevel_items()) <= 1:
            return #  only one top-level element left; ignore
        try:
            self._inhibit_triggers = True
            
            for row_index in reversed(range(self._ui_filesys_model.invisibleRootItem().rowCount())):
                item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                if item.path == path:
                    self._ui_filesys_model.removeRow(row_index)
            
            self.update_pathbar()
        finally:
            self._inhibit_triggers = False
        self.topLevelsChanged.emit([str(item.path) for item in self._get_toplevel_items()])
        self.filesChanged.emit()

    
    def change_root(self, current_root: PathExt, new_root: PathExt):
        self._add_to_history(current_root, new_root)
        self._change_root(current_root, new_root)


    def _change_root(self, current_root: PathExt, new_root: PathExt):
        try:
            self._inhibit_triggers = True
            
            toplevel_item: FilesysBrowser.MyFileItem = None
            if self._simplified:
                toplevel_item = self._get_toplevel_items()[0]
            else:
                for toplevel_item in self._get_toplevel_items():
                    if toplevel_item.path == current_root:
                        break
            if toplevel_item is None:
                return
            
            toplevel_row_index = self._ui_filesys_model.indexFromItem(toplevel_item).row()
            self._ui_filesys_model.removeRow(toplevel_row_index)
            new_item = self._add_toplevel(new_root, toplevel_row_index)
            self._ui_filesys_view.expand(self._ui_filesys_model.indexFromItem(new_item))
            
            self.update_pathbar()

        finally:
            self._inhibit_triggers = False
        self.topLevelsChanged.emit([str(item.path) for item in self._get_toplevel_items()])
        self.filesChanged.emit()


    def show_context_menu(self, items: list[tuple[str,Callable|list]]):
        point = self._contextmenu_point or QCursor().pos()
        QtHelper.show_popup_menu(self, items, point)


    def refresh(self):
        # TODO: re-select previously selected items

        try:
            self._inhibit_triggers = True
            toplevel_paths: list[PathExt] = []
            for row_index in range(self._ui_filesys_model.invisibleRootItem().rowCount()):
                item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
                if not isinstance(item, FilesysBrowser.MyFileItem):
                    continue
                toplevel_paths.append(item.path)
            
            self._ui_filesys_model.invisibleRootItem().removeRows(0, self._ui_filesys_model.invisibleRootItem().rowCount())

            for i,path in enumerate(toplevel_paths):
                self._add_toplevel(path, i)
            
            self.update_pathbar()

        finally:
            self._inhibit_triggers = False

        self.filesChanged.emit()
    

    def _get_toplevel_item_for_pathbar(self) -> FilesysBrowser.MyFileItem|None:
        if self._simplified:
            toplevel_items = self._get_toplevel_items()
            if len(toplevel_items) < 1:
                return None
            return toplevel_items[0]

        # is there exactly one top-level item?
        toplevel_items = self._get_toplevel_items()
        if len(toplevel_items) == 1:
            return toplevel_items[0]

        # is there exactly one selected item?
        selected_items = self._get_all_selected_items()
        if len(selected_items) == 1:
            parent = self._find_toplevel_item(selected_items[0])
            if parent:
                return parent

        return None

    
    def update_pathbar(self):
        toplevel_item_for_pathbar = self._get_toplevel_item_for_pathbar()
        if toplevel_item_for_pathbar:
            all_toplevel_items = self._get_toplevel_items()
            self._ui_pathbar.path = toplevel_item_for_pathbar.path
            self._ui_pathbar.show_navigation = True
            self._ui_pathbar.allow_close = len(all_toplevel_items) > 1
        else:  # no top-level item found
            self._ui_pathbar.show_navigation = False
            self._ui_pathbar.allow_close = False
        self._ui_pathbar.allow_add = not self._simplified

    
    def _add_toplevel(self, path: PathExt, row_index: int):
        for row_index in range(self._ui_filesys_model.invisibleRootItem().rowCount()):
            item = self._ui_filesys_model.invisibleRootItem().child(row_index, 0)
            if not isinstance(item, FilesysBrowser.MyFileItem):
                continue
            if item.path == path:
                return  # path is already at top-level; ignore

        if path.is_dir():
            new_item = FilesysBrowser.MyFileItem(self._ui_filesys_model, path, FilesysBrowserItemType.Dir, is_toplevel=True, filter=self._filter)
        elif path.is_file() and is_ext_supported_archive(path.suffix):
            if not self._show_archives:
                return None
            new_item = FilesysBrowser.MyFileItem(self._ui_filesys_model, path, FilesysBrowserItemType.Arch, is_toplevel=True, filter=self._filter)
        else:
            return  # files cannot be a top-lvel item; ignore
        
        self._ui_filesys_model.insertRow(row_index, new_item)
        new_item_index = self._ui_filesys_model.indexFromItem(new_item)
        if new_item_index:
            self._ui_filesys_view.expand(new_item_index)
        
    
    def _get_all_selected_items(self) -> list[FilesysBrowser.MyFileItem]:
        return list([item for item in [self._ui_filesys_model.itemFromIndex(index) for index in self._ui_filesys_view.selectedIndexes()] if isinstance(item, FilesysBrowser.MyFileItem)])
        
    
    def _get_toplevel_items(self) -> list[FilesysBrowser.MyFileItem]:
        all_toplevel_items = [self._ui_filesys_model.invisibleRootItem().child(i, 0) for i in range(self._ui_filesys_model.invisibleRootItem().rowCount())]
        return list([item for item in all_toplevel_items if isinstance(item, FilesysBrowser.MyFileItem)])


    def _find_toplevel_item(self, item: FilesysBrowser.MyFileItem) -> FilesysBrowser.MyFileItem|None:
        if item is None or not isinstance(item, FilesysBrowser.MyFileItem):
            return None
        if item.is_toplevel:
            return item
        return self._find_toplevel_item(item.parent())


    def _check_items(self, items: list[FilesysBrowser.MyFileItem], toggle: bool = False, toggle_common: bool = False, toggle_exclusive: bool = False, modify_to = None):

        if toggle and toggle_common:

            def get_number_of_checked_items_recursively(parent: FilesysBrowser.MyFileItem):
                n_total, n_checked = 0, 0
                nonlocal any_changed
                if parent is None:
                    return
                for row_index in range(parent.rowCount()):
                    item = parent.child(row_index, 0)
                    if not isinstance(item, FilesysBrowser.MyFileItem):
                        continue
                    if item in items:
                        n_total += 1
                        if item.checked:
                            n_checked += 1
                    sub_total, sub_checked = get_number_of_checked_items_recursively(item)
                    n_total += sub_total
                    n_checked += sub_checked
                return n_total, n_checked
            
            n_total, n_checked = get_number_of_checked_items_recursively(self._ui_filesys_model.invisibleRootItem())
            if n_checked > 0 and n_checked < n_total:
                # some, but not all, are checked -> check all
                toggle_to_on = True
            elif n_checked <= n_total/2:
                # majority is un-checked -> check all
                toggle_to_on = True
            else:
                # majority is checked -> un-check all
                toggle_to_on = False

        any_changed = False
        try:
            self._inhibit_triggers = True
            def recurse(parent: FilesysBrowser.MyFileItem):
                nonlocal any_changed
                if parent is None:
                    return
                for row_index in range(parent.rowCount()):
                    item = parent.child(row_index, 0)
                    if not isinstance(item, FilesysBrowser.MyFileItem):
                        continue
                    if toggle:
                        if toggle_common:
                            if item in items:
                                if item.checked != toggle_to_on:
                                    item.checked = toggle_to_on
                                    any_changed = True
                            else:
                                if toggle_exclusive and item.checked:
                                    item.checked = False
                                    any_changed = True
                        else:
                            if item in items:
                                item.checked = not item.checked
                                any_changed = True
                            else:
                                if toggle_exclusive and item.checked:
                                    item.checked = False
                                    any_changed = True
                    elif modify_to is not None:
                        if item in items and item.checked != modify_to:
                            item.checked = modify_to
                            any_changed = True
                    else:
                        do_check = item in items
                        if item.checked != do_check:
                            item.checked = do_check
                            any_changed = True
                    recurse(item)
            recurse(self._ui_filesys_model.invisibleRootItem())
        finally:
            self._inhibit_triggers = False
        if any_changed:
            self.selectionChanged.emit()
    

    def _on_selection_change(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection):

        if self._inhibit_triggers:
            return
        
        self.update_pathbar()

        if Settings.select_file_to_check:
            selected_items = self._get_all_selected_items()
            if len(selected_items)==1:
                if selected_items[0].type != FilesysBrowserItemType.File:
                    return  # the user selected a single non-file; do not change the checkboxes
            self._check_items(selected_items)
        
    
    def _on_files_changed(self):
        if self._inhibit_triggers:
            return
        self._ui_filesys_view.header().resizeSections(QHeaderView.ResizeMode.ResizeToContents)
        self.filesChanged.emit()
    

    def _on_checked_change(self):
        if self._inhibit_triggers:
            return
        self.selectionChanged.emit()

    
    def _find_toplevel_item(self, child_item: FilesysBrowser.MyFileItem) -> FilesysBrowser.MyFileItem:
        def recurse(item: FilesysBrowser.MyFileItem):
            if item.is_toplevel:
                return item
            parent = item.parent()
            if not isinstance(parent, FilesysBrowser.MyFileItem):
                raise RuntimeError(f'Cannot find toplevel item of {child_item}')
            return recurse(parent)
        return recurse(child_item)


    def _on_contextmenu_requested(self, point: QPoint):
        self._contextmenu_point = self._ui_filesys_view.mapToGlobal(point)
        index = self._ui_filesys_view.indexAt(point)
        if not index:
            return
        item: FilesysBrowser.MyFileItem = self._ui_filesys_model.itemFromIndex(index)
        if not isinstance(item, FilesysBrowser.MyFileItem):
            return
        top_item = self._find_toplevel_item(item)
        if not isinstance(top_item, FilesysBrowser.MyFileItem):
            return
        self._contextmenu_item = item
        self.contextMenuRequested.emit(item.path, top_item.path, item.type)


    def _on_pathbar_change(self, path: str):
        toplevel_item = self._get_toplevel_item_for_pathbar()
        if toplevel_item is None:
            return
        self.change_root(toplevel_item.path, PathExt(path))


    def _on_pathbar_add(self, path: str):
        self.add_toplevel(PathExt(path))


    def _on_pathbar_close(self):
        toplevel_item = self._get_toplevel_item_for_pathbar()
        if not toplevel_item:
            return
        self.remove_toplevel(toplevel_item.path)
    

    def _on_navigate_back(self):
        if len(self._history) < 1:
            return
        from_path, to_path = self._history.pop()
        self._change_root(to_path, from_path)
    

    def _on_doubleclicked(self, ctrl: bool, shift: bool):
        if not Settings.select_file_to_check:
            selected_items = self._get_all_selected_items()
            self._check_items(selected_items, toggle=True, toggle_common=True, toggle_exclusive=shift)
    

    def _on_space_pressed(self, key: str, ctrl: bool, shift: bool):
        selected = self._get_all_selected_items()
        if key==' ':
            self._check_items(selected, toggle=True, toggle_common=not ctrl, toggle_exclusive=shift)
        elif key=='+':
            self._check_items(selected, modify_to=True)
        elif key=='\n':
            self._check_items(selected)
        elif key=='-':
            self._check_items(selected, modify_to=False)


    @staticmethod
    def _ensure_icons_loaded():
        def ensure_icon_loaded(icon: QIcon, filename: str) -> QIcon:
            if icon:
                return icon
            try:
                return QtHelper.load_resource_icon(filename)
            except Exception as ex:
                logging.warning(f'Unable to load icon <{filename}> from resource directory ({ex})')
                return QIcon()
        
        FilesysBrowser._icon_file = ensure_icon_loaded(FilesysBrowser._icon_file, 'filesys_file.svg')
        FilesysBrowser._icon_dir  = ensure_icon_loaded(FilesysBrowser._icon_dir,  'filesys_directory.svg')
        FilesysBrowser._icon_arch = ensure_icon_loaded(FilesysBrowser._icon_arch, 'filesys_archive.svg')


    def _add_to_history(self, from_path: PathExt, to_path: PathExt):
        self._history.append((from_path, to_path))
        while len(self._history) > FilesysBrowser.MAX_HISTORY:
            del(self._history[0])
