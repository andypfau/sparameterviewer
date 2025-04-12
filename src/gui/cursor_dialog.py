from .cursor_dialog_ui import CursorDialogUi
from .help import show_help
from typing import Callable
from lib import PlotData


class CursorDialog(CursorDialogUi):

    OFF = '[cursor turned off]'

    def __init__(self, parent):
        super().__init__(parent)
        self._update_callback: Callable = None
        self.plots: list[PlotData] = []
        self._currently_shown = False
    

    def show_dialog(self, plots: list[PlotData], callback: Callable):
        if not self._currently_shown:
            self._update_callback = callback
            self.plots = plots
            self.ui_set_trace_list([CursorDialog.OFF, *[plot.name for plot in plots]])
            self.ui_trace1 = CursorDialog.OFF
            self.ui_trace2 = CursorDialog.OFF
            self._currently_shown = True
        super().show()
    
    
    def is_currently_shown(self):
        return self._currently_shown


    def update(self):

        if self.ui_trace1 != CursorDialog.OFF:
            trace_name_1 = self.ui_trace1
        else:
            trace_name_1 = None

        if self.ui_trace1 != CursorDialog.OFF:
            trace_name_1 = self.ui_trace1
        else:
            trace_name_1 = None

        self._update_callback(self)
        
    
    def update_readout(self, readout: str):
        self.ui_set_readout(readout)


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














    def on_cursor_select(self):
        self.update()


    def on_cursor_select(self):
        self.update()


    def on_trace1_change(self):
        self.update()


    def on_trace2_change(self):
        self.update()


    def on_auto_cursor_changed(self):
        self.update()


    def on_auto_trace_changed(self):
        self.update()


    def on_syncx_changed(self):
        self.update()


    def on_help(self):
        show_help('tools.md')

    def on_close(self):
        self._currently_shown = False
