from ..helpers.qt_helper import QtHelper
from lib import AppPaths, PathExt, Parameters, SiValue, MainWindowLayout

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import pathlib
import enum
import logging
import os
import re
import numpy as np
import tokenize
from typing import Callable, Optional, Union



class PyEditor(QTextEdit):


    COLOR_BG = '#fff'
    COLOR_BG_INACTIVE = '#ddd'
    COLOR_TEXT = '#000'
    COLOR_TEXT_INACTIVE = '#222'
    COLOR_TEXT_COMMENT = '#585'


    class PythonSyntaxHighlighter(QSyntaxHighlighter):

        def highlightBlock(self, line: str):  # overloaded from QSyntaxHighlighter
            
            def format(start, length, *, color: str = None, bold: bool = False, italic: bool = False):
                nonlocal self
                format = QTextCharFormat()
                if color:
                    format.setForeground(QColor(color))
                if bold:
                    format.setFontWeight(QFont.Weight.Bold)
                if italic:
                    format.setFontItalic(True)
                self.setFormat(start, length, format)
            
            # try:
            #     _line_was_read = False
            #     def _readline() -> bytes:
            #         nonlocal _line_was_read
            #         if _line_was_read:
            #             return ''
            #         _line_was_read = True
            #         return line + '\n'
            #     for token in tokenize.generate_tokens(_readline):
            #         print(token)
            # except Exception as ex:
            #     return

            if '#' in line:
               start = line.index('#')
               length = len(line) - start
               format(start, length, color=PyEditor.COLOR_TEXT_COMMENT, italic=True)


    def __init__(self, parent = None):
        super().__init__(parent)
        
        self.document().setDefaultFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._ui_highlighter = PyEditor.PythonSyntaxHighlighter(self.document())
        self._inactive = False

        self._update_color_scheme()
    

    def inactive(self) -> bool:
        return self._inactive
    def setInactive(self, inactive: bool):
        self._inactive = inactive
        self._update_color_scheme()
    

    def _update_color_scheme(self):
        self.setStyleSheet(f'''
            color: {PyEditor.COLOR_TEXT_INACTIVE if self._inactive else PyEditor.COLOR_TEXT};
            background-color: {PyEditor.COLOR_BG_INACTIVE if self._inactive else PyEditor.COLOR_BG};
        ''')


    def keyPressEvent(self, event: QtGui.QKeyEvent|None):  # overloaded from QTextEdit
        super().keyPressEvent(event)
        
        HASH_KEY = Qt.Key.Key_Backslash  # works on my German keyboard, don't understand why
        if event.key()==HASH_KEY and event.modifiers()==QtCore.Qt.KeyboardModifier.ControlModifier:
            self._on_toggle_comment()


    def _on_toggle_comment(self):

        cursor = self.textCursor()

        def get_sel_range() -> tuple[int,int,int,int]:
            nonlocal cursor
            sel_start, sel_end = cursor.selectionStart(), cursor.selectionEnd()
            cursor.setPosition(sel_start)
            first_line = cursor.blockNumber()
            cursor.setPosition(sel_end)
            last_line = cursor.blockNumber()
            return first_line, last_line

        def set_text_and_selection(lines: list[str], first_line: int, last_line: int):
            nonlocal cursor
            
            text = '\n'.join(lines)
            self.setText(text)
            
            start_pos = sum(len(line)+1 for line in lines[:first_line])
            end_pos = sum(len(line)+1 for line in lines[:last_line+1])-1
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(cursor)


        def strip_start(s: str, chars: str = None) -> str:
            if chars:
                while s.startswith(chars):
                    s = s[len(chars):]
            else:  # strip whitespace
                m = re.match(r'^\s+', s)
                if m:
                    s = s[len(m.group()):]
            return s


        first_line, last_line = get_sel_range()
        n_lines = last_line - first_line + 1
        
        lines = self.toPlainText().splitlines()
        n_comments = len([i for i in range(first_line,last_line+1) if strip_start(lines[i]).startswith('#')])
        do_comment = n_comments < n_lines // 2
        for i in range(first_line,last_line+1):
            is_commented = strip_start(lines[i]).startswith('#')
            if do_comment:
                if not is_commented:  # make comment
                    lines[i] = '# ' + strip_start(lines[i])
            else:
                if is_commented:  # un-comment
                    lines[i] = strip_start(strip_start(strip_start(lines[i]), '#'))

        set_text_and_selection(lines, first_line, last_line)
