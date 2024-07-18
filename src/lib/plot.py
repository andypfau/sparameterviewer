from .si import Si, SiFmt
from .structs import PlotData, PlotDataQuantity
from .shortstr import remove_common_prefixes_and_suffixes

import math
import re
import numpy as np
import logging
from dataclasses import dataclass
import matplotlib.pyplot as pyplot
import matplotlib.ticker as ticker


@dataclass
class ItemToPlot:
    x: "list[float]"
    y: "list[float]"
    z: "list[float]|None"
    name: str
    style: str



class PlotHelper:


    class Cursor:
        
        def __init__(self, plot: "PlotHelper", style: str, color: object = None):
            
            self.plot = plot
            self.enabled = False
            self.style = style
            self.color = color

            self.x, self.y, self.z = 0, 0, None
            self.data: PlotHelper.Data
            self.data = None

            self._is_set = False
            self._hl, self._vl = None, None
        

        def set(self, x: float, y: float, z: float, enable: bool = True, color: object = None):
            self.x, self.y, self.z = x, y, z
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
        y_qty: "str", y_fmt: SiFmt, y_log: bool, z_qty: "str" = None, z_fmt: SiFmt = None,
        smith_type: str='z', smith_z=1.0,
        show_legend: bool = True, hide_single_item_legend: bool = False, shorten_legend: bool = False):
        
        self.cursors = [
            PlotHelper.Cursor(self, '--'),
            PlotHelper.Cursor(self, '-.'),
        ]

        self.plots: list[PlotData]
        self.plots = []

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
        self.z_qty = z_qty
        self.z_fmt = z_fmt
        self.show_legend = show_legend
        self.hide_single_item_legend = hide_single_item_legend
        self.shorten_legend = shorten_legend

        self.fig.clf()
        
        self.x_range = [+1e99,-1e99]
        self.y_range = [+1e99,-1e99]
        self.z_range = [+1e99,-1e99]
        self.items_to_plot: list[ItemToPlot]
        self.items_to_plot = []

        self.plot = None # type: pyplot.axes.Axes
    

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


    def get_closest_plot_point(self, x: float, y: float, name: "str|None" = None) -> "tuple[PlotHelper.Data,float,float,float]":

        best_error = +1e99
        best_x = None
        best_y = None
        best_z = None
        best_plot = None

        for plot in self.plots:
            if name is not None:
                if plot.name != name:
                    continue
            for idx,(dx,dy) in enumerate(zip(plot.x.values, plot.y.values)):
                error = math.sqrt(pow(x-dx,2)+pow(y-dy,2))
                if error < best_error:
                    best_error = error
                    best_x = dx
                    best_y = dy
                    if plot.z is not None:
                        best_z = plot.z.values[idx]
                    best_plot = plot

        return best_plot, best_x, best_y, best_z


    def add(self, x: "list[float]", y: "list[float]", z: "list[float]|None", name: str, style: str):
        assert len(x)==len(y)
        if len(x) < 1:
            logging.info(f'Ignoring plot "{name}" (contains zero points)')
            return
        
        self.x_range = [min(self.x_range[0],min(x)), max(self.x_range[1],max(x))]
        self.y_range = [min(self.y_range[0],min(y)), max(self.y_range[1],max(y))]
        if z is not None:
            self.z_range = [min(self.z_range[0],min(z)), max(self.z_range[1],max(z))]
        self.items_to_plot.append(ItemToPlot(x, y, z, name, style))
    

    def render(self):

        def get_r_max():
            r_max = 0
            for item in self.items_to_plot:
                r_this = max(np.sqrt(np.power(item.x,2) + np.power(item.y,2)))
                r_max = max(r_max, r_this)
            return r_max

        if self.polar:
            self.plot = self.fig.add_subplot(111, projection='polar')
            r_max = get_r_max()
            if r_max <= 1:
                self.plot.set_ylim((0,1))
        elif self.smith:
            from skrf import plotting
            self.plot = self.fig.add_subplot(111)
            r_max = get_r_max()
            r_smith = 1 if r_max<=1 else r_max*1.05
            plotting.smith(ax=self.plot, chart_type=self.smith_type, ref_imm=self.smith_z, draw_labels=True, smithR=r_smith)
        else:
            self.plot = self.fig.add_subplot(111)
        
        self.any_legend = False

        labels = [item.name for item in self.items_to_plot]
        if self.shorten_legend:
            labels = remove_common_prefixes_and_suffixes(labels)

        for item,label in zip(self.items_to_plot, labels):
        
            x, y, z, name, style = item.x, item.y, item.z, item.name, item.style

            # escaping for matplotlib
            if label.startswith('_'):
                label = ' _' + label[1:]

            def fix_log(x,y):
                if x[0]<=0 and self.x_log:
                    x,y = x[1:], y[1:]
                if y[0]<=0 and self.y_log:
                    x,y = x[1:], y[1:]
                return x,y
            
            if self.polar:
                c = x + 1j*y
                new_plt = self.plot.plot(np.angle(c), np.abs(c), style, label=label)
            elif self.smith:
                c = x + 1j*y
                from skrf import plotting
                new_plt = plotting.plot_smith(s=c, ax=self.plot, chart_type='z', show_legend=True, label=label, title=None)
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
                PlotDataQuantity(self.z_qty, self.z_fmt, z) if z is not None else None,
                style,
                color,
            ))
        
        if self.smith and r_smith!=1:
            # for whatever reason, Smith charts can only be scaled after adding data (whereas e.g. polar plots can be scaled before)
            self.plot.set_xlim((-r_smith,+r_smith))
            self.plot.set_ylim((-r_smith,+r_smith))


    def finish(self):
                
        if len(self.plots)<1:
            return
        
        show_legend = self.show_legend
        if len(self.items_to_plot) <= 1 and self.hide_single_item_legend:
            show_legend = False
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
