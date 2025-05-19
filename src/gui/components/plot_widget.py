from __future__ import annotations

from lib import Settings

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

import matplotlib.pyplot
import matplotlib.backend_bases
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from typing import Optional, Callable
import logging
import enum



class PlotWidget(QWidget):
    

    class Tool(enum.Enum):
        Off = enum.auto()
        Pan = enum.auto()
        Zoom = enum.auto()


    class MyNavigationToolbar(NavigationToolbar2QT):
        
        toolitems = [toolitem for toolitem in NavigationToolbar2QT.toolitems if toolitem[0] in ('Home', 'Pan', 'Zoom', 'Back', 'Forward')]

        def stop_user_action(self):
            self.mode = matplotlib.backend_bases._Mode.NONE
            self._update_buttons_checked()

    
    def __init__(self):
        super().__init__()
        self._observers: list[Callable] = []

        style = Settings.plot_style or 'bmh'
        try:
            # can only be changed during start, otherwise the plot freaks out...
            matplotlib.pyplot.style.use(style)
        except Exception as ex:
            logging.error(f'Unable to set plotstyle to "{style}" ({ex})')

        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        #self._toolbar = PlotWidget.MyNavigationToolbar(self._canvas, self)
        self._toolbar = matplotlib.backend_bases.NavigationToolbar2(self._canvas)
        
        layout = QVBoxLayout()
        layout.addWidget(self._canvas)
        #layout.addWidget(self._toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        self._plot_mouse_down = False
        def get_coordinates(event: matplotlib.backend_bases.MouseEvent) -> tuple[float,float,float,float]:
            if not event.xdata or not event.ydata:
                return None, None, None, None
            if len(event.canvas.figure.axes) == 2:
                (ax1, ax2) = event.canvas.figure.axes
                if event.inaxes is ax2:
                    x2, y2 = event.x, event.y
                    x, y = ax1.transData.inverted().transform((event.x, event.y))
                    return x, y, x2, y2
                else:
                    x, y = event.xdata, event.ydata
                    x2, y2 = ax2.transData.inverted().transform((event.x, event.y))
                    return x, y, x2, y2
            else:
                x, y = event.xdata, event.ydata
                return x, y, None, None

        def callback_click(event: matplotlib.backend_bases.MouseEvent):
            nonlocal self
            if event.button and event.button==matplotlib.backend_bases.MouseButton.LEFT and event.xdata and event.ydata:
                self._plot_mouse_down = True
                x, y, x2, y2 = get_coordinates(event)
                self.on_mouse_event(left_btn_pressed=True, left_btn_event=True, x=x, y=y, x2=x2, y2=y2)
        def callback_release(event: matplotlib.backend_bases.MouseEvent):
            nonlocal self
            if event.button and event.button==matplotlib.backend_bases.MouseButton.LEFT:
                self._plot_mouse_down = False
                self.on_mouse_event(left_btn_pressed = False, left_btn_event=True, x=None, y=None, x2=None, y2=None)
        def callback_move(event: matplotlib.backend_bases.MouseEvent):
            nonlocal self
            if self._plot_mouse_down and event.xdata and event.ydata:
                x, y, x2, y2 = get_coordinates(event)
                self.on_mouse_event(left_btn_pressed=True, left_btn_event=False, x=x, y=y, x2=x2, y2=y2)
        self._figure.canvas.callbacks.connect('button_press_event', callback_click)
        self._figure.canvas.callbacks.connect('button_release_event', callback_release)
        self._figure.canvas.callbacks.connect('motion_notify_event', callback_move)
    

    def tool(self) -> PlotWidget.Tool:
        match self._canvas.toolbar.mode:
            case matplotlib.backend_bases._Mode.PAN:
                return PlotWidget.Tool.Pan
            case matplotlib.backend_bases._Mode.ZOOM:
                return PlotWidget.Tool.Zoom
        return PlotWidget.Tool.Off
    def setTool(self, tool: PlotWidget.Tool):
        match tool:
            case PlotWidget.Tool.Pan:
                self._canvas.toolbar.mode = matplotlib.backend_bases._Mode.PAN
            case PlotWidget.Tool.Zoom:
                self._canvas.toolbar.mode = matplotlib.backend_bases._Mode.ZOOM
            case _:
                self._canvas.toolbar.mode = matplotlib.backend_bases._Mode.NONE

    
    @staticmethod
    def get_plot_styles() -> list[str]:
        return list(matplotlib.pyplot.style.available)


    @staticmethod
    def get_color_cycle() -> list[str]:
        return matplotlib.pyplot.rcParams['axes.prop_cycle'].by_key()['color']


    def attach(self, callback: Callable):
        self._observers.append(callback)


    @property
    def figure(self) -> Figure:
        return self._figure


    def draw(self):
        self._figure.tight_layout()
        self._canvas.draw()


    def clear(self):
        self._figure.clf()


    def on_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float], x2: Optional[float], y2: Optional[float]):
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](left_btn_pressed, left_btn_event, x, y, x2, y2)
            except:
                del self._observers[i]
