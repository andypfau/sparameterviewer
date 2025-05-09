import matplotlib.lines
from .si import Si, SiFmt
from .structs import PlotData, PlotDataQuantity
from .shortstr import remove_common_prefixes_and_suffixes
from .utils import natural_sort_key

import math
import numpy as np
import logging
import matplotlib
import matplotlib.pyplot as pyplot
import matplotlib.ticker as ticker
import pandas as pd
from dataclasses import dataclass
from typing import Optional


@dataclass
class ItemToPlot:
    data: PlotData
    prefer_seconary_yaxis: bool
    currently_used_axis: int
    style: str
    color: str
    width: float
    opacity: float
    label: str = None



class PlotHelper:


    class Cursor:
        
        def __init__(self, plot: "PlotHelper", style: str, color: object = None, use_2nd_axis: bool = False):
            
            self.plot = plot
            self.enabled = False
            self.style = style
            self.color = color
            self.use_2nd_axis = use_2nd_axis
            self.axis_changed = False

            self.x, self.y, self.z = 0, 0, None

            self._is_set = False
            self._hl: matplotlib.lines.Line2D = None
            self._vl: matplotlib.lines.Line2D = None
        

        def set(self, x: float, y: float, z: float, enable: bool = True, color: object = None, use_2nd_axis: bool = False):
            self.x, self.y, self.z = x, y, z
            self._is_set = True
            self.enabled = enable
            self.color = color
            self.axis_changed = self.use_2nd_axis != use_2nd_axis
            self.use_2nd_axis = use_2nd_axis
            self.update()


        def enable(self, enable: bool):
            self.enabled = enable
            self.update()
        

        def update(self):

            LINEWIDTH = 1.0

            if self.axis_changed:
                if self._hl:
                    self._hl.set_visible(False)
                    self._hl.remove()
                    self._hl = None
                if self._vl:
                    self._vl.set_visible(False)
                    self._vl.remove()
                    self._vl = None
            
            if self.enabled and self._is_set:

                plot = self.plot.plot2 if self.use_2nd_axis else self.plot.plot

                if not self._hl:
                    self._hl = plot.axhline(self.y, linewidth=LINEWIDTH)
                self._hl.set_linestyle(self.style)
                if self.color is not None:
                    self._hl.set_color(self.color)
                self._hl.set_ydata([self.y, self.y])
                self._hl.set_visible(True)

                if not self._vl:
                    self._vl = plot.axvline(self.x, linewidth=LINEWIDTH)
                self._vl.set_linestyle(self.style)
                if self.color is not None:
                    self._vl.set_color(self.color)
                self._vl.set_xdata([self.x, self.x])
                self._vl.set_visible(True)

            else:

                if self._hl:
                    self._hl.set_visible(False)
                if self._vl:
                    self._vl.set_visible(False)
    

    def __init__(self, figure: any, smith: bool, polar: bool, x_qty: str, x_fmt: SiFmt, x_log: bool,
        y_qty: "str", y_fmt: SiFmt, y_log: bool, y2_qty: "str", y2_fmt: SiFmt, z_qty: "str" = None, z_fmt: SiFmt = None,
        smith_type: str='z', smith_z=1.0,
        show_legend: bool = True, hide_single_item_legend: bool = False, shorten_legend: bool = False):
        
        self.cursors = [
            PlotHelper.Cursor(self, '--'),
            PlotHelper.Cursor(self, '-.'),
        ]

        self._figure = figure
        self._smith = smith
        self._polar = polar
        self._smith_type = smith_type
        self._smith_z = smith_z
        self._x_qty = x_qty
        self._x_fmt = x_fmt
        self._x_log = x_log
        self._y_qty = y_qty
        self._y_fmt = y_fmt
        self._y2_qty = y2_qty
        self._y2_fmt = y2_fmt
        self._y_log = y_log
        self._z_qty = z_qty
        self._z_fmt = z_fmt
        self._show_legend = show_legend
        self._hide_single_item_legend = hide_single_item_legend
        self._shorten_legend = shorten_legend
        self._use_two_yaxes = None
        self._axes_swapped = None
        self._r_smith = None
        
        self._figure.clf()
        
        self.x_range = [+1e99,-1e99]
        self.y_range = [+1e99,-1e99]
        self.z_range = [+1e99,-1e99]
        self.items: list[ItemToPlot] = []

        self.plot: pyplot.Axes = None
        self.plot2: pyplot.Axes = None


    @property
    def plots(self) -> list[PlotData]:
        return [item.data for item in self.items]


    @property
    def x_fmt(self) -> SiFmt:
        return self._x_fmt


    @property
    def y_fmt(self) -> SiFmt:
        return self._y_fmt


    @property
    def y2_fmt(self) -> SiFmt:
        return self._y2_fmt


    @property
    def y_left_fmt(self) -> SiFmt:
        if self._axes_swapped:
            return self._y2_fmt
        else:
            return self._y_fmt


    @property
    def y_right_fmt(self) -> Optional[SiFmt]:
        if self._use_two_yaxes:
            if self._axes_swapped:
                return self._y2_fmt
            else:
                return self._y_fmt
        else:
            return None


    @property
    def z_fmt(self) -> SiFmt:
        return self._z_fmt
    

    def get_closest_cursor(self, x: float, y: float, width: float = 1, height: float = 1) -> "tuple[int,PlotHelper.Cursor]":

        if (not self.cursors[0].enabled) and (not self.cursors[1].enabled):
            return (None, None)
        if (self.cursors[0].enabled) and (not self.cursors[1].enabled):
            return (0, self.cursors[0])
        if (not self.cursors[0].enabled) and (self.cursors[1].enabled):
            return (1, self.cursors[1])

        dx0 = (x-self.cursors[0].x) /  width if x is not None else 0
        dy0 = (y-self.cursors[0].y) / height if y is not None else 0
        dx1 = (x-self.cursors[1].x) /  width if x is not None else 0
        dy1 = (y-self.cursors[1].y) / height if y is not None else 0

        dist0 = math.sqrt(dx0**2 + dy0**2)
        dist1 = math.sqrt(dx1**2 + dy1**2)
        if dist0 < dist1:
            return (0, self.cursors[0])
        else:         
            return (1, self.cursors[1])


    def get_closest_plot_point(self, x: float, y: float, name: "str|None" = None, width: float = 1, height: float = 1) -> "tuple[PlotData,float,float,float]":

        best_error = +1e99
        best_x = None
        best_y = None
        best_z = None
        best_plot = None

        for plot in self.items:
            if name is not None:
                if plot.data.name != name:
                    continue
            if plot.currently_used_axis != 1:
                continue  # tracing cursors on the right axis does not work yet
            
            dx = (np.array(plot.data.x.values) - x) /  width if x is not None else 0
            dy = (np.array(plot.data.y.values) - y) / height if y is not None else 0
            dist = np.sqrt(np.abs(dx**2) + np.abs(dy**2))
            idx = np.argmin(dist)
            error = dist[idx]
            if error < best_error:
                best_error = error
                best_x = plot.data.x.values[idx]
                best_y = plot.data.y.values[idx]
                best_z = plot.data.z.values[idx] if plot.data.z is not None else None
                best_plot = plot.data

        return best_plot, best_x, best_y, best_z


    def add(self, x: "list[float]", y: "list[float]", z: "list[float]|None", name: str, style: str, color: str, width: float, opacity: float, prefer_2nd_yaxis: bool = False):
        self._use_two_yaxes = None
        self._axes_swapped = None
        assert len(x)==len(y)
        if len(x) < 1:
            logging.info(f'Ignoring plot "{name}" (contains zero points)')
            return
        
        self.x_range = [min(self.x_range[0],min(x)), max(self.x_range[1],max(x))]
        self.y_range = [min(self.y_range[0],min(y)), max(self.y_range[1],max(y))]
        if z is not None:
            self.z_range = [min(self.z_range[0],min(z)), max(self.z_range[1],max(z))]

        self.items.append(
            ItemToPlot(
                PlotData(
                    name, 
                    PlotDataQuantity(self._x_qty, self._x_fmt, x),
                    PlotDataQuantity(self._y_qty, self._y_fmt, y),
                    PlotDataQuantity(self._z_qty, self._z_fmt, z) if z is not None else None,  
                    'black'  # placeholder
                ),
                prefer_2nd_yaxis,
                -1,  # placeholder
                style,
                color,
                width,
                opacity,
            )
        )
    

    def render(self):
        self._use_two_yaxes = False
        self._axes_swapped = False
        self._r_smith = None
        self._prepare_plots_and_axes()
        self._add_traces_to_plots()
        self._fix_axis_labels()


    def _prepare_plots_and_axes(self):
        def get_r_max():
            r_max = 0
            for item in self.items:
                r_this = max(np.sqrt(np.power(item.data.x.values,2) + np.power(item.data.y.values,2)))
                r_max = max(r_max, r_this)
            return r_max

        self.plot2 = None
        if self._polar:
            self.plot = self._figure.add_subplot(111, projection='polar')
            r_max = get_r_max()
            if r_max <= 1:
                self.plot.set_ylim((0,1))
            self._use_two_yaxes = False
        elif self._smith:
            from skrf import plotting
            self.plot = self._figure.add_subplot(111)
            r_max = get_r_max()
            self._r_smith = 1 if r_max<=1 else r_max*1.05
            plotting.smith(ax=self.plot, chart_type=self._smith_type, ref_imm=self._smith_z, draw_labels=True, smithR=self._r_smith)
            self._use_two_yaxes = False
        else:
            anything_on_primary_yaxis = any([not item.prefer_seconary_yaxis for item in self.items])
            anything_on_secondary_yaxis = any([item.prefer_seconary_yaxis for item in self.items])
            self._use_two_yaxes = anything_on_primary_yaxis and anything_on_secondary_yaxis
            self.plot = self._figure.add_subplot(111)
            if self._use_two_yaxes:
                self.plot2 = self.plot.twinx()
        
    
    def _add_traces_to_plots(self):
        self.any_legend = False

        for item in self.items:
            item.label = item.data.name
        if self._shorten_legend:
            labels = [item.label for item in self.items]
            labels = remove_common_prefixes_and_suffixes(labels)
            for label,item in zip(labels,self.items):
                item.label = label
        
        self.items = sorted(self.items, key=lambda item: natural_sort_key(item.label))

        for item_index,item in enumerate(self.items):
            if item.prefer_seconary_yaxis and self._use_two_yaxes:
                plot = self.plot2
                self.items[item_index].currently_used_axis = 2
            else:
                plot = self.plot
                self.items[item_index].currently_used_axis = 1
        
            x, y, style, color, width, opacity = item.data.x.values, item.data.y.values, item.style, item.color, item.width, item.opacity

            # escaping for matplotlib
            if item.label.startswith('_'):
                item.label = ' _' + item.label[1:]

            def fix_log(x,y):
                if x[0]<=0 and self._x_log:
                    x,y = x[1:], y[1:]
                if y[0]<=0 and self._y_log:
                    x,y = x[1:], y[1:]
                return x,y
            
            if self._polar:
                c = x + 1j*y
                new_plt = plot.plot(np.angle(c), np.abs(c), style, label=item.label, color=color, lw=width, alpha=opacity)
            elif self._smith:
                c = x + 1j*y
                from skrf import plotting
                new_plt = plotting.plot_smith(s=c, ax=plot, chart_type='z', show_legend=True, label=item.label, title=None, color=color, lw=width, alpha=opacity)
            elif self._x_log or self._y_log:
                x,y = fix_log(x,y)
                new_plt = plot.plot(x, y, style, label=item.label, color=color, lw=width, alpha=opacity)
            else:
                new_plt = plot.plot(x, y, style, label=item.label, color=color, lw=width, alpha=opacity)

            color = new_plt[0].get_color() if new_plt is not None else None
            self.items[item_index].data.color = color
        
        if self._smith:
            assert self._r_smith is not None
            if self._r_smith!=1:
                # for whatever reason, Smith charts can only be scaled after adding data (whereas e.g. polar plots can be scaled before)
                self.plot.set_xlim((-self._r_smith,+self._r_smith))
                self.plot.set_ylim((-self._r_smith,+self._r_smith))
                
        show_legend = self._show_legend
        if len(self.items) <= 1 and self._hide_single_item_legend:
            show_legend = False
        if show_legend:
            self.plot.legend()
        

    def _fix_axis_labels(self):
        if self._polar or self._smith:
            return
        
        if self._use_two_yaxes:
            y_qty, y_fmt, y_log, y2_qty, y2_fmt = self._y_qty, self._y_fmt, self._y_log, self._y2_qty, self._y2_fmt
            self.plot2.grid(False)  # two grids in one plot are just confusing
        else:
            self._axes_swapped = any([item.currently_used_axis==1 and item.prefer_seconary_yaxis for item in self.items])
            if self._axes_swapped:
                # data for axis 2 was displayed on axis 1, so we nee to use the other unit
                y_qty, y_fmt, y_log, y2_qty, y2_fmt = self._y2_qty, self._y2_fmt, False, None, None
            else:
                y_qty, y_fmt, y_log, y2_qty, y2_fmt = self._y_qty, self._y_fmt, self._y_log, None, None
        
        if self._x_qty is not None:
            self.plot.set_xlabel(self._x_qty)
        if y_qty is not None:
            self.plot.set_ylabel(y_qty)
        if y2_qty is not None:
            self.plot2.set_ylabel(y2_qty)
        
        @ticker.FuncFormatter
        def x_axis_formatter(value, _):
            return str(Si(value, si_fmt=self._x_fmt))
        self.plot.xaxis.set_major_formatter(x_axis_formatter)
        
        if y_fmt is not None:
            @ticker.FuncFormatter
            def y_axis_formatter(value, _):
                return str(Si(value, si_fmt=y_fmt))
            self.plot.yaxis.set_major_formatter(y_axis_formatter)
        
        if y2_fmt is not None:
            @ticker.FuncFormatter
            def y_axis_formatter(value, _):
                return str(Si(value, si_fmt=y2_fmt))
            self.plot2.yaxis.set_major_formatter(y_axis_formatter)
        
        if self._x_log:
            self.plot.set_xscale('log')
        if y_log:
            self.plot.set_yscale('log')
