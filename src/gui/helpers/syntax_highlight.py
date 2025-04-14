from .qt_helper import QtHelper
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *



class PythonSyntaxHighlighter(QSyntaxHighlighter):

    def highlightBlock(self, text):
        # text is one line at a time
        
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

        if '#' in text:
            start = text.index('#')
            length = len(text) - start
            format(start, length, color='gray', italic=True)
