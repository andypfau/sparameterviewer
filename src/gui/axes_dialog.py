from lib import AppGlobal

import tkinter as tk

from .settings import Settings
from .axes_dialog_pygubu import PygubuApp



def format(value: float) -> str:
    return f'{value:.3g}'

def parse(text: str) -> float:
    try:
        return float(text)
    except:
        return None



# extend auto-generated UI code
class SparamviewerAxesDialog(PygubuApp):
    def __init__(self, master, callback, x0, x1, xauto, y0, y1, yauto):
        super().__init__(master)
        self.callback = callback

        self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto = x0, x1, xauto, y0, y1, yauto

        self.x0_var.set(format(x0))
        self.x1_var.set(format(x1))
        self.xauto_var.set('auto' if xauto else 'manual')
        self.y0_var.set(format(y0))
        self.y1_var.set(format(y1))
        self.yauto_var.set('auto' if yauto else 'manual')
        
        def on_auto_change(var, index, mode):
            self.xauto = self.xauto_var.get() == 'auto'
            self.yauto = self.yauto_var.get() == 'auto'
            self.trigger_callback()
        self.xauto_var.trace('w', on_auto_change)
        self.yauto_var.trace('w', on_auto_change)


    def trigger_callback(self):
        self.callback(self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto)


    def _handle_text_change(self, text, trigger, text_var, default_value):
        update_ui = trigger == 'focusout'
        value = parse(text)
        ok = value is not None
        if update_ui:
            text_var.set(format(value if ok else default_value))
        return ok, value


    def on_x0(self, text, trigger):
        ok, value = self._handle_text_change(text, trigger, self.x0_var, self.x0)
        if ok:
            self.x0 = value
            self.trigger_callback()
        return True

    def on_x1(self, text, trigger):
        ok, value = self._handle_text_change(text, trigger, self.x1_var, self.x1)
        if ok:
            self.x1 = value
            self.trigger_callback()
        return True

    def on_y0(self, text, trigger):
        ok, value = self._handle_text_change(text, trigger, self.y0_var, self.y0)
        if ok:
            self.y0 = value
            self.trigger_callback()
        return True

    def on_y1(self, text, trigger):
        ok, value = self._handle_text_change(text, trigger, self.y1_var, self.y1)
        if ok:
            self.y1 = value
            self.trigger_callback()
        return True
