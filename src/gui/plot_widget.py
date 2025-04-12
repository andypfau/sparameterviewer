from .settings import Settings
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot
from typing import Optional, Callable



class PlotWidget(QWidget):        

    class MyNavigationToolbar(NavigationToolbar2QT):
        toolitems = [toolitem for toolitem in NavigationToolbar2QT.toolitems if toolitem[0] in ('Home', 'Pan', 'Zoom')]

    
    def __init__(self):
        super().__init__()
        self._mouse_event_handler = None
        
        try:
            matplotlib.pyplot.style.use(Settings.plot_style or 'bmh')
        except:
            pass

        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = PlotWidget.MyNavigationToolbar(self._canvas, self)
        
        layout = QVBoxLayout()
        layout.addWidget(self._canvas)
        layout.addWidget(self._toolbar)
        self.setLayout(layout)
        
        BUTTON_LEFT = 1
        self._plot_mouse_down = True
        def callback_click(event):
            nonlocal self
            if event.button and event.button==BUTTON_LEFT and event.xdata and event.ydata:
                self._plot_mouse_down = True
                self.on_mouse_event(left_btn_pressed=True, left_btn_event=True, x=event.xdata, y=event.ydata)
        def callback_release(event):
            nonlocal self
            if event.button and event.button==BUTTON_LEFT:
                self._plot_mouse_down = False
                self.on_mouse_event(left_btn_pressed = False, left_btn_event=True, x=None, y=None)
        def callback_move(event):
            nonlocal self
            if self._plot_mouse_down and event.xdata and event.ydata:
                self.on_mouse_event(left_btn_pressed=True, left_btn_event=False, x=event.xdata, y=event.ydata)
        self._figure.canvas.callbacks.connect('button_press_event', callback_click)
        self._figure.canvas.callbacks.connect('button_release_event', callback_release)
        self._figure.canvas.callbacks.connect('motion_notify_event', callback_move)
    

    def set_cursor_event_handler(self, handler: Callable):
        pass
    

    @property
    def figure(self) -> Figure:
        return self._figure


    def draw(self):
        self._canvas.draw()


    def clear(self):
        self._figure.clf()


    def on_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float]):
        if not self._mouse_event_handler:
            return
        self._mouse_event_handler(left_btn_pressed, left_btn_event, x, y)
