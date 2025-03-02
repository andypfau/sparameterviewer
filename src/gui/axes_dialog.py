from lib import AppGlobal, parse_si_range, format_si_range

import tkinter as tk

from .settings import Settings
from .axes_dialog_pygubuui import PygubuAppUI



def format(value: float) -> str:
    return f'{value:.3g}'

def parse(text: str) -> float:
    try:
        return float(text)
    except:
        return None



# extend auto-generated UI code
class SparamviewerAxesDialog(PygubuAppUI):
    def __init__(self, master, callback, x0, x1, xauto, y0, y1, yauto):
        super().__init__(master)
        self.callback = callback
        
        AppGlobal.set_toplevel_icon(self.toplevel_axes)

        self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto = x0, x1, xauto, y0, y1, yauto

        self.combo_x['values'] = (
            format_si_range(any, any, allow_total_wildcard=True),
            format_si_range(self.x0, self.x1),
        )
        self.combo_y['values'] = (
            format_si_range(any, any, allow_total_wildcard=True),
            format_si_range(self.y0, self.y1),
            format_si_range(-21, +3),
            format_si_range(-41, +11),
            format_si_range(-101, +31),
        )

        self.update_ui_vars_from_status_vars()
        
        self.toplevel_axes.grab_set()  # modal dialog


    def update_vars(self, x0, x1, xauto, y0, y1, yauto):
        self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto = x0, x1, xauto, y0, y1, yauto
        self.update_ui_vars_from_status_vars()
    

    def update_ui_vars_from_status_vars(self):
        
        if self.xauto:
            self.x_var.set(format_si_range(any, any, allow_total_wildcard=True))
        else:
            self.x_var.set(format_si_range(self.x0, self.x1))
        
        if self.yauto:
            self.y_var.set(format_si_range(any, any, allow_total_wildcard=True))
        else:
            self.y_var.set(format_si_range(self.y0, self.y1))


    def trigger_callback(self):
        self.callback(self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto)


    def on_x(self, text, condition):
        x0, x1 = parse_si_range(text, wildcard_low=any, wildcard_high=any, allow_individual_wildcards=False, allow_both_wildcards=True)
        if x0 is any and x1 is any:
            self.xauto = True
            self.trigger_callback()
        elif x0 is not None and x1 is not None:
            self.x0, self.x1, self.xauto = x0, x1, False
            self.trigger_callback()
        return True


    def on_y(self, text, condition):
        y0, y1 = parse_si_range(text, wildcard_low=any, wildcard_high=any, allow_individual_wildcards=False, allow_both_wildcards=True)
        if y0 is any and y1 is any:
            self.yauto = True
            self.trigger_callback()
        elif y0 is not None and y1 is not None:
            self.y0, self.y1, self.yauto = y0, y1, False
            self.trigger_callback()
        return True
