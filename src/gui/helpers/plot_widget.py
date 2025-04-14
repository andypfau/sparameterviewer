import matplotlib.backend_bases
from .settings import Settings
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import matplotlib.backend_bases
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from typing import Optional, Callable
import logging



class PlotWidget(QWidget):        

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
        self._toolbar = PlotWidget.MyNavigationToolbar(self._canvas, self)
        
        layout = QVBoxLayout()
        layout.addWidget(self._canvas)
        layout.addWidget(self._toolbar)
        self.setLayout(layout)
        
        self._plot_mouse_down = False
        def callback_click(event: matplotlib.backend_bases.MouseEvent):
            nonlocal self
            if event.button and event.button==matplotlib.backend_bases.MouseButton.LEFT and event.xdata and event.ydata:
                self._plot_mouse_down = True
                self.on_mouse_event(left_btn_pressed=True, left_btn_event=True, x=event.xdata, y=event.ydata)
        def callback_release(event: matplotlib.backend_bases.MouseEvent):
            nonlocal self
            if event.button and event.button==matplotlib.backend_bases.MouseButton.LEFT:
                self._plot_mouse_down = False
                self.on_mouse_event(left_btn_pressed = False, left_btn_event=True, x=None, y=None)
        def callback_move(event: matplotlib.backend_bases.MouseEvent):
            nonlocal self
            if self._plot_mouse_down and event.xdata and event.ydata:
                self.on_mouse_event(left_btn_pressed=True, left_btn_event=False, x=event.xdata, y=event.ydata)
        self._figure.canvas.callbacks.connect('button_press_event', callback_click)
        self._figure.canvas.callbacks.connect('button_release_event', callback_release)
        self._figure.canvas.callbacks.connect('motion_notify_event', callback_move)
    

    @staticmethod
    def get_plot_styles() -> list[str]:
        return list(matplotlib.pyplot.style.available)


    def attach(self, callback: Callable):
        self._observers.append(callback)


    def stop_user_action(self):
        self._toolbar.stop_user_action()
    

    @property
    def figure(self) -> Figure:
        return self._figure


    def draw(self):
        self._canvas.draw()


    def clear(self):
        self._figure.clf()


    def on_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float]):
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](left_btn_pressed, left_btn_event, x, y)
            except:
                del self._observers[i]
