from .qt_helper import QtHelper
from lib import AppPaths
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class PathBar(QWidget):


    class MyWidget(QWidget):

        blankClicked = pyqtSignal()
        backClicked = pyqtSignal()

        def mouseReleaseEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.BackButton:
                self.backClicked.emit()
            elif event.button() == Qt.MouseButton.LeftButton:
                child = self.childAt(event.pos())
                if child is None:
                    self.blankClicked.emit()
            super().mouseReleaseEvent(event)
        
        
    class MyLineEdit(QLineEdit):
        
        escapePressed = pyqtSignal()
        backClicked = pyqtSignal()

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Escape:
                self.escapePressed.emit()
            else:
                super().keyPressEvent(event)

        def mouseReleaseEvent(self, event: QMouseEvent):
            if event.button() == Qt.MouseButton.BackButton:
                self.backClicked.emit()
            super().mouseReleaseEvent(event)


    pathChanged = pyqtSignal(str)
    backClicked = pyqtSignal()


    def __init__(self, path: str|None = None):
        super().__init__()
        if not path:
            path = AppPaths.get_default_file_dir()
        self._path = pathlib.Path(path)
        self._breadcrumb_paths: list[pathlib.Path] = []
        self._enabled = True

        self._toggle_button = QPushButton('...')
        self._toggle_button.clicked.connect(self._on_toggle_breadcrumb)
        self._toggle_button.setContentsMargins(0, 0, 0, 0)
        self._breadcrumb = PathBar.MyWidget()
        self._breadcrumb.setVisible(False)
        self._breadcrumb.blankClicked.connect(self._on_outside_breadcrumb_click)
        self._breadcrumb.backClicked.connect(self._on_back_click)
        self._breadcrumb.setToolTip('Click to navigate; click blank area to show text input')
        self._breadcrumb_label = QLabel()
        self._breadcrumb_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._breadcrumb_label.setWordWrap(True)

        self._breadcrumb_label.linkActivated.connect(self._on_link_click)
        self._breadcrumb.setLayout(QtHelper.layout_h(self._breadcrumb_label, ...))
        self._text = PathBar.MyLineEdit(self)
        self._text.setText(str(self._path.absolute()))
        self._text.setToolTip('Press Enter to accept path / Escape to discard, and show breadcrumb bar')
        self._text.returnPressed.connect(self._text_press_enter)
        self._text.escapePressed.connect(self._text_press_escape)
        self._text.backClicked.connect(self._on_back_click)
        layout = QtHelper.layout_h(self._breadcrumb, self._text, self._toggle_button)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._implement_enabled_state()
    

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
        
        self._path = path
        self._update_and_show_text()
    

    @property
    def enabled(self) -> bool:
        return self._enabled
    @enabled.setter
    def enabled(self, value: bool):
        if self._enabled == value:
            return
        self._enabled = value
        self._update_and_show_text()


    def _text_press_enter(self):
        if not self._enabled:
            return
        path = pathlib.Path(self._text.text())
        if not (path.exists() and path.is_dir()):
            return
        
        actually_changed = self._path != path
        self._path = path
        self._breadcrumb.setVisible(False)
        self._text.setVisible(True)
        if actually_changed:
            self.pathChanged.emit(str(path.absolute()))


    def _implement_enabled_state(self):
        self._toggle_button.setVisible(self._enabled)
        self._text.setEnabled(self._enabled)
        if self._enabled:
            self._text.setPlaceholderText('Enter path...')
        else:
            self._text.setText('')
            self._text.setPlaceholderText('')
            self._breadcrumb.setVisible(False)
            self._text.setVisible(True)


    def _update_and_show_text(self):
        self._implement_enabled_state()
        if not self._enabled:
            return

        if not self._path.exists():
            return

        self._breadcrumb.setVisible(False)
        self._text.setText(str(self._path.absolute()))
        self._text.setEnabled(True)
        self._text.setVisible(True)
        self._text.setFocus()


    def _update_and_show_breadcrumbs(self):
        self._implement_enabled_state()
        if not self._enabled:
            return
        
        if not self._path.exists():
            return
        
        self._breadcrumb_paths = []
        parts = list(self._path.parts)
        prev_part = ''
        parts_so_far = []
        html = ''
        for i, part in enumerate(parts):
            
            parts_so_far.append(part)
            self._breadcrumb_paths.append(pathlib.Path(os.path.join(*parts_so_far)))

            if (i > 0) and (os.sep not in prev_part):
                html += os.sep
            html += f'<a href="{i}">{part}</a>'
            if os.sep in part:
                html += ' '

            prev_part = part
        
        self._breadcrumb_label.setText(html)

        self._text.setVisible(False)
        self._breadcrumb.setVisible(True)


    def _text_press_escape(self):
        if not self._enabled:
            return
        self._update_and_show_text()


    def _on_link_click(self, identifier):
        if not self._enabled:
            return
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
        if not self._enabled:
            return
        self._update_and_show_text()
    

    def _on_toggle_breadcrumb(self):
        if not self._enabled:
            return
        if self._breadcrumb.isVisible():
            self._update_and_show_text()
        elif self._text.isVisible():
            self._update_and_show_breadcrumbs()


    def _on_back_click(self):
        if not self._enabled:
            return
        self.backClicked.emit()
