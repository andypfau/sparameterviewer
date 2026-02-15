from __future__ import annotations

import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from typing import override



class MyCustomRow:
    def __init__(self, path: str, notes: str = '', ref: bool = False):
        self.path, self.notes, self.ref = path, notes, ref
        self.parent: MyCustomRow = None
        self.children: list= []

    def append_child(self, child: MyCustomRow):
        child.parent = self
        self.children.append(child)

    def get_child(self, row: int) -> list:
        return self.children[row]

    def child_count(self) -> int:
        return len(self.children)

    def row_index(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)




class MultiColumnTreeModel(QAbstractItemModel):
    def __init__(self, root, parent=None):
        super().__init__(parent)
        self._root = root

    @override
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 2

    @override
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        node = self._node_from_index(parent)
        return node.child_count()

    @override
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parent_node = self._node_from_index(parent)
        try:
            child_node = parent_node.get_child(row)
        except IndexError:
            return QModelIndex()
        return self.createIndex(row, column, child_node)

    @override
    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        node = self._node_from_index(index)
        parent_node = node.parent
        if parent_node is None or parent_node is self._root:
            return QModelIndex()
        return self.createIndex(parent_node.row_index(), 0, parent_node)

    @override
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> list|None:
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            node = self._node_from_index(index)
            
            text = None
            if index.column() == 0:
                text = node.path
            elif index.column() == 1:
                text = node.notes
                if node.ref:
                    text += ' (ref)'
            assert text is not None
            return text
        return None

    @override
    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> list:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            headers = ["Name", "Type", "Size"]
            if 0 <= section < len(headers):
                return headers[section]
        return None

    @override
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        return base | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def _node_from_index(self, index: QModelIndex) -> MyCustomRow:
        if index.isValid():
            return index.internalPointer()
        return self._root



def main():
    def build_tree():
        root = MyCustomRow('', '')  # dummy root
        
        root.append_child(project := MyCustomRow('/home/', ''))
        project.append_child(MyCustomRow("main.py", "file", True))
        project.append_child(MyCustomRow("README.md", "file"))
        project.append_child(utils := MyCustomRow("utils", "folder"))
        utils.append_child(MyCustomRow("helpers.py", "file"))

        return root

    app = QApplication(sys.argv)
    root = build_tree()
    model = MultiColumnTreeModel(root)
    view = QTreeView()
    view.setModel(model)
    view.setUniformRowHeights(True)
    view.expandAll()
    view.resizeColumnToContents(0)
    view.setWindowTitle("Multi-column QTreeView (custom model)")
    view.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()
