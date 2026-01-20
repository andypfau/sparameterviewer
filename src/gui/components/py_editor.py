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
import tokenize, token
from typing import Callable, Optional, Union



class PyEditor(QTextEdit):


    COLOR_BG = QColorConstants.White
    COLOR_BG_INACTIVE = QColorConstants.LightGray
    COLOR_TEXT = QColorConstants.Black
    COLOR_TEXT_INACTIVE = QColorConstants.DarkGray
    COLOR_TEXT_COMMENT = QColorConstants.Gray
    COLOR_TEXT_NUMBER = QColorConstants.DarkRed
    COLOR_TEXT_OPERATOR = QColorConstants.DarkCyan
    COLOR_TEXT_NAME = QColorConstants.DarkBlue
    COLOR_TEXT_STR = QColorConstants.Blue
    COLOR_TEXT_ERROR = QColorConstants.Red


    class PythonSyntaxHighlighter(QSyntaxHighlighter):

        def highlightBlock(self, line: str):  # overloaded from QSyntaxHighlighter
            
            def format(start, length, *, color: QColor|str = None, bold: bool = False, italic: bool = False, underline: bool = False):
                nonlocal self
                format = QTextCharFormat()
                if color:
                    format.setForeground(QColor(color))
                if bold:
                    format.setFontWeight(QFont.Weight.Bold)
                if italic:
                    format.setFontItalic(True)
                if underline:
                    format.setFontUnderline(True)
                self.setFormat(start, length, format)
            
            try:
                lines = list(line.splitlines())
                def readline() -> bytes:
                    nonlocal lines
                    if len(lines) < 1:
                        return ''
                    line, lines = lines[0], lines[1:]
                    return line + '\n'
                
                for t in tokenize.generate_tokens(readline):
                    start, end = t.start[1], t.end[1]
                    length = end - start
                    if t.type==token.COMMENT:
                        format(start, length, color=PyEditor.COLOR_TEXT_COMMENT, italic=True)
                    elif t.type==token.NAME:
                        format(start, length, color=PyEditor.COLOR_TEXT_NAME)
                    elif t.type==token.NUMBER:
                        format(start, length, color=PyEditor.COLOR_TEXT_NUMBER)
                    elif t.type==token.OP:
                        format(start, length, color=PyEditor.COLOR_TEXT_OPERATOR)
                    elif t.type==token.STRING:
                        format(start, length, color=PyEditor.COLOR_TEXT_STR)

            except Exception as ex:
                format(0, len(line), color=PyEditor.COLOR_TEXT_ERROR)


    def __init__(self, parent = None):
        super().__init__(parent)
        
        self.document().setDefaultFont(QtHelper.make_font(family=QtHelper.get_monospace_font()))
        self.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._ui_highlighter = PyEditor.PythonSyntaxHighlighter(self.document())
        self._inactive = False

        self.setAcceptRichText(False)  # this control takes care of syntax highlighting, so only accept unformatted text

        self._update_color_scheme()
    

    def inactive(self) -> bool:
        return self._inactive
    def setInactive(self, inactive: bool):
        self._inactive = inactive
        self._update_color_scheme()
    

    def _update_color_scheme(self):
        self.setStyleSheet(f'''
            QTextEdit {{
                color: {PyEditor.COLOR_TEXT_INACTIVE.name() if self._inactive else PyEditor.COLOR_TEXT.name()};
                background-color: {PyEditor.COLOR_BG_INACTIVE.name() if self._inactive else PyEditor.COLOR_BG.name()};
            }}
        ''')


    def keyPressEvent(self, event: QtGui.QKeyEvent|None):  # overloaded from QTextEdit
        
        # CTR+# is reported as CTRL+\ works on German keyboard layout, don't understand why
        if event.key() in (Qt.Key.Key_Backslash,Qt.Key.Key_NumberSign) and event.modifiers()==QtCore.Qt.KeyboardModifier.ControlModifier:
            self._on_toggle_comment()
        
        super().keyPressEvent(event)


    def _on_toggle_comment(self):

        def strip_start(s: str, chars: str = None) -> str:
            if chars:
                while s.startswith(chars):
                    s = s[len(chars):]
            else:  # strip whitespace
                m = re.match(r'^\s+', s)
                if m:
                    s = s[len(m.group()):]
            return s

        def toggle_comments(s: str) -> str:
            lines = s.splitlines()
            n_comments = len([line for line in lines if strip_start(line).startswith('#')])
            do_comment = n_comments < len(lines) / 2.0
            for i,line in enumerate(lines):
                is_commented = strip_start(line).startswith('#')
                if do_comment:
                    if not is_commented:  # make comment
                        lines[i] = '# ' + strip_start(line)
                else:
                    if is_commented:  # un-comment
                        lines[i] = strip_start(strip_start(strip_start(line), '#'))
            return '\n'.join(lines)

        cursor = self.textCursor()
        cursor.beginEditBlock()  # ensures undo-history is preserved

        # select whole lines
        sel_start, sel_end = cursor.selectionStart(), cursor.selectionEnd()
        cursor.setPosition(sel_start)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
        block_start = cursor.selectionStart()
        cursor.setPosition(sel_end, QTextCursor.MoveMode.KeepAnchor)
        cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)

        sel_text = cursor.selectedText()
        new_sel_text = toggle_comments(sel_text)
        
        cursor.removeSelectedText()
        cursor.insertText(new_sel_text)

        # select new whole lines
        cursor.setPosition(block_start)
        cursor.setPosition(block_start + len(new_sel_text), QTextCursor.MoveMode.KeepAnchor)

        cursor.endEditBlock()  # ensures undo-history is preserved
        self.setTextCursor(cursor)
