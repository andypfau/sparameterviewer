from .qt_helper import QtHelper
from lib import AppPaths
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os



class PathBar(QWidget):


    class WidgetClick(QWidget):

        blankClicked = pyqtSignal(QPoint)

        def mouseReleaseEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.LeftButton:
                child = self.childAt(event.pos())
                if child is None:
                    self.blankClicked.emit(event.pos())
            super().mouseReleaseEvent(event)
        
        
    class LineEditEsc(QLineEdit):
        escapePressed = pyqtSignal()
        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Escape:
                self.escapePressed.emit()
            else:
                super().keyPressEvent(event)


    pathChanged = pyqtSignal(str)


    def __init__(self, path: str|None = None):
        super().__init__()
        if not path:
            path = AppPaths.get_default_file_dir()
        self._path = pathlib.Path(path)
        self._breadcrumb_paths: list[pathlib.Path] = []
        self._breadcrumb_widgets: list[QWidget] = []

        self._breadcrumb = PathBar.WidgetClick()
        self._breadcrumb.setVisible(False)
        self._breadcrumb.blankClicked.connect(self._on_outside_breadcrumb_click)
        self._breadcrumb_layout = QHBoxLayout()
        self._breadcrumb_layout.setContentsMargins(0, 0, 0, 0)
        self._breadcrumb_layout.setSpacing(0)
        self._breadcrumb.setLayout(self._breadcrumb_layout)
        self._text = PathBar.LineEditEsc(self)
        self._text.setText(str(self._path.absolute()))
        self._text.returnPressed.connect(self._text_press_enter)
        self._text.escapePressed.connect(self._text_press_escape)
        layout = QtHelper.layout_v(self._breadcrumb, self._text)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
    

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
        
        actually_changed = self._path != path
        self._path = path
        self._update_and_show_breadcrumbs()
        if actually_changed:
            self.pathChanged.emit(str(path.absolute()))


    def _text_press_enter(self):
        path = pathlib.Path(self._text.text())
        if not (path.exists() and path.is_dir()):
            return
        
        actually_changed = self._path != path
        self._path = path
        self.pathChanged.emit(str(path.absolute()))
        self._breadcrumb.setVisible(False)
        self._text.setVisible(True)
        if actually_changed:
            self.pathChanged.emit(str(path.absolute()))


    def _update_and_show_text(self):
        if not self._path.exists():
            return

        self._text.setText(str(self._path.absolute()))
        self._breadcrumb.setVisible(False)
        self._text.setVisible(True)
        self._text.setFocus()


    def _update_and_show_breadcrumbs(self):
        if not self._path.exists():
            return
        
        # empty layout
        for i in reversed(range(len(self._breadcrumb_widgets))):
            item = self._breadcrumb_widgets[i]
            if isinstance(item, QWidget):
                self._breadcrumb_layout.removeWidget(item)
            elif isinstance(item, QSpacerItem):
                self._breadcrumb_layout.removeItem(item)
            del self._breadcrumb_widgets[i]
        
        self._breadcrumb_paths = []
        parts = list(self._path.parts)
        prev_part = None
        parts_so_far = []
        self._breadcrumb_widgets = []
        for i, part in enumerate(parts):
            
            parts_so_far.append(part)
            self._breadcrumb_paths.append(pathlib.Path(os.path.join(*parts_so_far)))

            if (i > 0) and (prev_part != os.sep):
                separator = QLabel(os.sep)
                separator.setContentsMargins(0, 0, 0, 0)
                self._breadcrumb_layout.addWidget(separator)
                self._breadcrumb_widgets.append(separator)

            link = QLabel(f'<a href="{i}">{part}</a>')
            link.setContentsMargins(0, 0, 0, 0)
            link.setOpenExternalLinks(False)
            link.linkActivated.connect(self._on_link_click)
            self._breadcrumb_widgets.append(link)
            self._breadcrumb_layout.addWidget(link)

            prev_part = part
        stretch = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding)
        self._breadcrumb_widgets.append(stretch)
        self._breadcrumb_layout.addSpacerItem(stretch)

        self._text.setVisible(False)
        self._breadcrumb.setVisible(True)


    def _text_press_escape(self):
        self._update_and_show_breadcrumbs()


    def _on_link_click(self, identifier):
        try:
            path = self._breadcrumb_paths[int(identifier)]
        except:
            return

        if not path.is_dir() or not path.exists():
            return
        
        actually_changed = self._path != path
        self._path = pathlib.Path(path)
        self._update_and_show_text()
        if actually_changed:
            self.pathChanged.emit(str(path.absolute()))
        
    
    def _on_outside_breadcrumb_click(self):
        self._breadcrumb.setVisible(False)
        self._text.setVisible(True)
        self._text.setFocus()
