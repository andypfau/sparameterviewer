from lib import AppGlobal
from tkinter import ttk, filedialog

from .settings import Settings
from .settings_dialog_pygubuui import PygubuAppUI
from lib.utils import is_windows
import matplotlib.pyplot as pyplot

import os


WINDOWS = [
    'boxcar', 'triang', 'parzen', 'bohman', 'blackman', 'nuttall',
    'blackmanharris', 'flattop', 'bartlett', 'barthann',
    'hamming', 'kaiser', 'gaussian', 'general_hamming',
    'chebwin', 'cosine', 'hann', 'exponential', 'tukey', 'taylor',
    'dpss', 'lanczos']



# extend auto-generated UI code
class SparamviewerSettingsDialog(PygubuAppUI):
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
        self.impedance.set('impedance' if Settings.tdr_impedance else 'gamma')
        
        AppGlobal.set_toplevel_icon(self.toplevel_settings)

        def on_window_change(var, index, mode):
            Settings.window_arg = self.win_param.get()
            Settings.tdr_shift = self.shift_ps.get()*1e-12
            Settings.tdr_impedance = self.impedance.get() == 'impedance'
            self.callback()
        
        self.win_param.trace_add('write', on_window_change)
        self.shift_ps.trace_add('write', on_window_change)
        self.impedance.trace_add('write', on_window_change)

        def on_editor_change(var, index, mode):
            Settings.ext_editor_cmd = self.ext_ed.get()

        self.ext_ed.trace_add('write', on_editor_change)

        self.ttk_style = ttk.Style(self.toplevel_settings)
        self.theme_map = {}
        themes = []
        theme_sel = 0
        for i,name in enumerate(self.ttk_style.theme_names()):
            self.theme_map[i] = name
            themes.append(name)
            if Settings.ttk_theme == name:
                theme_sel = i
        self.combobox_theme['values'] = themes
        if Settings.ttk_theme != '':
            self.combobox_theme.current(theme_sel)

        self.combobox_plotstyle['values'] = pyplot.style.available
        if Settings.plot_style in pyplot.style.available:
            self.combobox_plotstyle.current(pyplot.style.available.index(Settings.plot_style))
        

        def on_comment_expr_change(var, index, mode):
            Settings.comment_existing_expr = self.comment_existing_expr.get()=='comment'
        self.comment_existing_expr.set('comment' if Settings.comment_existing_expr else 'keep')
        self.comment_existing_expr.trace_add('write', on_comment_expr_change)
        
        self.ext_ed.set(Settings.ext_editor_cmd)
        

    def run(self, focus: bool = True):
        if focus:
            self.mainwindow.focus_force()
        super().run()
    

    def on_win_sel(self, event=None):
        win_id = self.combobox_window.current()
        typ = self.window_map[win_id]
        Settings.window_type = typ
        self.callback()
    

    def on_theme_sel(self, event=None):
        try:
            theme = self.theme_map[self.combobox_theme.current()]
            Settings.ttk_theme = theme
            Settings.save()
            self.ttk_style.theme_use(theme)
        except:
            pass
    

    def on_plotstyle_sel(self, event=None):
        Settings.plot_style = pyplot.style.available[self.combobox_plotstyle.current()]
        Settings.save()
        pyplot.style.use(Settings.plot_style)

    
    def on_sel_ext_editor(self):
        SparamviewerSettingsDialog.let_user_select_ext_editor()
        self.ext_ed.set(Settings.ext_editor_cmd or '')
    
    @staticmethod
    def let_user_select_ext_editor() -> str:
        kwargs = {}
        if is_windows:
            kwargs['filetypes'] = (('Executables','*.exe'),('All Files','*'))
        else:
            kwargs['filetypes'] = (('All Files','*'))
        if Settings.ext_editor_cmd:
            if os.path.exists(Settings.ext_editor_cmd):
                kwargs['initialdir'] = os.path.split(Settings.ext_editor_cmd)[0]
                kwargs['initialfile'] = Settings.ext_editor_cmd
        filename = filedialog.askopenfilename(title='Select External Editor', multiple=False, **kwargs)
        if filename:
            Settings.ext_editor_cmd = filename
            Settings.save()
            return filename
        else:
            return None
