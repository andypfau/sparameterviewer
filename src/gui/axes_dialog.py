from .axes_dialog_ui import AxesDialogUi
from lib import parse_si_range, format_si_range
from typing import Callable


class AxesDialog(AxesDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
        self.callback: Callable = None
        self.x0, self.x1, self.xauto = 0, 0, False
        self.y0, self.y1, self.yauto = 0, 0, False
        self.ui_set_x_presets([
            format_si_range(any, any, allow_total_wildcard=True),
            format_si_range(0, 10e9),
        ])
        self.ui_set_y_presets([
            format_si_range(any, any, allow_total_wildcard=True),
            format_si_range(-25, +25),
            format_si_range(-25, +3),
            format_si_range(-50, +3),
            format_si_range(-100, +3),
        ])
    

    def show_modal_dialog(self, x0, x1, xauto, y0, y1, yauto, callback):
        self.x0, self.x1, self.xauto = x0, x1, xauto
        self.y0, self.y1, self.yauto = y0, y1, yauto
        self.callback = callback
        self.update_ui_from_vars()
        super().ui_show_modal()


    def update_ui_from_vars(self):
        if self.xauto:
            self.ui_x = format_si_range(any, any, allow_total_wildcard=True)
        else:
            self.ui_x = format_si_range(self.x0, self.x1)
        if self.yauto:
            self.ui_y = format_si_range(any, any, allow_total_wildcard=True)
        else:
            self.ui_y = format_si_range(self.y0, self.y1)
        

    def trigger_callback(self):
        if not self.callback:
            return
        self.callback(self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto)


    def on_x_change(self):
        (x0,x1) = parse_si_range(self.ui_x, wildcard_low=any, wildcard_high=any, allow_both_wildcards=True, allow_individual_wildcards=False)
        if (x0,x1) == (None,None):
            self.ui_inidicate_x_error(True)
            return
        elif (x0,x1) == (any,any):
            self.xauto = True
        else:
            self.x0, self.x1, self.xauto = x0, x1, False
        self.trigger_callback()
        self.ui_inidicate_x_error(False)


    def on_y_change(self):
        (y0,y1) = parse_si_range(self.ui_y, wildcard_low=any, wildcard_high=any, allow_both_wildcards=True, allow_individual_wildcards=False)
        if (y0,y1) == (None,None):
            self.ui_inidicate_y_error(True)
            return
        elif (y0,y1) == (any,any):
            self.yauto = True
        else:
            self.y0, self.y1, self.yauto = y0, y1, False
        self.trigger_callback()
        self.ui_inidicate_y_error(False)
