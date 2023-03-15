#!/bin/python3

from tkinter import END
from .cursor_dialog_pygubu import SparamviewerPygubuApp
from lib import TkText, AppGlobal, PlotData

import os


# extend auto-generated UI code
class SparamviewerCursorDialog(SparamviewerPygubuApp):
    
    def __init__(self, master, plots: "list[PlotData]", callback: "callable"):
        super().__init__(master)
        
        AppGlobal.set_toplevel_icon(self.toplevel_cursor)

        def on_close():
            self.on_close()
            self.toplevel_cursor.destroy()
        self.toplevel_cursor.protocol("WM_DELETE_WINDOW", on_close)
        
        TkText.default_keyhandler(self.text_readout, readonly=True)

        self.callback = callback

        self.repopulate(plots)

        self.var_selected_cursor.set('cursor_1')
        self.var_auto_cursor.set('manual')
        self.var_auto_trace.set('auto')

        self.update()
    

    def on_close(self):
        self.callback(None)


    def on_sel_trace1(self, event=None):
        self.update()


    def on_sel_trace2(self, event=None):
        self.update()


    def on_auto_cursor(self):
        self.update()


    def on_auto_trace(self):
        self.update()


    def on_sel_cursor1(self):
        self.update()


    def on_sel_cursor2(self):
        self.update()


    def  on_sync_x(self):
        self.update()


    def repopulate(self, plots: "list[PlotData]"):
        
        self.plots = plots

        def populate(combobox, plots):
            values = ['[cursor turned off]']
            for plot in plots:
                values.append(plot.name)
            combobox['values'] = values
            combobox.current(0)

        populate(self.combobox_c1, plots)
        populate(self.combobox_c2, plots)


    def update(self):

        self.enable_cursor_1 = True if self.combobox_c1.current()>0 else False
        self.enable_cursor_2 = True if self.combobox_c2.current()>0 else False
        
        self.auto_select_cursor = self.var_auto_cursor.get()=='auto'
        self.selected_cursor_idx = 0 if self.var_selected_cursor.get()=='cursor_1' else 1

        self.auto_select_trace = self.var_auto_trace.get()=='auto'
        
        if self.enable_cursor_1:
            self.selected_trace_name_1 = list(self.plots)[self.combobox_c1.current() - 1].name
        else:
            self.selected_trace_name_1 = None
        if self.enable_cursor_2:
            self.selected_trace_name_2 = list(self.plots)[self.combobox_c2.current() - 1].name
        else:
            self.selected_trace_name_2 = None

        self.callback(self)
        
    
    def update_readout(self, readout: str):
        TkText.set_text(self.text_readout, readout)


    def set_cursor(self, selected_cursor_idx: int):
        self.var_selected_cursor.set(f'cursor_{selected_cursor_idx+1}')
        self.selected_cursor_idx = selected_cursor_idx


    def set_trace(self, trace_idx: int, selected_trace_name: str):

        if trace_idx==0:
            self.enable_cursor_1 = True
            self.selected_trace_name_1 = selected_trace_name
            combobox = self.combobox_c1
        elif trace_idx==1:
            self.enable_cursor_2 = True
            self.selected_trace_name_2 = selected_trace_name
            combobox = self.combobox_c2
        else:
            return

        for i,plot in enumerate(self.plots):
            if plot.name==selected_trace_name:
                combobox.current(i+1)
                break


    def clear(self):
        self.enable_cursor_1 = False
        self.selected_trace_name_1 = None
        self.combobox_c1.current(0)
        self.enable_cursor_2 = False
        self.selected_trace_name_2 = None
        self.combobox_c2.current(0)
        self.update_readout('')
