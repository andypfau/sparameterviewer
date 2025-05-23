from __future__ import annotations

from ..helpers.qt_helper import QtHelper
from lib import AppPaths, PathExt, Parameters, get_callstack_str
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
import dataclasses
from typing import Callable, Optional, Union



class ParamSelector(QWidget):


    paramsChanged = pyqtSignal()


    class Simplified(enum.StrEnum):
        All = 'All Parameters'
        SiiS21 = 'All Parameters (Forward)'
        Sij = 'Insertion Loss'
        S21 = 'Insertion Loss (Forward)'
        S12 = 'Insertion Loss (Reverse)'
        Sii = 'Return Loss'
        S11 = 'S11'
        S22 = 'S22'
        Expressions = 'Expression-Based'


    class DefocusScrollArea(QScrollArea):

        focusLost = pyqtSignal()

        def focusOutEvent(self, event: QFocusEvent):
            self.focusLost.emit()


    class GraphicWidget(QWidget):

        paramClicked = pyqtSignal(int, int, QtCore.Qt.KeyboardModifier)
        overflowClicked = pyqtSignal()

        @dataclasses.dataclass
        class Geometry:
            x0: float
            y0: float
            cell_size: float
            cell_border: float
            all_cells_size: float
            total_size: float
            overflow: bool

        def __init__(self, parent = ...):
            super().__init__(parent)
            self._data = np.array([[False, False, True], [False, True, True], [True, True, True]], dtype=bool)
            self._scale_widget_to_contents = False
            self._current_geometry: ParamSelector.GraphicWidget.Geometry|None = None
            self._target_size = 64
            self.setContentsMargins(0, 0, 0, 0)
            self._adjust_widget_size()
        
        def get_geometry(self) -> ParamSelector.GraphicWidget.Geometry:
            if self._current_geometry is None:
                self._current_geometry = self._calculate_geometry()
            return self._current_geometry
    
        def _calculate_geometry(self) -> ParamSelector.GraphicWidget.Geometry:
            #logging.debug(f'_calculate_geometry()')
            grid_size = self.matrix_dimensions
            MINIMUM_CELL_SIZE, DEFAULT_CELL_SIZE, LARGE_CELL_SIZE, MAXIMUM_CELL_SIZE = 14, 22, 32, 32
            WIDGET_BORDER, CELL_BORDER = 1, 1
            
            if self._scale_widget_to_contents:  # widget size is adjusted, use fixed cell size
                cell_size = DEFAULT_CELL_SIZE if self.matrix_dimensions<10 else LARGE_CELL_SIZE  # for a large matrix, the text is longer
                all_cells_size = grid_size * cell_size
                total_size = 2*WIDGET_BORDER + all_cells_size
                x0, y0 = WIDGET_BORDER, WIDGET_BORDER
                return ParamSelector.GraphicWidget.Geometry(x0, y0, cell_size, CELL_BORDER, all_cells_size, total_size, overflow=False)
            
            else:  # widget is fixed size, adjust cell size
                cell_size = (self._target_size - 2*WIDGET_BORDER) / grid_size
                cell_border = CELL_BORDER
                if cell_size > MAXIMUM_CELL_SIZE:
                    cell_size = MAXIMUM_CELL_SIZE
                all_cells_size = grid_size * cell_size
                total_size = 2*WIDGET_BORDER + all_cells_size
                x0, y0 = WIDGET_BORDER + (self._target_size- total_size) / 2, WIDGET_BORDER + (self._target_size - total_size) / 2
                overflow = cell_size < MINIMUM_CELL_SIZE
                if overflow:
                    cell_border = 0
                return ParamSelector.GraphicWidget.Geometry(x0, y0, cell_size, cell_border, all_cells_size, total_size, overflow)
        
        def _adjust_widget_size(self):
            #logging.debug(f'_adjust_widget_size()')
            self._current_geometry = None  # invalidate
            if self._scale_widget_to_contents:  # adjust widget size to required size
                geometry = self._calculate_geometry()  # use fixed geometry
                self.resize(geometry.total_size, geometry.total_size)
            else:  # fixed widget size (contents will be scaled)
                self.resize(self._target_size, self._target_size)
        
        def resizeEvent(self, event: QResizeEvent|None):
            self._current_geometry = None  # invalidate
    
        def mouseReleaseEvent(self, event: QMouseEvent|None):
            super().mouseReleaseEvent(event)
            if not event or event.button() != Qt.MouseButton.LeftButton:
                return  # no mouse click -> ignore
            geometry = self.get_geometry()

            if geometry.overflow:
                self.overflowClicked.emit()
                return
            
            keys = QApplication.keyboardModifiers()
            grid_size, x0, y0, cell_size = self.matrix_dimensions, geometry.x0, geometry.y0, geometry.cell_size
            for i in range(grid_size):
                for j in range(grid_size):
                    rect = QRectF(x0+j*cell_size, y0+i*cell_size, cell_size, cell_size)
                    if rect.contains(QPointF(event.pos())):
                        self.paramClicked.emit(i, j, keys)

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            default_font = painter.font()
            small_font = QtHelper.make_font(base=default_font, rel_size=0.75)

            geometry = self.get_geometry()
            grid_size, x0, y0, cell_size, cell_border, all_cells_size, overflow = \
                self.matrix_dimensions, geometry.x0, geometry.y0, geometry.cell_size, geometry.cell_border, geometry.all_cells_size, geometry.overflow
            always_use_comma = self.matrix_dimensions >= 10

            palette = QPalette()
            color_base = palette.color(QPalette.ColorRole.Base)
            color_dark = palette.color(QPalette.ColorRole.Dark)
            color_light = palette.color(QPalette.ColorRole.Light)
            color_text = palette.color(QPalette.ColorRole.Text)
            color_hl = palette.color(QPalette.ColorRole.Highlight)
            color_hl_text = palette.color(QPalette.ColorRole.HighlightedText)
            
            MIN_CELL_SIZE_FOR_RENDERING = 2.5
            if overflow and cell_size < MIN_CELL_SIZE_FOR_RENDERING:
                # too many elements -> just draw one large rectangle as a placeholder
                rect = QRectF(x0, y0, all_cells_size, all_cells_size)
                painter.setBrush(color_hl)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(rect)
                return

            MIN_CELL_SIZE_FOR_LARGE_FONT = 18
            always_use_small_font = cell_size < MIN_CELL_SIZE_FOR_LARGE_FONT

            for i in range(grid_size):
                for j in range(grid_size):
                    rect = QRectF(x0+j*cell_size+cell_border, y0+i*cell_size+cell_border, cell_size-2*cell_border, cell_size-2*cell_border)
                    
                    enabled = self._data[i,j]
                    if enabled:
                        painter.setBrush(color_hl)
                        painter.setPen(Qt.PenStyle.NoPen)
                    else:
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        if overflow:
                            painter.setPen(color_dark)
                        else:
                            painter.setPen(Qt.PenStyle.NoPen)
                        
                    if overflow:
                        painter.drawEllipse(rect)
                    else:
                        painter.drawRoundedRect(rect, 2, 2)

                    if not overflow:
                        if enabled:
                            painter.setPen(color_hl_text)
                        else:
                            painter.setPen(color_text)
                        
                        ep, ip = i+1, j+1
                        is_long_text = ep>=10 or ip>=10
                        
                        if is_long_text or always_use_comma:
                            text = f'{ep},{ip}'
                        else:
                            text = f'{ep}{ip}'
                        if is_long_text or always_use_small_font:
                            painter.setFont(small_font)
                        else:
                            painter.setFont(default_font)
                        
                        painter.drawText(rect, QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter, text)

            painter.end()
    
        @property
        def data(self) -> np.ndarray:
            return self._data.copy()
        @data.setter
        def data(self, value: np.ndarray):
            size_changed = value.shape != self._data.shape
            if (not size_changed) and np.array_equal(value, self._data):
                return
            #logging.debug(f'Setting size to {value.shape}')
            self._data = value
            if size_changed:
                self._adjust_widget_size()
            self.repaint()
    
        @property
        def target_size(self) -> int:
            return self._target_size
        @target_size.setter
        def target_size(self, value: int):
            if self._target_size == value:
                return
            self._target_size = value
            self._adjust_widget_size()
    
        @property
        def scale_widget_to_contents(self) -> bool:
            return self._scale_widget_to_contents
        @scale_widget_to_contents.setter
        def scale_widget_to_contents(self, value: bool):
            if self._scale_widget_to_contents == value:
                return
            self._scale_widget_to_contents = value
            self._adjust_widget_size()
        
        @property
        def matrix_dimensions(self) -> int:
            return self._data.shape[0]


    def __init__(self, parent = ...):
        super().__init__(parent)

        INITIAL_SIZE = 64
        
        self._largest_data = np.ndarray([0,0], dtype=bool)
        self._simplified = False
        self._ignore_simple_change = False
        self._allow_expressions = False
        self._use_expressions = False

        self._ui_simple = QWidget()
        self._ui_simple.setVisible(self._simplified)
        self._ui_simple_params_combo = QComboBox()
        self._ui_simple_params_combo.setStyleSheet('QComboBox QAbstractItemView { min-width: 40ex; }')
        self._ui_simple_params_combo.currentIndexChanged.connect(self._on_simple_params_changed)
        self._ui_simple.setLayout(QtHelper.layout_v(
            ...,
            self._ui_simple_params_combo,
            ..., spacing=10
        ))

        self._ui_advanced = QWidget()
        self._ui_advanced.setVisible(not self._simplified)

        self._ui_grid = ParamSelector.GraphicWidget(self)
        self._ui_grid.setContentsMargins(0, 0, 0, 0)
        self._ui_grid.setToolTip('Click a parameter to show it; hold Ctrl to toggle, hold Shift to apply to whole diagonal/triangular')
        self._ui_grid.data = np.full([2, 2], False, dtype=bool)
        self._ui_grid.paramClicked.connect(self._on_param_clicked)
        self._ui_grid.overflowClicked.connect(self._on_overflow_clicked)
        self._ui_grid.target_size = INITIAL_SIZE
        self._ui_grid_scoll = ParamSelector.DefocusScrollArea()
        self._ui_grid_scoll.setWidget(self._ui_grid)
        self._ui_grid_scoll.setMinimumSize(INITIAL_SIZE, INITIAL_SIZE)
        self._ui_grid_scoll.focusLost.connect(self._on_defocus_scrollable_grid)
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
            self._ui_grid_scoll,
            spacing=10
        ))
        self.setContentsMargins(0, 0, 0, 0)
        self._ui_simple.setContentsMargins(0, 0, 0, 0)
        self._ui_advanced.setContentsMargins(0, 0, 0, 0)
        self.setLayout(QtHelper.layout_v(self._ui_simple, self._ui_advanced))
        
        self._update_simple_params_combo_elements()


    def autoScaleGridToContents(self) -> bool:
        return self._ui_grid.scale_widget_to_contents
    def setAutoScaleGridToContents(self, auto_scale: bool):
        #logging.debug(get_callstack_str())
        if self._ui_grid.scale_widget_to_contents == auto_scale:
            return
        if auto_scale:
            #logging.debug(f'Changing to auto size')
            self._ui_grid_scoll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self._ui_grid_scoll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self._ui_grid.scale_widget_to_contents = True
        else:
            #logging.debug(f'Changing to fixed size')
            self._ui_grid.scale_widget_to_contents = False
            self._ui_grid_scoll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self._ui_grid_scoll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._ui_grid_scoll.adjustSize()
    
    
    def gridSize(self) -> int:
        return self._ui_grid_scoll.minimumWidth()
    def setGridSize(self, size: int):
        self._ui_grid_scoll.setMinimumSize(size, size)
        self._ui_grid.target_size = size


    def allowExpressions(self) -> bool:
        return self._allow_expressions
    def setAllowExpressions(self, value: bool):
        if self._allow_expressions == value:
            return
        self._update_simple_params_combo_elements()
        self._allow_expressions = value
        self._ui_expr_button.setVisible(self._allow_expressions)
        if not self._allow_expressions:
            if self._use_expressions:
                self.setParams(Parameters.ComboAll)


    def simplified(self) -> bool:
        return self._simplified
    def setSimplified(self, value: bool):
        self._simplified = value
        self._ui_simple.setVisible(self._simplified)
        self._ui_advanced.setVisible(not self._simplified)

        
    def matrixDimensions(self) -> int:
        return self._ui_grid.matrix_dimensions
    def setMatrixDimensions(self, dim: int):
        assert dim >= 1
        current_dim = self.matrixDimensions()
        if dim == current_dim:
            return
        
        self.setAutoScaleGridToContents(False)

        current_pattern = self.params()

        if current_pattern == Parameters.Custom:  # try to extend/shrink the matrix
            current_params = self.paramMask()
            new_params = np.full([dim, dim], False, dtype=bool)
            if dim > current_dim:  # expand
                for i in range(min(new_params.shape[0],self._largest_data.shape[0])):
                    for j in range(min(new_params.shape[1],self._largest_data.shape[1])):
                        new_params[i,j] = self._largest_data[i,j]
                for i in range(current_dim):
                    for j in range(current_dim):
                        new_params[i,j] = current_params[i,j]
            else:  # shrink or equal
                if current_params.shape[0] >= self._largest_data.shape[0]:
                    self._largest_data = current_params
                for i in range(dim):
                    for j in range(dim):
                        new_params[i,j] = current_params[i,j]
            self._ui_grid.data = new_params
            self._update_simple_params_from_params(self._guess_params_from_data(new_params))
        
        else:  # just re-apply the current pattern to a new matrix
            guessed_pattern = self._guess_params_from_data(self.paramMask())
            self._ui_grid.data = self._make_mask(guessed_pattern, dim)
            self._update_simple_params_from_params(guessed_pattern)

        self.paramsChanged.emit()


    def _on_defocus_scrollable_grid(self):
        self.setAutoScaleGridToContents(False)

    
    def _guess_params_from_data(self, params: np.ndarray) -> Parameters:
        #logging.debug(get_callstack_str())

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
            #logging.debug('_guess_params_from_data() done.')
            return result
        else:
            #logging.debug('_guess_params_from_data() done.')
            return Parameters.Custom
    

    def params(self) -> Parameters:
        return self._guess_params_from_data(self.paramMask())
    def setParams(self, value: Parameters):
        self._ui_grid.data = self._make_mask(value)
        self._update_simple_params_from_params(value)
    

    def useExpressions(self) -> bool:
        return self._use_expressions
    def setUseExpressions(self, value: bool):
        if not self._allow_expressions:
            return
        self._use_expressions = value
        self._ui_expr_button.setChecked(value)


    def paramMask(self) -> np.ndarray:
        return self._ui_grid.data
    def setParamMask(self, value: np.ndarray):
        self._ui_grid.data = value
        self._update_simple_params_from_params(self._guess_params_from_data(value))
    

    def _make_mask(self, params: Parameters = Parameters.Off, dim: int|None = None) -> np.ndarray:
        dim = dim or self.matrixDimensions()
        mask = np.full([dim, dim], False, dtype=bool)
        if params & Parameters.S11 and dim >= 1:
            mask[0,0] = True
        if params & Parameters.S22 and dim >= 2:
            mask[1,1] = True
        if params & Parameters.Sii:
            for i in range(dim):
                mask[i,i] = True
        if params & Parameters.S21:
            for i in range(dim):
                for j in range(dim):
                    if i > j:
                        mask[i,j] = True
        if params & Parameters.S12:
            for i in range(dim):
                for j in range(dim):
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
        self._ui_grid.data = params
        self._update_simple_params_from_params(self._guess_params_from_data(params))
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
        self._use_expressions = self._ui_expr_button.isChecked()
        self.paramsChanged.emit()


    def _on_param_clicked(self, x: int, y: int, keys: QtCore.Qt.KeyboardModifier):
        toggle = keys & QtCore.Qt.KeyboardModifier.ControlModifier
        apply_to_whole_range = keys & QtCore.Qt.KeyboardModifier.ShiftModifier
        
        if toggle:
            mask = self.paramMask()
            new_value = not mask[x,y]
        else:
            mask = self._make_mask()
            new_value = True
        
        if apply_to_whole_range:
            dim = self.matrixDimensions()
            for i in range(dim):
                for j in range(dim):
                    if x==y and i==j:
                        mask[i, j] = new_value
                    elif x<y and i<j:
                        mask[i, j] = new_value
                    elif x>y and i>j:
                        mask[i, j] = new_value
        else:
            mask[x,y] = new_value
        
        self.setParamMask(mask)
        self.paramsChanged.emit()


    def _on_overflow_clicked(self):
        self.setAutoScaleGridToContents(True)
    

    def _update_simple_params_combo_elements(self):
        self._ui_simple_params_combo.currentIndexChanged.disconnect(self._on_simple_params_changed)
        self._ui_simple_params_combo.clear()
        for option in ParamSelector.Simplified:
            if (option == ParamSelector.Simplified.Expressions) and (not self._allow_expressions):
                continue
            self._ui_simple_params_combo.addItem(str(option))
        self._ui_simple_params_combo.currentIndexChanged.connect(self._on_simple_params_changed)
        self._update_simple_params_from_params(self.params())
    

    def _update_simple_params_from_params(self, params: Parameters):
        try:
            self._ignore_simple_change = True
            match params:
                case Parameters.ComboSii21:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.SiiS21))
                case Parameters.ComboSij:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.Sij))
                case Parameters.Sii:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.Sii))
                case Parameters.S12:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.S12))
                case Parameters.S21:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.S21))
                case Parameters.S11:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.S11))
                case Parameters.S22:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.S22))
                case _:
                    self._ui_simple_params_combo.setCurrentText(str(ParamSelector.Simplified.All))  # fallback
        finally:
            self._ignore_simple_change = False
    

    def _on_simple_params_changed(self):
        if not self._simplified or self._ignore_simple_change:
            return
        
        match self._ui_simple_params_combo.currentText():
            case str(ParamSelector.Simplified.All):
                self.setParamMask(self._make_mask(Parameters.ComboAll))
            case str(ParamSelector.Simplified.SiiS21):
                self.setParamMask(self._make_mask(Parameters.Sii|Parameters.S21))
            case str(ParamSelector.Simplified.Sij):
                self.setParamMask(self._make_mask(Parameters.ComboSij))
            case str(ParamSelector.Simplified.S21):
                self.setParamMask(self._make_mask(Parameters.S21))
            case str(ParamSelector.Simplified.S12):
                self.setParamMask(self._make_mask(Parameters.S12))
            case str(ParamSelector.Simplified.Sii):
                self.setParamMask(self._make_mask(Parameters.Sii))
            case str(ParamSelector.Simplified.S11):
                self.setParamMask(self._make_mask(Parameters.S11))
            case str(ParamSelector.Simplified.S22):
                self.setParamMask(self._make_mask(Parameters.S22))
            case _:
                return
        
        self.paramsChanged.emit()
