from lib import AppPaths
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib



class PathBar(QWidget):

    pathChanged = pyqtSignal(str)

    def __init__(self, path: str|None = None):
        super().__init__()
        if not path:
            path = AppPaths.get_default_file_dir()
        self._path = pathlib.Path(path)

        self._text = QLineEdit(self)
        self._text.setText(str(self._path.absolute()))
        self._text.returnPressed.connect(self._text_press_enter)
        self._layout = QHBoxLayout()
        self._layout.addWidget(self._text)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)
    

    @property
    def path(self) -> str:
        return str(self._path.absolute())
    @path.setter
    def path(self, path_str: str):
        path = pathlib.Path(path_str)
        if not path.exists():
            return
        if path.is_file():
            path = path.parent
        if not path.is_dir() or not path.exists():
            return
        if self._path == path:
            return
        self._path = pathlib.Path(path)
        self._text.setText(str(self._path.absolute()))


    def _text_press_enter(self):
        path = pathlib.Path(self._text.text())
        if not (path.exists() and path.is_dir()):
            return
        self._path = path
        self.pathChanged.emit(str(path.absolute()))
