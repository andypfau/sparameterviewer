from __future__ import annotations
from ..helpers.qt_helper import QtHelper
from ..helpers.simple_dialogs import open_directory_dialog
from lib import AppPaths
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import pathlib
import os
import enum



class PathBar(QWidget):


    class Mode(enum.Enum):
        Text = enum.auto()
        Breadcrumbs = enum.auto()


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
    

    class MyLabel(QLabel):
        
        blankClicked = pyqtSignal()

        def __init__(self):
            super().__init__()
            self.linkActivated.connect(self._on_link)
            self._timer: QTimer = None

        def mousePressEvent(self, event: QMouseEvent):
            if self._timer:
                self._timer.stop()
            else:
                self._timer = QTimer()
                self._timer.timeout.connect(self._on_timeout)
                self._timer.setSingleShot(True)
            self._timer.start(100)
            super().mousePressEvent(event)

        def _on_link(self):
            if self._timer:
                self._timer.stop()
                del self._timer
                self._timer = None

        def _on_timeout(self):
            if self._timer:
                self._timer.stop()
                del self._timer
                self._timer = None
            self.blankClicked.emit()


    pathChanged = pyqtSignal(str)
    pathAdded = pyqtSignal(str)
    pathClosed = pyqtSignal()
    backClicked = pyqtSignal()


    def __init__(self, path: str|None = None):
        super().__init__()
        if not path:
            path = AppPaths.get_default_file_dir()
        self._path = pathlib.Path(path)
        self._breadcrumb_paths: dict[any,pathlib.Path] = {}
        self._enabled = True
        self._default_mode = PathBar.Mode.Breadcrumbs

        self._ui_toggle_breadcrumbs_button = QtHelper.make_toolbutton(self, None, self._on_switch_to_breadcrumbs, icon='path_breadcrumbs.svg', tooltip='Show Breadcrumb Bar')
        self._ui_toggle_text_button = QtHelper.make_toolbutton(self, None, self._on_switch_to_text, icon='path_text.svg', tooltip='Show Text Editor')
        self._ui_dir_select_dialog_button = QtHelper.make_toolbutton(self, None, self._on_open_dir_select_dialog, icon='path_browse.svg', tooltip='Navigate to Directory...')
        self._ui_add_dir_button = QtHelper.make_toolbutton(self, None, self._on_add_dir_select_dialog, icon='path_add.svg', tooltip='Add another Directory...')
        self._ui_add_dir_button.setVisible(False)
        self._ui_close_button = QtHelper.make_toolbutton(self, None, self._on_close_dir, icon='path_close.svg')
        self._ui_close_button.setVisible(False)
        self._ui_breadcrumb = PathBar.MyWidget()
        self._ui_breadcrumb.setContentsMargins(0, 0, 0, 0)
        self._ui_breadcrumb.setVisible(False)
        self._ui_breadcrumb.blankClicked.connect(self._on_outside_breadcrumb_click)
        self._ui_breadcrumb.backClicked.connect(self._on_back_click)
        self._ui_breadcrumb.setToolTip('Click to navigate; click blank area to show text input')
        self._ui_breadcrumb_label = PathBar.MyLabel()
        self._ui_breadcrumb_label.linkActivated.connect(self._on_link_click)
        self._ui_breadcrumb_label.blankClicked.connect(self._on_outside_breadcrumb_click)
        self._ui_breadcrumb_label.setContentsMargins(0, 0, 0, 0)
        self._ui_breadcrumb_label.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        layout = QtHelper.layout_h(self._ui_breadcrumb_label)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._ui_breadcrumb.setLayout(layout)
        self._ui_text = PathBar.MyLineEdit(self)
        self._ui_text.setText(str(self._path.absolute()))
        self._ui_text.setToolTip('Press Enter to accept path / Escape to discard, and show breadcrumb bar')
        self._ui_text.returnPressed.connect(self._text_press_enter)
        self._ui_text.escapePressed.connect(self._text_press_escape)
        self._ui_text.backClicked.connect(self._on_back_click)
        self._ui_text_completer_model = QFileSystemModel()
        self._ui_text_completer_model.setRootPath('')
        self._ui_text_completer = QCompleter(self._ui_text_completer_model)
        self._ui_text_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._ui_text_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self._ui_text.setCompleter(self._ui_text_completer)
        self._ui_empty_pane = QtHelper.layout_widget_h(..., spacing=0, margins=0)
        self._ui_empty_pane.setVisible(False)
        self._ui_navigation_pane = QtHelper.layout_widget_h(
            self._ui_breadcrumb,
            self._ui_text,
            self._ui_toggle_breadcrumbs_button,
            self._ui_toggle_text_button,
            self._ui_dir_select_dialog_button,
            self._ui_close_button,
            spacing=0, margins=0
        )
        layout = QtHelper.layout_h(
            self._ui_navigation_pane,
            self._ui_empty_pane,
            self._ui_add_dir_button,
            spacing=0, margins=0
        )
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        if self._default_mode == PathBar.Mode.Breadcrumbs:
            self._update_and_show_breadcrumbs()
        else:
            self._update_and_show_text()
    

    @property
    def mode(self) -> PathBar.Mode:
        if self._ui_breadcrumb.isVisible():
            return PathBar.Mode.Breadcrumbs
        return PathBar.Mode.Text


    @property
    def allow_close(self) -> bool:
        return self._ui_close_button.isVisible()
    @allow_close.setter
    def allow_close(self, value: bool):
        self._ui_close_button.setVisible(value)


    @property
    def allow_add(self) -> bool:
        return self._ui_add_dir_button.isVisible()
    @allow_add.setter
    def allow_add(self, value: bool):
        self._ui_add_dir_button.setVisible(value)


    @property
    def show_navigation(self) -> bool:
        return self._ui_navigation_pane.isVisible()
    @show_navigation.setter
    def show_navigation(self, value: bool):
        self._ui_navigation_pane.setVisible(value)
        self._ui_empty_pane.setVisible(not value)


    @property
    def default_mode(self) -> PathBar.Mode:
        return self._default_mode
    @default_mode.setter
    def default_mode(self, value: PathBar.Mode):
        self._default_mode = value


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
        if self._default_mode == PathBar.Mode.Breadcrumbs:
            self._update_and_show_breadcrumbs()
        else:
            self._update_and_show_text()
    

    def enabled(self) -> bool:
        return self._enabled
    def setEnabled(self, value: bool):
        if self._enabled == value:
            return
        self._enabled = value
        if self._default_mode == PathBar.Mode.Breadcrumbs:
            self._update_and_show_breadcrumbs()
        else:
            self._update_and_show_text()


    def _text_press_enter(self):
        if not self._enabled:
            return
        path = pathlib.Path(self._ui_text.text())
        if not (path.exists() and path.is_dir()):
            QtHelper.indicate_error(self._ui_text, True)
            return
        QtHelper.indicate_error(self._ui_text, False)
        
        actually_changed = self._path != path
        self._path = path
        if self._default_mode == PathBar.Mode.Breadcrumbs:
            self._update_and_show_breadcrumbs()
        else:
            self._update_and_show_text()
        if actually_changed:
            self.pathChanged.emit(str(path.absolute()))


    def _text_press_escape(self):
        if not self._enabled:
            return
        if self._default_mode == PathBar.Mode.Breadcrumbs:
            self._update_and_show_breadcrumbs()
        else:
            self._update_and_show_text()


    def _implement_enabled_state(self):
        self._ui_toggle_text_button.setEnabled(self._enabled)
        self._ui_toggle_breadcrumbs_button.setEnabled(self._enabled)
        self._ui_dir_select_dialog_button.setEnabled(self._enabled)
        self._ui_text.setEnabled(self._enabled)
        if self._enabled:
            self._ui_text.setPlaceholderText('Enter path...')
        else:
            self._ui_text.setText('')
            QtHelper.indicate_error(self._ui_text, False)
            self._ui_text.setPlaceholderText('')
            self._ui_breadcrumb.setVisible(False)
            self._ui_text.setVisible(True)


    def _update_and_show_text(self):
        self._implement_enabled_state()
        if not self._enabled:
            return

        if not self._path.exists():
            return

        self._ui_breadcrumb.setVisible(False)
        self._ui_text.setText(str(self._path.absolute()))
        QtHelper.indicate_error(self._ui_text, False)
        self._ui_text.setEnabled(True)
        self._ui_text.setVisible(True)
        self._ui_text.setFocus()
        self._ui_toggle_text_button.setVisible(False)
        self._ui_toggle_breadcrumbs_button.setVisible(True)


    def _update_and_show_breadcrumbs(self):
        self._implement_enabled_state()
        if not self._enabled:
            return
        
        if not self._path.exists():
            return
        
        def path_to_disp_str(path: pathlib.Path) -> str:
            if path.parent == path:
                s = path.anchor
            else:
                s = path.name
            return s.strip(os.sep)
        
        self._breadcrumb_paths.clear()

        paths = [self._path]
        while paths[0].parent != paths[0]:
            paths.insert(0, paths[0].parent)

        label_width = self._ui_breadcrumb_label.width()
        font_metrics = QFontMetrics(self._ui_breadcrumb_label.font())
        char_width = font_metrics.averageCharWidth()
        MARGIN_CHARS = 3
        max_chars = label_width // char_width - MARGIN_CHARS
        SHORTENER = '...'
        shortened = False
        while True:
            plaintext = os.sep.join([path_to_disp_str(p) for p in paths])
            if shortened:
                plaintext += os.sep + SHORTENER
            if len(plaintext) <= max_chars:
                break
            if len(paths) < 3:
                break
            del paths[1]
            shortened = True
        
        html_parts = []
        for i,path in enumerate(paths):
            identifier = f'#{i}'
            if shortened and i==1:
                html_parts.append(SHORTENER)
            html_parts.append(f'<a href="{identifier}">{path_to_disp_str(path)}</a>')
            self._breadcrumb_paths[identifier] = path
        html = os.sep.join(html_parts)
        
        self._ui_breadcrumb_label.setText(html)
        self._ui_text.setVisible(False)
        self._ui_breadcrumb.setVisible(True)
        self._ui_toggle_text_button.setVisible(True)
        self._ui_toggle_breadcrumbs_button.setVisible(False)


    def _on_link_click(self, identifier):
        if not self._enabled:
            return
        try:
            path = self._breadcrumb_paths[identifier]
        except:
            return

        if not path.is_dir() or not path.exists():
            return
        
        actually_changed = self._path != path
        self._path = pathlib.Path(path)
        if self._default_mode == PathBar.Mode.Breadcrumbs:
            self._update_and_show_breadcrumbs()
        else:
            self._update_and_show_text()
        if actually_changed:
            self.pathChanged.emit(str(path.absolute()))
        
    
    def _on_outside_breadcrumb_click(self):
        if not self._enabled:
            return
        self._update_and_show_text()
    

    def _on_back_click(self):
        if not self._enabled:
            return
        self.backClicked.emit()


    def _on_switch_to_breadcrumbs(self):
        if not self._enabled:
            return
        self._update_and_show_breadcrumbs()


    def _on_switch_to_text(self):
        if not self._enabled:
            return
        self._update_and_show_text()


    def _on_add_dir_select_dialog(self):
        if not self._enabled:
            return
        
        current_dir = self.path
        new_dir = open_directory_dialog(self, title='Select Directory to Append', initial_dir=current_dir)
        if not new_dir:
            return
        
        new_dir = os.path.abspath(new_dir)
        if not (os.path.exists(new_dir) and os.path.isdir(new_dir)):
            return
        if os.path.samefile(current_dir, new_dir):
            return
        
        self.path = str(new_dir)
        self.pathAdded.emit(new_dir)

    
    def _on_open_dir_select_dialog(self):
        if not self._enabled:
            return
        
        current_dir = self.path
        new_dir = open_directory_dialog(self, title='Select Directory', initial_dir=current_dir)
        if not new_dir:
            return
        
        new_dir = os.path.abspath(new_dir)
        if not (os.path.exists(new_dir) and os.path.isdir(new_dir)):
            return
        if os.path.samefile(current_dir, new_dir):
            return
        
        self.path = str(new_dir)
        self.pathChanged.emit(new_dir)


    def _on_close_dir(self):
        self.pathClosed.emit()
