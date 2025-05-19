from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths, PathExt, Parameters
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import pathlib
import enum
import logging
import os
import math
import numpy as np
import enum
from typing import Callable, Optional, Union



class ParamSelector(QWidget):


    paramsChanged = pyqtSignal()


    class GraphicWidget(QWidget):

        paramClicked = pyqtSignal(int, int, QtCore.Qt.KeyboardModifier)
        overflowClicked = pyqtSignal()

        def __init__(self, parent = ...):
            super().__init__(parent)
            self._data = np.array([[False, False, True], [False, True, True], [True, True, True]], dtype=bool)
            self._use_expressions = False
            self._overflow = False
            self._max_size = 4
            self._x0, self._y0, self._cell_size, self._cell_spacing = 0, 0, 1, 1
            self.setContentsMargins(0, 0, 0, 0)
            self.setMinimumSize(QSize(64,64))
    
        def mouseReleaseEvent(self, event: QMouseEvent|None):
            super().mouseReleaseEvent(event)
            if not event or event.button() != Qt.MouseButton.LeftButton:
                return
            if self._overflow:
                self.overflowClicked.emit()
                return
            keys = QApplication.keyboardModifiers()
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    x = self._x0 + j*(self._cell_size+self._cell_spacing)
                    y = self._y0 + i*(self._cell_size+self._cell_spacing)
                    rect = QRect(x, y, self._cell_size, self._cell_size)
                    if rect.contains(event.pos()):
                        self.paramClicked.emit(i, j, keys)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            cell_spacing = 3
            border = 1

            short_side = min(self.width(), self.height())
            cell_size = math.floor((short_side - 2*border - ((self.grid_size - 1) * cell_spacing)) / self.grid_size)
            total_size = 2*border + (self.grid_size - 1) * cell_spacing + self.grid_size * cell_size
            x0, y0 = border + (self.width() - total_size) // 2, border + (self.height() - total_size) // 2

            self._x0, self._y0, self._cell_size, self._cell_spacing = x0, y0, cell_size, cell_spacing
            self._overflow = self.grid_size > self._max_size
            if self._overflow:
                painter.setPen(QColorConstants.Gray)
                painter.drawLine(x0, y0, x0+total_size, y0+total_size)
                painter.drawLine(x0+total_size, y0, x0, y0+total_size)
                return

            if self._use_expressions:
                if cell_size >= 8:
                    delta = 4
                else:
                    delta = 2
            else:
                delta = 0
            final_cell_size = cell_size - delta
            show_text = (self.grid_size <= 9) and (final_cell_size >= 12)

            palette = QPalette()
            color_base = palette.color(QPalette.ColorRole.Base)
            color_dark = palette.color(QPalette.ColorRole.Dark)
            color_light = palette.color(QPalette.ColorRole.Light)
            color_text = palette.color(QPalette.ColorRole.Text)
            color_hl = palette.color(QPalette.ColorRole.Highlight)
            color_hl_text = palette.color(QPalette.ColorRole.HighlightedText)
            
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    x = x0 + j*(cell_size+cell_spacing)
                    y = y0 + i*(cell_size+cell_spacing)

                    rect = QRect(x+delta//2, y+delta//2, final_cell_size, final_cell_size)
                    
                    if self._use_expressions:
                        painter.setBrush(color_dark)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.drawRect(rect)
                    
                    else:
                        enabled = self._data[i,j]
                        if enabled:
                            painter.setBrush(color_hl)
                            painter.setPen(Qt.PenStyle.NoPen)
                        else:
                            painter.setBrush(Qt.BrushStyle.NoBrush)
                            painter.setPen(Qt.PenStyle.NoPen)
                            
                        painter.drawRect(rect)

                        if show_text:
                            if enabled:
                                painter.setPen(color_hl_text)
                            else:
                                painter.setPen(color_dark)
                            painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter, f'{i+1}{j+1}')

            painter.end()
    
        @property
        def data(self) -> np.ndarray:
            return self._data.copy()
        @data.setter
        def data(self, value: np.ndarray):
            if value.shape == self._data.shape:
                if np.array_equal(value, self._data):
                    return
            self._data = value
            self.repaint()
    
        @property
        def use_expressions(self) -> bool:
            return self._use_expressions
        @use_expressions.setter
        def use_expressions(self, value: bool):
            if self._use_expressions == value:
                return
            self._use_expressions = value
            self.repaint()
    
        @property
        def max_size(self) -> int:
            return self._max_size
        @max_size.setter
        def max_size(self, value: int):
            if self._max_size == value:
                return
            self._max_size = value
            self.repaint()
        
        @property
        def grid_size(self) -> int:
            return self._data.shape[0]


    def __init__(self, parent = ...):
        super().__init__(parent)
        
        self._largest_data = np.ndarray([0,0], dtype=bool)
        self._simplified = False
        
        self._ui_simple = QWidget()
        self._ui_simple.setVisible(self._simplified)
        # TODO: implement simplified UI
        self._ui_simple.setLayout(QtHelper.layout_v('Simplified plot selector comes here...'))

        self._ui_advanced = QWidget()
        self._ui_advanced.setVisible(not self._simplified)

        self._ui_grid = ParamSelector.GraphicWidget(self)
        self._ui_grid.setContentsMargins(0, 0, 0, 0)
        self._ui_grid.setToolTip('Click a parameter to show it; hold Ctrl to toggle')
        self._ui_grid.data = np.full([2, 2], False, dtype=bool)
        self._ui_grid.paramClicked.connect(self._on_param_clicked)
        self._ui_grid.overflowClicked.connect(self._on_overflow_clicked)
        self._ui_sall_button = QtHelper.make_button(self, None, self._on_s_all, icon='toolbar_s-all.svg', tooltip='Show all terms (e.g. S11, S21, S12, ...); hold ctrl to toggle', toolbar=True)
        self._ui_sii_button = QtHelper.make_button(self, None, self._on_sii, icon='toolbar_sii.svg', tooltip='Show all Sii terms (e.g. S11, S22, S33, ...); hold ctrl to toggle', toolbar=True)
        self._ui_sij_button = QtHelper.make_button(self, None, self._on_sij, icon='toolbar_sij.svg', tooltip='Show all Sij terms (e.g. S21, S12, S31, ...); hold ctrl to toggle', toolbar=True)
        self._ui_s11_button = QtHelper.make_button(self, None, self._on_s11, icon='toolbar_s11.svg', tooltip='Show S11 term; hold Ctrl to toggle', toolbar=True)
        self._ui_s22_button = QtHelper.make_button(self, None, self._on_s22, icon='toolbar_s22.svg', tooltip='Show S22 term; hold Ctrl to toggle', toolbar=True)
        self._ui_s21_button = QtHelper.make_button(self, None, self._on_s21, icon='toolbar_s21.svg', tooltip='Show all Sij terms with i>j (e.g. S21, S31, S32, ...); hold ctrl to toggle', toolbar=True)
        self._ui_s12_button = QtHelper.make_button(self, None, self._on_s12, icon='toolbar_s12.svg', tooltip='Show all Sij terms with i<j(e.g. S12, S13, S23, ...); hold ctrl to toggle', toolbar=True)
        self._ui_expr_button = QtHelper.make_button(self, None, self._on_expr, icon='toolbar_s-expr.svg', tooltip='Use expressions for plotting', toolbar=True, checked=False)
        self._ui_advanced.setLayout(QtHelper.layout_h(
            QtHelper.layout_grid([
                [self._ui_sall_button, None, self._ui_expr_button],
                [self._ui_s12_button, self._ui_sij_button, self._ui_s21_button],
                [self._ui_s11_button, self._ui_sii_button, self._ui_s22_button],
            ], spacing=1),
            self._ui_grid,
            spacing=10
        ))
        self.setContentsMargins(0, 0, 0, 0)
        self._ui_simple.setContentsMargins(0, 0, 0, 0)
        self._ui_advanced.setContentsMargins(0, 0, 0, 0)
        self.setLayout(QtHelper.layout_v(self._ui_simple, self._ui_advanced))
    

    def simplified(self) -> bool:
        return self._simplified
    def setSimplified(self, value: bool):
        self._simplified = value
        self._ui_simple.setVisible(self._simplified)
        self._ui_advanced.setVisible(not self._simplified)

        
    def gridSize(self) -> int:
        return self._ui_grid.grid_size
    def setGridSize(self, size: int):
        assert size >= 1
        current_size = self.gridSize()
        if size == current_size:
            return
        
        current_pattern = self.params()

        if current_pattern == Parameters.Custom:  # try to extend/shrink the matrix
            current_params = self.paramMask()
            new_params = np.full([size, size], False, dtype=bool)
            if size > current_size:  # expand
                for i in range(min(new_params.shape[0],self._largest_data.shape[0])):
                    for j in range(min(new_params.shape[1],self._largest_data.shape[1])):
                        new_params[i,j] = self._largest_data[i,j]
                for i in range(current_size):
                    for j in range(current_size):
                        new_params[i,j] = current_params[i,j]
            else:  # shrink or equal
                if current_params.shape[0] >= self._largest_data.shape[0]:
                    self._largest_data = current_params
                for i in range(size):
                    for j in range(size):
                        new_params[i,j] = current_params[i,j]
            self._ui_grid.data = new_params
        
        else:  # just re-apply the current pattern to a new matrix
            guessed_pattern = self._guess_params_from_data(self.paramMask())
            self._ui_grid.data = self._make_mask(guessed_pattern, size)

        self.paramsChanged.emit()

        
    def maxGridSize(self) -> int:
        return self._ui_grid.max_size
    def setMaxGridSize(self, value: int):
        self._ui_grid.max_size = value

    
    def _guess_params_from_data(self, params: np.ndarray) -> Parameters:
        if np.all(params):
            return Parameters.ComboAll
        if not np.any(params):
            return Parameters.Off

        result = Parameters.Off
        if np.all(params[self._make_mask(Parameters.Sii)]):
            result |= Parameters.Sii
        else:
            if np.all(params[self._make_mask(Parameters.S11)]):
                result |= Parameters.S11
            if np.all(params[self._make_mask(Parameters.S22)]):
                result |= Parameters.S22
        if np.all(params[self._make_mask(Parameters.S21)]):
            result |= Parameters.S21
        if np.all(params[self._make_mask(Parameters.S12)]):
            result |= Parameters.S12
        
        # is there any outlier to this pattern?
        result_params = self._make_mask(result)
        if np.array_equal(result_params, self.paramMask()):
            return result
        else:
            return Parameters.Custom
    

    def params(self) -> Parameters:
        if self._ui_grid.use_expressions:
            return Parameters.Expressions
        return self._guess_params_from_data(self.paramMask())
    def setParams(self, value: Parameters):
        if value == Parameters.Expressions:
            self._ui_grid.use_expressions = True
            self._ui_expr_button.setChecked(True)
            return
        
        self._ui_expr_button.setChecked(False)
        self._ui_grid.data = self._make_mask(value)


    def paramMask(self) -> np.ndarray:
        return self._ui_grid.data
    def setParamMask(self, value: np.ndarray):
        self._ui_expr_button.setChecked(False)
        self._ui_grid.use_expressions = False
        self._ui_grid.data = value
    

    def _make_mask(self, params: Parameters = Parameters.Off, size: int|None = None) -> np.ndarray:
        size = size or self.gridSize()
        mask = np.full([size, size], False, dtype=bool)
        if params & Parameters.S11 and size >= 1:
            mask[0,0] = True
        if params & Parameters.S22 and size >= 2:
            mask[1,1] = True
        if params & Parameters.Sii:
            for i in range(size):
                mask[i,i] = True
        if params & Parameters.S21:
            for i in range(size):
                for j in range(size):
                    if i > j:
                        mask[i,j] = True
        if params & Parameters.S12:
            for i in range(size):
                for j in range(size):
                    if i < j:
                        mask[i,j] = True
        return mask

    
    def _apply_mask(self, mask: np.ndarray):
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl is held -> toggle
            params = self.paramMask()
            n_in_mask = np.count_nonzero(mask)
            n_currently_on = np.count_nonzero(params[mask])
            majority_is_currently_on = n_currently_on >= n_in_mask / 2
            if majority_is_currently_on:
                params[mask] = False
            else:
                params[mask] = True
        else:
            # only set these
            params = mask
        self._ui_expr_button.setChecked(False)
        self._ui_grid.use_expressions = False
        self._ui_grid.data = params
        self.paramsChanged.emit()

    
    def _on_s_all(self):
        self._apply_mask(self._make_mask(Parameters.ComboAll))


    def _on_sii(self):
        self._apply_mask(self._make_mask(Parameters.Sii))

    
    def _on_sij(self):
        self._apply_mask(self._make_mask(Parameters.ComboSij))

    
    def _on_s11(self):
        self._apply_mask(self._make_mask(Parameters.S11))

    
    def _on_s22(self):
        self._apply_mask(self._make_mask(Parameters.S22))

    
    def _on_s21(self):
        self._apply_mask(self._make_mask(Parameters.S21))

    
    def _on_s12(self):
        self._apply_mask(self._make_mask(Parameters.S12))

    
    def _on_expr(self):
        self._ui_grid.use_expressions = self._ui_expr_button.isChecked()
        self.paramsChanged.emit()


    def _on_param_clicked(self, x: int, y: int, keys: QtCore.Qt.KeyboardModifier):
        if keys & QtCore.Qt.KeyboardModifier.ControlModifier:
            # Ctrl is held -> toggle this
            mask = self.paramMask()
            mask[x,y] = not mask[x,y]
        else:
            # set this, un-set all others
            mask = self._make_mask()
            mask[x,y] = True
        self.setParamMask(mask)
        self.paramsChanged.emit()


    def _on_overflow_clicked(self):
        pass  # TODO: show a dialog
