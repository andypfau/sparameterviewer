from tkinter import END

import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as ticker
import numpy as np
import skrf, copy, math, cmath, glob, os

from lib import SParamFile, AppGlobal, BodeFano
from sparamviewer_rl_pygubu import SparamviewerPygubuApp



def v2db(v):
    return 20*np.log10(np.maximum(1e-15,np.abs(v)))



# extend auto-generated UI code
class SparamviewerReturnlossDialog(SparamviewerPygubuApp):
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

        pyplot.style.use('bmh')
        self.fig = Figure()
        panel = self.frame_rlplot
        self.canvas = FigureCanvasTkAgg(self.fig, master=panel)  
        self.canvas.draw()
        toolbar = NavigationToolbar2Tk(self.canvas, panel)
        toolbar.update()
        self.canvas.get_tk_widget().pack(expand=True, fill='both')
        
        # defaults
        self.port.set("1")
        self.int0.set("0")
        self.int1.set("999")
        self.tgt0.set("0")
        self.tgt1.set("10")

        def on_change():
            self.on_change()
        self.port.trace("w", lambda name, index, mode, sv = self.tgt0: on_change())
        self.int0.trace("w", lambda name, index, mode, sv = self.tgt0: on_change())
        self.int1.trace("w", lambda name, index, mode, sv = self.tgt0: on_change())
        self.tgt0.trace("w", lambda name, index, mode, sv = self.tgt0: on_change())
        self.tgt1.trace("w", lambda name, index, mode, sv = self.tgt0: on_change())

        # update
        self.on_change()
    

    def on_change(self, *args, **kwargs):
        try:
            file = self.files[self.combobox_files.current()]
            port = int(self.port.get())
            int0 = float(self.int0.get())*1e9
            int1 = float(self.int1.get())*1e9
            tgt0 = float(self.tgt0.get())*1e9
            tgt1 = float(self.tgt1.get())*1e9
        except Exception as ex:
            self.err_msg.set(f'Unable to parse input ({ex})')
            self.fig.clf()
            return
        
        try:
            self.update_plot(file, port, int0, int1, tgt0, tgt1)
        except Exception as ex:
            self.err_msg.set(f'Unable to plot ({ex})')
            self.fig.clf()
            return
        
        self.err_msg.set('')
    

    def update_plot(self, file: SParamFile, port: int, int0: float, int1: float, tgt0: float, tgt1: float):
        
        bodefano = BodeFano.from_network(file.nw, port, int0, int1, tgt0, tgt1)

        self.fig.clf()
        self.plot = self.fig.add_subplot(111)
        
        self.plot.fill_between(bodefano.nw_f_intrange/1e9, v2db(bodefano.nw_s_intrange), color='chartreuse', alpha=0.1)
        self.plot.plot(bodefano.nw_f_intrange/1e9, v2db(bodefano.nw_s_intrange), '-', label=f'S{port}{port}')
        self.plot.plot([bodefano.f_integration_actual_start_hz/1e9,bodefano.f_integration_actual_stop_hz/1e9], [bodefano.db_total,bodefano.db_total], ':', label=f'Current avg. RL (integration range): {bodefano.db_total:+.3g} dB')
        self.plot.plot([tgt0/1e9,tgt1/1e9], [bodefano.db_current,bodefano.db_current], '--', label=f'Current avg. RL (target range): {bodefano.db_current:+.3g} dB')
        self.plot.plot([tgt0/1e9,tgt1/1e9], [bodefano.db_optimized,bodefano.db_optimized], '-', label=f'Achievable avg. RL (target range): {bodefano.db_optimized:+.3g} dB')
        
        self.plot.set_xlabel('f / GHz')
        self.plot.set_ylabel('RL / dB')
        self.plot.legend()

        self.canvas.draw()
