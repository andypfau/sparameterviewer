from lib import AppGlobal

from .settings import Settings
from .settings_dialog_pygubu import PygubuApp


WINDOWS = [
    'boxcar', 'triang', 'parzen', 'bohman', 'blackman', 'nuttall',
    'blackmanharris', 'flattop', 'bartlett', 'barthann',
    'hamming', 'kaiser', 'gaussian', 'general_hamming',
    'chebwin', 'cosine', 'hann', 'exponential', 'tukey', 'taylor',
    'dpss', 'lanczos']



# extend auto-generated UI code
class SparamviewerSettingsDialog(PygubuApp):
    def __init__(self, master, callback):
        super().__init__(master)
        self.callback = callback
        
        self.window_map = {}
        window_list = []
        win_sel = 0
        for i,win in enumerate(sorted(WINDOWS)):
            self.window_map[i] = win
            window_list.append(win[0].upper() + win[1:].replace('_',' '))
            if win == Settings.window_type:
                win_sel = i
        self.combobox_window['values'] = window_list
        self.combobox_window.current(win_sel)

        self.win_param.set(Settings.window_arg)
        self.shift_ps.set(Settings.tdr_shift/1e-12)
        
        AppGlobal.set_toplevel_icon(self.toplevel_settings)

    def on_win_sel(self, event=None):
        win_id = self.combobox_window.current()
        typ = self.window_map[win_id]
        Settings.window_type = typ
        self.invoke_callback()

    def on_change_shift(self, event=None):
        print(event)
        Settings.window_arg = self.win_param.get()
        self.invoke_callback()

    def on_change_arg(self, event=None):
        Settings.tdr_shift = self.shift_ps.get()*1e-12
        self.invoke_callback()

    def invoke_callback(self):
        win_id = self.combobox_window.current()
        typ = self.window_map[win_id]
        arg = self.win_param.get()
        shift = self.shift_ps.get()*1e-12
        self.callback(typ, arg, shift)
