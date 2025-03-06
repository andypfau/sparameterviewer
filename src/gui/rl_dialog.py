from tkinter import END, DISABLED, NORMAL

import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as ticker
import numpy as np
import skrf, copy, math, cmath, glob, os

from lib import SParamFile, AppGlobal, BodeFano, TkText, Si, parse_si_range, format_si_range
from .rl_dialog_pygubuui import PygubuAppUI
from .settings import Settings



def v2db(v):
    return 20*np.log10(np.maximum(1e-15,np.abs(v)))



# extend auto-generated UI code
class SparamviewerReturnlossDialog(PygubuAppUI):
    def __init__(self, master, files: "list[SParamFile]", selected_tag: any = None):
        super().__init__(master)
        
        AppGlobal.set_toplevel_icon(self.toplevel_rl)

        self.files = files

        values = []
        idx_to_select = 0
        for i,nwf in enumerate(files):
            values.append(nwf.name)
            if nwf.tag == selected_tag:
                idx_to_select = i
        self.combobox_files['values'] = values
        if len(values)>0:
            self.combobox_files.current(idx_to_select)

        pyplot.style.use(Settings.plot_style if Settings.plot_style is not None else 'bmh')
        self.fig = Figure()
        panel = self.frame_rlplot
        self.canvas = FigureCanvasTkAgg(self.fig, master=panel)  
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, panel)
        toolbar.update()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        
        self.entry_int['values'] = (
            format_si_range(any, any, allow_total_wildcard=True),
            format_si_range(0, 10e9),
        )
        self.entry_tgt['values'] = (
            format_si_range(1e9, 2e9),
        )
        
        # defaults
        self.port.set("1")
        self.int_range.set(format_si_range(any, any, allow_total_wildcard=True))
        self.tgt_range.set(format_si_range(1e9, 2e9))

        self.port.trace_add('write', self.on_change)
        self.int_range.trace_add('write', self.on_change)
        self.tgt_range.trace_add('write', self.on_change)
        self.plot_kind.trace_add('write', self.on_change)

        # update
        self.on_change()
        

    def run(self, focus: bool = True):
        if focus:
            self.mainwindow.focus_force()
        super().run()
    

    def on_change(self, *args, **kwargs):

        def error(msg):
            TkText.set_text(self.result_box, msg)
            self.fig.clf()

        try:
            file = self.files[self.combobox_files.current()]
            port = int(self.port.get())
            (int0, int1) = parse_si_range(self.int_range.get())
            (tgt0, tgt1) = parse_si_range(self.tgt_range.get(), wildcard_low=None, wildcard_high=None)
            plot_kind = self.plot_kind.get()
        except Exception as ex:
            error(f'Unable to parse input ({ex})')
            return
        
        if int0 is None or int1 is None:
            error('Invlaid integration range')
            return
        if tgt0 is None or tgt1 is None:
            error('Invlaid target range')
            return
        
        try:
            self.update_plot(file, port, int0, int1, tgt0, tgt1, plot_kind)
        except Exception as ex:
            error(f'Unable to plot ({ex})')
            return
    

    def update_plot(self, file: SParamFile, port: int, int0: float, int1: float, tgt0: float, tgt1: float, plot_kind:str):
        
        bodefano = BodeFano.from_network(file.nw, port, int0, int1, tgt0, tgt1)

        int0, int1 = bodefano.f_integration_actual_start_hz, bodefano.f_integration_actual_stop_hz

        message = \
            f'Available: {bodefano.db_available:+.3g} dB ({Si(bodefano.f_integration_actual_start_hz,"Hz")}..{Si(bodefano.f_integration_actual_stop_hz,"Hz")})\n' + \
            f'Current: {bodefano.db_current:+.3g} dB ({Si(tgt0,"Hz")}..{Si(tgt1,"Hz")})\n' + \
            f'Achievable: {bodefano.db_achievable:+.3g} dB ({Si(tgt0,"Hz")}..{Si(tgt1,"Hz")})'
        TkText.set_text(self.result_box, message)

        self.fig.clf()
        self.plot = self.fig.add_subplot(111)

        if plot_kind=='rl_hist':
            self.plot.hist(x=v2db(bodefano.nw_s_intrange), ls='-', color='darkblue', label=f'S{port}{port}')
            self.plot.axvline(x=bodefano.db_available, ls=':', color='blue', label=f'Available')
            self.plot.axvline(x=bodefano.db_current, ls='--', color='blue', label=f'Current')
            self.plot.axvline(x=bodefano.db_achievable, ls='-', color='green', label=f'Achievable')
            
            self.plot.set_xlabel('RL / dB')
            self.plot.set_ylabel('Histogram')
            self.plot.legend()
        
        elif plot_kind=='rl_vs_f':
            self.plot.fill_between(bodefano.nw_f_intrange/1e9, v2db(bodefano.nw_s_intrange), color='chartreuse', alpha=0.1)
            self.plot.plot(bodefano.nw_f_intrange/1e9, v2db(bodefano.nw_s_intrange), '-', color='darkblue', label=f'S{port}{port}')
            self.plot.plot([bodefano.f_integration_actual_start_hz/1e9,bodefano.f_integration_actual_stop_hz/1e9], [bodefano.db_available,bodefano.db_available], ':', color='blue', label=f'Available')
            self.plot.plot([tgt0/1e9,tgt1/1e9], [bodefano.db_current,bodefano.db_current], '--', color='blue', label=f'Current')
            self.plot.plot([tgt0/1e9,tgt1/1e9], [bodefano.db_achievable,bodefano.db_achievable], '-', color='green', label=f'Achievable')
            
            self.plot.set_xlabel('f / GHz')
            self.plot.set_ylabel('RL / dB')
            self.plot.legend()

        self.canvas.draw()
