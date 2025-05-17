from __future__ import annotations

from .qt_helper import QtHelper
from .settings import Parameters
from lib import AppPaths, PathExt
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

        paramClicked = pyqtSignal(int, int)
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
            for ix in range(self.grid_size):
                for iy in range(self.grid_size):
                    x = self._x0 + ix*(self._cell_size+self._cell_spacing)
                    y = self._y0 + iy*(self._cell_size+self._cell_spacing)
                    rect = QRect(x, y, self._cell_size, self._cell_size)
                    if rect.contains(event.pos()):
                        self.paramClicked.emit(ix, iy)

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

            for ix in range(self.grid_size):
                for iy in range(self.grid_size):
                    x = x0 + ix*(cell_size+cell_spacing)
                    y = y0 + iy*(cell_size+cell_spacing)

                    if self._use_expressions:
                        if cell_size >= 8:
                            delta = 4
                        else:
                            delta = 2
                    else:
                        delta = 0
                    rect = QRect(x+delta//2, y+delta//2, cell_size-delta, cell_size-delta)

                    if self._use_expressions:
                        painter.setBrush(QColorConstants.Gray)
                        painter.setPen(Qt.PenStyle.NoPen)
                    elif self._data[ix,iy]:
                        painter.setBrush(QColorConstants.Black)
                        painter.setPen(Qt.PenStyle.NoPen)
                    else:
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.setPen(QColorConstants.Gray)

                    painter.drawRect(rect)

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

        self._ui_grid = ParamSelector.GraphicWidget(self)
        self._ui_grid.setContentsMargins(0, 0, 0, 0)
        self._ui_grid.data = np.full([1, 1], False, dtype=bool)
        self._ui_grid.paramClicked.connect(self._on_param_clicked)
        self._ui_grid.overflowClicked.connect(self._on_overflow_clicked)
        self._ui_sall_button = QtHelper.make_button(self, None, self._on_s_all, icon='toolbar_s-all.svg', tooltip='Show All Terms (e.g. S11, S21, S12, ...); Hold Ctrl to Toggle', toolbar=True)
        self._ui_sii_button = QtHelper.make_button(self, None, self._on_sii, icon='toolbar_sii.svg', tooltip='Show All Sii Terms (e.g. S11, S22, S33, ...); Hold Ctrl to Toggle', toolbar=True)
        self._ui_sij_button = QtHelper.make_button(self, None, self._on_sij, icon='toolbar_sij.svg', tooltip='Show All Sij Terms (e.g. S21, S12, S31, ...); Hold Ctrl to Toggle', toolbar=True)
        self._ui_s11_button = QtHelper.make_button(self, None, self._on_s11, icon='toolbar_s11.svg', tooltip='Show S11 Term; Hold Ctrl to Toggle', toolbar=True)
        self._ui_s22_button = QtHelper.make_button(self, None, self._on_s22, icon='toolbar_s22.svg', tooltip='Show S22 Term; Hold Ctrl to Toggle', toolbar=True)
        self._ui_s21_button = QtHelper.make_button(self, None, self._on_s21, icon='toolbar_s21.svg', tooltip='Show All Sij Terms With i>j (e.g. S21, S31, S32, ...); Hold Ctrl to Toggle', toolbar=True)
        self._ui_s12_button = QtHelper.make_button(self, None, self._on_s12, icon='toolbar_s12.svg', tooltip='Show All Sij Terms With i<j(e.g. S12, S13, S23, ...); Hold Ctrl to Toggle', toolbar=True)
        self._ui_expr_button = QtHelper.make_button(self, None, self._on_expr, icon='toolbar_s-expr.svg', tooltip='Use Expressions', toolbar=True, checked=False)
        self.setLayout(QtHelper.layout_h(
            QtHelper.layout_grid([
                [self._ui_sall_button, None, self._ui_expr_button],
                [self._ui_s12_button, self._ui_sij_button, self._ui_s21_button],
                [self._ui_s11_button, self._ui_sii_button, self._ui_s22_button],
            ], spacing=1),
            self._ui_grid,
            spacing=10
        ))
        self.setContentsMargins(0, 0, 0, 0)

        
    def gridSize(self) -> int:
        return self._ui_grid.grid_size
    def setGridSize(self, size: int):
        assert size >= 1
        current_size = self.gridSize()
        if current_size == self.size():
            return
        
        current_pattern = self.params()
        if current_pattern == Parameters.Custom:
            # try to extend/shrink the matrix
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
            self.setParamMask(new_params)
        else:  # just apply pattern
            self._ui_grid.data = np.ndarray([size,size], dtype=bool)
            self.setParams(current_pattern)

        self.paramsChanged.emit()

        
    def maxGridSize(self) -> int:
        return self._ui_grid.max_size
    def setMaxGridSize(self, value: int):
        self._ui_grid.max_size = value
    

    def params(self) -> Parameters:
        if self._ui_expr_button.isChecked():
            return Parameters.Expressions
        params = self.paramMask()
        
        if np.all(params):
            return Parameters.ComboAll
        if not np.any(params):
            return Parameters.Off

        result = Parameters.Off
        if np.all(params[self._mask_sii()]):
            result |= Parameters.Sii
        else:
            if np.all(params[self._mask_s11()]):
                result |= Parameters.S11
            if np.all(params[self._mask_s22()]):
                result |= Parameters.S22
        if np.all(params[self._mask_s21()]):
            result |= Parameters.S21
        if np.all(params[self._mask_s12()]):
            result |= Parameters.S12
        
        # is there any outlier to this pattern?
        result_params = self._mask_s_none()
        if result & Parameters.Sii:
            result_params |= self._mask_sii()
        else:
            if result & Parameters.S11:
                result_params |= self._mask_s11()
            if result & Parameters.S22:
                result_params |= self._mask_s22()
        if result & Parameters.S21:
            result_params |= self._mask_s21()
        if result & Parameters.S12:
            result_params |= self._mask_s12()
        if np.array_equal(result_params, self.paramMask()):
            return result
        else:
            return Parameters.Custom
    def setParams(self, value: Parameters):
        use_expressions = bool(Parameters.Expressions & value)
        self._ui_expr_button.setChecked(use_expressions)
        self._ui_grid.use_expressions = use_expressions

        params = np.full([self.gridSize(), self.gridSize()], False, dtype=bool)
        if Parameters.Sii & value:
            params[self._mask_sii()] = True
        elif Parameters.S11 & value:
            params[self._mask_s11()] = True
        elif Parameters.S22 & value:
            params[self._mask_s22()] = True
        if Parameters.S21 & value:
            params[self._mask_s21()] = True
        if Parameters.S12 & value:
            params[self._mask_s12()] = True
        self._ui_grid.data = params


    def useExpressions(self) -> bool:
        return self._ui_expr_button.isChecked()
    def setUseExpressions(self, value: bool):
        self._ui_expr_button.setChecked(value)


    def paramMask(self) -> np.ndarray:
        return self._ui_grid.data
    def setParamMask(self, value: np.ndarray):
        self._ui_expr_button.setChecked(False)
        self._ui_grid.use_expressions = False
        self._ui_grid.data = value
    

    def _mask_s_none(self) -> np.ndarray:
        return np.full([self.gridSize(), self.gridSize()], False, dtype=bool)


    def _mask_s_all(self) -> np.ndarray:
        mask = self._mask_s_none()
        for i in range(self.gridSize()):
            for j in range(self.gridSize()):
                mask[i,j] = True
        return mask


    def _mask_sii(self) -> np.ndarray:
        mask = self._mask_s_none()
        for i in range(self.gridSize()):
            mask[i,i] = True
        return mask


    def _mask_sij(self) -> np.ndarray:
        mask = self._mask_s_none()
        for i in range(self.gridSize()):
            for j in range(self.gridSize()):
                if i != j:
                    mask[i,j] = True
        return mask


    def _mask_s11(self) -> np.ndarray:
        mask = self._mask_s_none()
        mask[0,0] = True
        return mask


    def _mask_s22(self) -> np.ndarray:
        mask = self._mask_s_none()
        if self.gridSize() >= 2:
            mask[1,1] = True
        return mask


    def _mask_s21(self) -> np.ndarray:
        mask = self._mask_s_none()
        for i in range(self.gridSize()):
            for j in range(self.gridSize()):
                if i > j:
                    mask[i,j] = True
        return mask


    def _mask_s12(self) -> np.ndarray:
        mask = self._mask_s_none()
        for i in range(self.gridSize()):
            for j in range(self.gridSize()):
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
        self._apply_mask(self._mask_s_all())


    def _on_sii(self):
        self._apply_mask(self._mask_sii())

    
    def _on_sij(self):
        self._apply_mask(self._mask_sij())

    
    def _on_s11(self):
        self._apply_mask(self._mask_s11())

    
    def _on_s22(self):
        self._apply_mask(self._mask_s22())

    
    def _on_s21(self):
        self._apply_mask(self._mask_s21())

    
    def _on_s12(self):
        self._apply_mask(self._mask_s12())

    
    def _on_expr(self):
        self._ui_grid.use_expressions = self._ui_expr_button.isChecked()
        self.paramsChanged.emit()

    def _on_param_clicked(self, x: int, y: int):
        mask = self.paramMask()
        mask[x,y] = not mask[x,y]
        self.setParamMask(mask)
        self.paramsChanged.emit()

    def _on_overflow_clicked(self):
        pass  # TODO: show a dialog
