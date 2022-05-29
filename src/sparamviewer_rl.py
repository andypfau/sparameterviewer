#!/bin/python3

from ast import Load
from asyncio import selector_events
from tkinter import END

import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.ticker as ticker
import numpy as np
import skrf, copy, math, cmath, glob, os
from scipy.interpolate import interp1d
from scipy.integrate import trapz

from lib import LoadedSParamFile, AppGlobal
from sparamviewer_rl_pygubu import SparamviewerPygubuApp


def crop_xrange(x, y, xmin=-1e99, xmax=+1e99):
    cropped = [(xx,yy) for xx,yy in zip(x,y) if xmin<=xx<=xmax]
    x_cropped = [xx for (xx,yy) in cropped]
    y_cropped = [yy for (xx,yy) in cropped]
    return np.array(x_cropped), np.array(y_cropped)

def integrate(f, s):
    integral = trapz(np.log(1/np.abs(s)), f*math.tau)
    return integral

def get_optimum_rl(integral, f0, f1):
    omega0, omega1 = math.tau*f0, math.tau*f1
    gamma = 1 / math.exp(integral / (omega1-omega0))
    db = 20*math.log10(gamma)
    return db


# extend auto-generated UI code
class SparamviewerReturnlossDialog(SparamviewerPygubuApp):
    def __init__(self, master, files: "list(LoadedSParamFile)", selected_id: "str|None"):
        super().__init__(master)
        
        AppGlobal.set_toplevel_icon(self.toplevel_rl)

        self.files = files

        values = []
        idx_to_select = 0
        for i,f in enumerate(files):
            values.append(os.path.split(f.filename)[1])
            if f.id==selected_id:
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
    

    def update_plot(self, file: LoadedSParamFile, port: int, int0: float, int1: float, tgt0: float, tgt1: float):
        
        nw_f_complete = file.sparam.frequencies
        nw_s_complete = file.sparam.get_sparam(port, port)

        nw_f_intrange, nw_s_intrange = crop_xrange(nw_f_complete, nw_s_complete, int0, int1)
        nw_f_calcrange, nw_s_calcrange = crop_xrange(nw_f_complete, nw_s_complete, tgt0, tgt1)
        
        f0_int, f1_int = min(nw_f_intrange), max(nw_f_intrange)
        
        integral_intrange = integrate(nw_f_intrange, nw_s_intrange)
        integral_calcrange = integrate(nw_f_calcrange, nw_s_calcrange)
        db_total = get_optimum_rl(integral_intrange, min(nw_f_intrange), max(nw_f_intrange))
        db_current = get_optimum_rl(integral_calcrange, tgt0, tgt1)
        db_optimized = get_optimum_rl(integral_intrange, tgt0, tgt1)

        self.fig.clf()
        self.plot = self.fig.add_subplot(111)

        self.plot.plot(nw_f_intrange/1e9, 20*np.log10(np.abs(nw_s_intrange)), '-', label=f'S{port}{port}')
        self.plot.plot([f0_int/1e9,f1_int/1e9], [db_total,db_total], ':', label=f'Current avg. RL (integration range): {db_total:+.3g} dB')
        self.plot.plot([tgt0/1e9,tgt1/1e9], [db_current,db_current], '--', label=f'Current avg. RL (target range): {db_current:+.3g} dB')
        self.plot.plot([tgt0/1e9,tgt1/1e9], [db_optimized,db_optimized], '-', label=f'Achievable avg. RL (target range): {db_optimized:+.3g} dB')
        self.plot.set_xlabel('f / GHz')
        self.plot.set_ylabel('RL / dB')
        self.plot.legend()

        self.canvas.draw()
