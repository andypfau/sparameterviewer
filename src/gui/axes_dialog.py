from .axes_dialog_ui import AxesDialogUi
from lib import parse_si_range, format_si_range


class AxesDialog(AxesDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
        self.callback = None
        self.x0, self.x1, self.xauto = 0, 0, False
        self.y0, self.y1, self.yauto = 0, 0, False
    

    def show_modal_dialog(self, x0, x1, xauto, y0, y1, yauto, callback):
        self.x0, self.x1, self.xauto = x0, x1, xauto
        self.y0, self.y1, self.yauto = y0, y1, yauto
        self.callback = callable
        self.update_ui_from_vars()
        super().ui_show_modal()


    def update_ui_from_vars(self):
        if self.xauto:
            self.ui_x = format_si_range(self.x0, self.x1)
        else:
            self.ui_x = format_si_range(any, any, allow_total_wildcard=True)
        if self.yauto:
            self.ui_y = format_si_range(self.y0, self.y1)
        else:
            self.ui_y = format_si_range(any, any, allow_total_wildcard=True)
        

    def trigger_callback(self):
        self.callback(self.x0, self.x1, self.xauto, self.y0, self.y1, self.yauto)


    def on_x_change(self):
        (x0,x1) = parse_si_range(self.ui_x, wildcard_low=any, wildcard_high=any, allow_both_wildcards=True, allow_individual_wildcards=False)
        if (x0,x1) == (None,None):
            self.ui_inidicate_x_error(True)
            return
        self.x0, self.x1 = x0, x1
        self.trigger_callback()
        self.ui_inidicate_x_error(False)


    def on_y_change(self):
        (y0,y1) = parse_si_range(self.ui_y, wildcard_low=any, wildcard_high=any, allow_both_wildcards=True, allow_individual_wildcards=False)
        if (y0,y1) == (None,None):
            self.ui_inidicate_y_error(True)
            return
        self.y0, self.y1 = y0, y1
        self.trigger_callback()
        self.ui_inidicate_y_error(False)
