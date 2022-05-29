from .touchstone import Touchstone
from .si import Si, SiFmt
from .structs import PlotData, PlotDataQuantity

import math
import numpy as np
from dataclasses import dataclass
import matplotlib.pyplot as pyplot
import matplotlib.ticker as ticker


class PlotHelper:


    class Cursor:
        
        def __init__(self, plot: "PlotHelper", style: str, color: object = None):
            self.plot = plot
            self.enabled = False
            self.style = style
            self.color = color
            self.x, self.y = 0, 0
            self.data = None # type: PlotHelper.Data
            self._is_set = False
            self._hl, self._vl = None, None
        

        def set(self, x: float, y: float, enable: bool = True, color: object = None):
            self.x, self.y = x, y
            self._is_set = True
            self.enabled = enable
            self.color = color
            self.update()


        def enable(self, enable: bool):
            self.enabled = enable
            self.update()
        

        def update(self):

            LINEWIDTH = 1.33
            
            if self.enabled and self._is_set:

                if not self._hl:
                    self._hl = self.plot.plot.axhline(self.y, linewidth=LINEWIDTH)
                self._hl.set_linestyle(self.style)
                if self.color is not None:
                    self._hl.set_color(self.color)
                self._hl.set_ydata([self.y, self.y])
                self._hl.set_visible(True)

                if not self._vl:
                    self._vl = self.plot.plot.axvline(self.x, linewidth=LINEWIDTH)
                self._vl.set_linestyle(self.style)
                if self.color is not None:
                    self._vl.set_color(self.color)
                self._vl.set_xdata([self.x, self.x])
                self._vl.set_visible(True)

            else:

                if self._vl:
                    self._hl.set_visible(False)
                    self._vl.set_visible(False)
    

    def __init__(self, fig: any, smith: bool, polar: bool, x_qty: str, x_fmt: SiFmt, x_log: bool,
        y_qty: "str", y_fmt: SiFmt, y_log: bool, smith_type: str='z', smith_z=1.0):
        
        self.cursors = [
            PlotHelper.Cursor(self, '--'),
            PlotHelper.Cursor(self, '-.'),
        ]

        self.plots = [] # type: list[PlotData]

        self.fig = fig
        self.smith = smith
        self.polar = polar
        self.smith_type = smith_type
        self.smith_z = smith_z
        self.x_qty = x_qty
        self.x_fmt = x_fmt
        self.x_log = x_log
        self.y_qty = y_qty
        self.y_fmt = y_fmt
        self.y_log = y_log
        self.fig.clf()
        
        if self.polar:
            self.plot = self.fig.add_subplot(111, projection='polar')
        elif self.smith:
            from skrf import plotting
            self.plot = self.fig.add_subplot(111)
            plotting.smith(ax=self.plot, chart_type=self.smith_type, ref_imm=self.smith_z, draw_labels=True)
        else:
            self.plot = self.fig.add_subplot(111)
        
        self.x_range = [+1e99,-1e99]
        self.y_range = [+1e99,-1e99]
    

    def get_closest_cursor(self, x: float, y: float) -> "tuple[int,PlotHelper.Data]":

        if (not self.cursors[0].enabled) and (not self.cursors[1].enabled):
            return (None, None)
        if (self.cursors[0].enabled) and (not self.cursors[1].enabled):
            return (0, self.cursors[0])
        if (not self.cursors[0].enabled) and (self.cursors[1].enabled):
            return (1, self.cursors[1])

        error_0 = math.sqrt(pow(x-self.cursors[0].x,2) + pow(y-self.cursors[0].y,2))
        error_1 = math.sqrt(pow(x-self.cursors[1].x,2) + pow(y-self.cursors[1].y,2))
        if error_0 < error_1:
            return (0, self.cursors[0])
        else:         
            return (1, self.cursors[1])


    def get_closest_plot_point(self, x: float, y: float, name: "str|None" = None) -> "tuple[PlotHelper.Data,float,float]":

        best_error = +1e99
        best_x = None
        best_y = None
        best_plot = None

        for plot in self.plots:
            if name is not None:
                if plot.name != name:
                    continue
            for dx,dy in zip(plot.x.values, plot.y.values):
                error = math.sqrt(pow(x-dx,2)+pow(y-dy,2))
                if error < best_error:
                    best_error = error
                    best_x = dx
                    best_y = dy
                    best_plot = plot

        return best_plot, best_x, best_y


    def add(self, x: "list[float]", y: "list[float]", name: str, style: str):
        
        self.x_range = [min(self.x_range[0],min(x)), max(self.x_range[1],max(x))]
        self.y_range = [min(self.y_range[0],min(y)), max(self.y_range[1],max(y))]
        
        def fix_log(x,y):
            if x[0]<=0 and self.x_log:
                x,y = x[1:], y[1:]
            if y[0]<=0 and self.y_log:
                x,y = x[1:], y[1:]
            return x,y
        
        # escaping
        label = name
        if label.startswith('_'):
            label = ' _' + label[1:]
        
        if self.polar:
            new_plt = self.plot.plot(x, y, style, label=label)
        elif self.smith:
            from skrf import plotting
            new_plt = plotting.plot_smith(s=x+1j*y, ax=self.plot, chart_type='z', show_legend=True, label=label, title=None)
        elif self.x_log and self.y_log:
            x,y = fix_log(x,y)
            new_plt = self.plot.loglog(x, y, style, label=label)
        elif self.x_log:
            x,y = fix_log(x,y)
            new_plt = self.plot.semilogx(x, y, style, label=label)
        elif self.y_log:
            x,y = fix_log(x,y)
            new_plt = self.plot.semilogy(x, y, style, label=label)
        else:
            new_plt = self.plot.plot(x, y, style, label=label)

        color = new_plt[0].get_color() if new_plt is not None else None
        self.plots.append(PlotData(
            name, 
            PlotDataQuantity(self.x_qty, self.x_fmt, x),
            PlotDataQuantity(self.y_qty, self.y_fmt, y),
            style,
            color,
        ))


    def finish(self, show_legend):
        
        if len(self.plots)<1:
            return
        
        if show_legend:
            self.plot.legend()
        
        if not self.polar:
            if self.x_qty is not None:
                self.plot.set_xlabel(self.x_qty)
            if self.y_qty is not None:
                self.plot.set_ylabel(self.y_qty)
            
            @ticker.FuncFormatter
            def x_axis_formatter(value, _):
                return str(Si(value, si_fmt=self.x_fmt))
            self.plot.xaxis.set_major_formatter(x_axis_formatter)
            
            @ticker.FuncFormatter
            def y_axis_formatter(value, _):
                return str(Si(value, si_fmt=self.y_fmt))
            self.plot.yaxis.set_major_formatter(y_axis_formatter)
