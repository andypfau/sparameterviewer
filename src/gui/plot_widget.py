from .settings import Settings
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot



class PlotWidget(QWidget):        

    class MyNavigationToolbar(NavigationToolbar2QT):
        toolitems = [toolitem for toolitem in NavigationToolbar2QT.toolitems if toolitem[0] in ('Home', 'Pan', 'Zoom')]

    
    def __init__(self):
        super().__init__()
        
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

    
    @property
    def figure(self) -> Figure:
        return self._figure


    def draw(self):
        self._canvas.draw()


    def clear(self):
        self._figure.clf()
