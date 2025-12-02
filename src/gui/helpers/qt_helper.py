from __future__ import annotations
from lib import is_windows, AppPaths, Settings, GuiColorScheme
from PyQt6 import QtCore, QtGui, QtWidgets, QtSvg
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import logging
from pathlib import Path
from typing import Callable, Optional, Union
import re
import dataclasses



class QtHelper:


    PROCESSING_BLACK_TO_CONTRAST = 1


    @staticmethod
    def set_dialog_icon(dialog: Union[QDialog,QMainWindow]):
        if is_windows():
            images_to_try = ['sparamviewer.ico']
        else:
            images_to_try = ['sparamviewer.png', 'sparamviewer.xbm']
        for image in images_to_try:
            try:
                dialog.setWindowIcon(QtHelper.load_resource_icon(image))
                return
            except Exception as ex:
                pass
        logging.error(f'Unable to set window icon')


    @staticmethod
    def load_resource_contrast_icon(filename: str, svg_size: QSize|None = None) -> QIcon:
        return QIcon(QtHelper.load_resource_pixmap(filename=filename, svg_size=svg_size, processing=QtHelper.PROCESSING_BLACK_TO_CONTRAST))


    @staticmethod
    def load_resource_icon(filename: str, svg_size: QSize|None = None) -> QIcon:
        return QIcon(QtHelper.load_resource_pixmap(filename=filename, svg_size=svg_size))


    @staticmethod
    def load_resource_pixmap(filename: str, svg_size: QSize|None = None, processing: int = 0) -> QPixmap:
        path = Path(AppPaths.get_resource_dir()) / filename
        
        if path.suffix.lower() == '.svg':
            
            with open(str(path), 'rb') as fp:
                file_contents = fp.read()

            if processing & QtHelper.PROCESSING_BLACK_TO_CONTRAST:
                processing -= QtHelper.PROCESSING_BLACK_TO_CONTRAST

                if QtHelper.get_current_gui_color_scheme() == GuiColorScheme.Dark:

                    # using dark scheme -> adapt contrast

                    file_xml = file_contents.decode('UTF-8')

                    # find all color codes
                    for m in reversed(list(re.finditer(r'#([0-9a-zA-Z]{6})', file_xml))):
                        color = int(m.group(1), 16)
                        
                        # determine brightness of that color
                        r, g, b = (color >> 16) & 0xFF, (color >> 8) & 0xFF, (color >> 0) & 0xFF
                        brightness = ((float(r)/256) + (float(g)/256) + (float(b)/256)) / 3
                        if brightness < 0.5:
                            
                            # this is a dark color -> darken it
                            rc, gc, bc = 255-r, 255-g, 255-b
                            replacement_str = f'{rc:02X}{gc:02X}{bc:02X}'
                            file_xml = file_xml[:m.start(1)] + replacement_str + file_xml[m.end(1):]

                    file_contents = file_xml.encode('UTF-8')
            
            assert processing == 0, f'Unsupported processing request'

            renderer = QtSvg.QSvgRenderer(file_contents)
            size = svg_size or renderer.defaultSize()
            pixmap = QPixmap(size)
            pixmap.fill(QColorConstants.Transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            return pixmap
        
        else:
            assert processing == 0, f'Unsupported processing request'
            return QPixmap(str(path))


    @staticmethod
    def make_label(text: str, *, font: Optional[QFont] = None, stretch: bool = False) -> QLabel:
        label = QLabel()
        label.setText(text)
        if font:
            label.setFont(font)
        if not stretch:
            label.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed, QSizePolicy.ControlType.Label))
        return label


    @staticmethod
    def make_font(*, base: QFont = None, family: str = None, bold: bool = None, underline: bool = None, strikethru: bool = None, rel_size: float = None) -> QFont:
        if base:
            font = QFont(base)
        else:
            font = QFont()
        if family:
            font.setFamily(family)
        if bold is not None:
            font.setBold(bold)
        if rel_size is not None:
            font.setPointSizeF(font.pointSizeF() * rel_size)
        if underline is not None:
            font.setUnderline(bold)
        if strikethru is not None:
            font.setStrikeOut(strikethru)
        return font


    @staticmethod
    def make_image(path: str, placeholder: str = 'Placeholder') -> QLabel:
        image = QLabel()
        try:
            pixmap = QPixmap(path)
            if pixmap.isNull():
                raise RuntimeError('QPixmap is null')
            image.setPixmap(pixmap)
            image.adjustSize()
        except Exception as ex:
            logging.error('Unable to create QPixmap from <{path}>')
            logging.exception(ex)
            image.setText(placeholder)
        return image


    @staticmethod
    def make_button(parent: QObject, text: str = None, action: Callable = None, /, *, icon: str|QIcon|tuple[str,QSize]|None = None, checked: bool = None, tooltip: str = None, shortcut: str = None) -> QPushButton:
        button = QPushButton()
        button.setText(text)
        if action:
            button.clicked.connect(action)
        if icon:
            image = QtHelper.load_resource_contrast_icon(icon)
            button.setIcon(image)
            sizes = image.availableSizes()
            if len(sizes) >= 1:
                button.setIconSize(sizes[-1])
        if checked is not None:
            button.setCheckable(True)
            button.setChecked(checked)
        if tooltip:
            button.setToolTip(tooltip)
        if shortcut:
            shorcut_obj = QShortcut(QKeySequence(shortcut), parent)
            shorcut_obj.activated.connect(action)
        return button


    @staticmethod
    def make_toolbutton(parent: QObject, text: str = None, action: Callable = None, /, *, icon: str|None = None, checked: bool = None, tooltip: str = None, shortcut: str = None) -> QToolButton:
        button = QToolButton()
        button.setAutoRaise(True)
        button.setText(text)
        if action:
            button.clicked.connect(action)
        if icon:
            image = QtHelper.load_resource_contrast_icon(icon)
            button.setIcon(image)
            sizes = image.availableSizes()
            if len(sizes) >= 1:
                button.setIconSize(sizes[-1])
        if checked is not None:
            button.setCheckable(True)
            button.setChecked(checked)
        if tooltip:
            button.setToolTip(tooltip)
        if shortcut:
            shorcut_obj = QShortcut(QKeySequence(shortcut), parent)
            shorcut_obj.activated.connect(action)
        return button


    @staticmethod
    def make_spring() -> QSpacerItem:
        return QSpacerItem(0, 0, QSizePolicy.Policy.Expanding)


    @staticmethod
    def make_hspace(width: int) -> QSpacerItem:
        return QSpacerItem(width, 0, QSizePolicy.Policy.Fixed)


    @staticmethod
    def make_vspace(height: int) -> QSpacerItem:
        return QSpacerItem(0, height, QSizePolicy.Policy.Fixed)
    

    @staticmethod
    def make_shortcut(parent, shortcut: str, action: Callable) -> QShortcut:
        result = QShortcut(parent)
        result.setKey(QKeySequence(shortcut))
        result.activated.connect(action)
        return result


    @staticmethod
    def show_popup_menu(parent: QWidget, items: list[tuple[str,Callable|list]], position: QPoint, call_wrapper: Callable[[Callable,bool,bool], None]|None = None):
        """
        Builds a menu
        Each key in `items` is the text on a menu item, or `None` to insert a separator.
        Each value in `items` is either a callable (which is called on clicking that item),
          or another dict for a submenu.
        """
        def populate_menu(menu: QMenu, items: list[tuple[str,Callable|list]]):
            for name,action_or_submenu in items:
                if name is None:
                    menu.addSeparator()
                elif isinstance(action_or_submenu, list):
                    submenu = QtHelper.add_submenu(menu, text=name)
                    populate_menu(submenu, items=action_or_submenu)
                else:
                    bold = False
                    if name.startswith('*'):
                        name = name[1:]
                        bold = True
                    if call_wrapper is not None:
                        def make_wrapper(callable):
                            def wrapper():
                                ctrl = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
                                shift = bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)
                                call_wrapper(callable, ctrl, shift)
                            return wrapper
                        action = make_wrapper(action_or_submenu)
                    else:
                        action = action_or_submenu
                    QtHelper.add_menuitem(menu, text=name, action=action, bold=bold)
        menu = QMenu(parent)
        populate_menu(menu, items)
        menu.popup(position)


    @staticmethod
    def add_submenu(parent: QMenu, text: str, visible: bool = True) -> QMenu:
        submenu = QMenu(text, parent)
        if not visible:
            submenu.setVisible(False)
        parent.addMenu(submenu)
        return submenu


    @staticmethod
    def add_menuitem(menu: QMenu, text: str, action: Callable, *, shortcut: str = None, visible: bool = True, checkable: bool = False, bold: bool = False) -> QAction:
        item = QAction(text, menu)
        if action is not None:
            item.triggered.connect(action)
        if shortcut is not None:
            item.setShortcut(QKeySequence(shortcut))
        if checkable:
            item.setCheckable(True)
        if not visible:
            item.setVisible(False)
        if bold:
            item.setFont(QtHelper.make_font(base=item.font(), bold=True))
        menu.addAction(item)
        return item


    @staticmethod
    def add_menu_action(menu: QMenu, widget: QWidget) -> QWidgetAction:
        item = QWidgetAction(menu)
        item.setDefaultWidget(widget)
        menu.addAction(item)
        return item


    @staticmethod
    def get_monospace_font() -> str:
        try:
            preferred_fonts = ['Fira Code', 'DejaVu Mono', 'Liberation Mono', 'Source Code Pro', 'Consolas', 'Courier New', 'Lucida Sans Typewriter', 'Monospace']
            if Settings.editor_font in preferred_fonts:
                return Settings.editor_font
            
            available_fonts = QtHelper.get_all_available_font_families(monospace_only=True)
            for preferred_font in preferred_fonts:
                if preferred_font in available_fonts:
                    Settings.editor_font = preferred_font
                    return preferred_font
        except:
            pass
        
        return QFont().family()  # fallback


    @staticmethod
    def get_all_available_font_families(monospace_only: bool = True) -> list[str]:
        families = QFontDatabase.families()
        if monospace_only:
            families = [family for family in families if QFontDatabase.isFixedPitch(family)]
        return list(families)


    @staticmethod
    def indicate_error(widget: QWidget, indicate_error: bool = True):
        if indicate_error:
            base_color = widget.palette().color(widget.palette(). ColorRole.Base)
            is_light = base_color.lightnessF() >= 0.5
            if is_light:
                bg_color = QColor.fromHsvF(0.0, 0.3, 0.95)
                fg_color = QColor.fromHsvF(0.0, 0.0, 0.0)
            else:
                bg_color = QColor.fromHsvF(0.0, 0.7, 0.7)
                fg_color = QColor.fromHsvF(0.0, 0.0, 1.0)
            style = f'background-color:{bg_color.name()};color:{fg_color.name()};'
        else:
            style = ''
        widget.setStyleSheet(style)


    @staticmethod
    def _box_layout(layout: QBoxLayout, direction: str, *items, margins: int|None = None, spacing: int|None = None) -> QBoxLayout:
        for item in items:
            if item is ...:
                layout.addStretch()
            elif isinstance(item, QSpacerItem):
                layout.addSpacerItem(item)
            elif isinstance(item, QLayoutItem):
                layout.addLayout(item)
            elif isinstance(item, str):
                layout.addWidget(QtHelper.make_label(item))
            elif isinstance(item, int):
                if direction=='h':
                    layout.addSpacerItem(QtHelper.make_hspace(item))
                elif direction=='v':
                    layout.addSpacerItem(QtHelper.make_vspace(item))
                else:
                    raise ValueError()
            else:
                layout.addWidget(item)
        if margins is not None:
            layout.setContentsMargins(margins, margins, margins, margins)
        if spacing is not None:
            layout.setSpacing(spacing)
        return layout


    @staticmethod
    def layout_h(*items, margins: int|None = None, spacing: int|None = None) -> QBoxLayout:
        return QtHelper._box_layout(QHBoxLayout(), 'h', *items, margins=margins, spacing=spacing)


    @staticmethod
    def layout_v(*items, margins: int|None = None, spacing: int|None = None) -> QBoxLayout:
        return QtHelper._box_layout(QVBoxLayout(), 'v', *items, margins=margins, spacing=spacing)


    @dataclasses.dataclass
    class CellSpan:
        item: any
        cols: int = 1
        rows: int = 1


    @staticmethod
    def layout_grid(items_rows_then_columns, margins: int|None = None, spacing: int|None = None) -> QGridLayout:
        layout = QGridLayout()
        for i_row,columns in enumerate(items_rows_then_columns):
            for i_col,item in enumerate(columns):
                cols, rows = 1, 1
                if isinstance(item, QtHelper.CellSpan):
                    item, cols, rows = item.item, item.cols, item.rows
                if item is None:
                    continue
                elif isinstance(item, QLayoutItem):
                    widget = QWidget()
                    widget.setLayout(item)
                    layout.addWidget(widget, i_row, i_col, rows, cols)
                elif isinstance(item, str):
                    layout.addWidget(QtHelper.make_label(item), i_row, i_col, rows, cols)
                else:
                    layout.addWidget(item, i_row, i_col, rows, cols)
        if margins is not None:
            layout.setContentsMargins(margins, margins, margins, margins)
        if spacing is not None:
            layout.setSpacing(spacing)
        return layout


    @staticmethod
    def layout_widget_h(*items, margins: int|None = None, spacing: int|None = None) -> QWidget:
        widget = QWidget()
        widget.setLayout(QtHelper.layout_h(*items, margins=margins, spacing=spacing))
        if margins is not None:
            widget.setContentsMargins(margins, margins, margins, margins)
        return widget


    @staticmethod
    def layout_widget_v(*items, margins: int|None = None, spacing: int|None = None) -> QWidget:
        widget = QWidget()
        widget.setLayout(QtHelper.layout_v(*items, margins=margins, spacing=spacing))
        if margins is not None:
            widget.setContentsMargins(margins, margins, margins, margins)
        return widget


    @staticmethod
    def layout_widget_grid(widgets_rows_then_columns, margins: int|None = None, spacing: int|None = None) -> QWidget:
        widget = QWidget()
        widget.setLayout(QtHelper.layout_grid(*widgets_rows_then_columns, margins=margins, spacing=spacing))
        if margins is not None:
            widget.setContentsMargins(margins, margins, margins, margins)
        return widget


    @staticmethod
    def modify_color(color: QColor, d_hue: float|None = None) -> QColor:
        result = QColor(color)
        if d_hue:
            hue = result.hslHueF() + d_hue
            while hue > 1.0:
                hue -= 1.0
            while hue < 0.0:
                hue += 1.0
            result = QColor.fromHslF(hue, result.hslSaturationF(), result.lightnessF(), result.alphaF())
        return result
    

    @staticmethod
    def get_current_gui_color_scheme() -> GuiColorScheme:
        try:
            if QtWidgets.QApplication.styleHints().colorScheme() == QtCore.Qt.ColorScheme.Dark:
                return GuiColorScheme.Dark
            if QtWidgets.QApplication.styleHints().colorScheme() == QtCore.Qt.ColorScheme.Light:
                return GuiColorScheme.Light
        except Exception as ex:
            logging.exception(f'Getting color scheme failed, assuming default ({ex})')
        return GuiColorScheme.Default
    

    @staticmethod
    def set_gui_color_scheme(scheme: GuiColorScheme):
        try:
            if scheme == GuiColorScheme.Light:
                QtWidgets.QApplication.styleHints().setColorScheme(QtCore.Qt.ColorScheme.Light)
            elif scheme == GuiColorScheme.Dark:
                QtWidgets.QApplication.styleHints().setColorScheme(QtCore.Qt.ColorScheme.Dark)
        except Exception as ex:
            logging.exception(f'Setting color scheme failed, ignoring ({ex})')
