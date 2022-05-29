import pathlib
import pygubu
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "sparamviewer_pygubu.ui"


class SparamviewerPygubuApp:
    def __init__(self, master=None):
        # build ui
        self.toplevel_main = tk.Tk() if master is None else tk.Toplevel(master)
        self.frame_5 = ttk.Frame(self.toplevel_main)
        self.panedwindow_1 = ttk.Panedwindow(self.frame_5, orient='vertical')
        self.frame_3 = ttk.Frame(self.panedwindow_1)
        self.frame_plot = ttk.Frame(self.frame_3)
        self.frame_plot.configure(height='150', width='150')
        self.frame_plot.pack(expand='true', fill='both', side='top')
        self.frame_3.configure(height='150', padding='5', width='150')
        self.frame_3.pack(expand='true', fill='both', side='top')
        self.panedwindow_1.add(self.frame_3, weight='3')
        self.frame_11 = ttk.Frame(self.panedwindow_1)
        self.frame_2 = ttk.Frame(self.frame_11)
        self.combobox_mode = ttk.Combobox(self.frame_2)
        self.combobox_mode.configure(state='readonly')
        self.combobox_mode.pack(expand='true', fill='x', side='left')
        self.combobox_mode.bind('<<ComboboxSelected>>', self.on_select_plotmode, add='')
        self.combobox_unit = ttk.Combobox(self.frame_2)
        self.combobox_unit.configure(state='readonly')
        self.combobox_unit.pack(padx='5', side='right')
        self.combobox_unit.bind('<<ComboboxSelected>>', self.on_select_plotmode, add='')
        self.frame_2.configure(height='50', padding='5', width='150')
        self.frame_2.pack(expand='false', fill='x', side='top')
        self.frame_1 = ttk.Frame(self.frame_11)
        self.notebook_mode = ttk.Notebook(self.frame_1)
        self.frame_4 = ttk.Frame(self.notebook_mode)
        self.frame_7 = ttk.Frame(self.frame_4)
        self.scrollbarhelper_1 = ScrollbarHelper(self.frame_7, scrolltype='vertical')
        self.treeview_files = ttk.Treeview(self.scrollbarhelper_1.container)
        self.treeview_files.pack(expand='true', fill='both', side='top')
        self.treeview_files.bind('<<TreeviewSelect>>', self.on_select_file, add='')
        self.scrollbarhelper_1.add_child(self.treeview_files)
        self.scrollbarhelper_1.configure(usemousewheel=True)
        self.scrollbarhelper_1.pack(expand='true', fill='both', side='top')
        self.frame_7.configure(height='200', padding='5', width='200')
        self.frame_7.pack(expand='true', fill='both', side='top')
        self.frame_4.configure(height='200', padding='5', width='200')
        self.frame_4.pack(expand='true', fill='both', side='bottom')
        self.notebook_mode.add(self.frame_4, text='Files/Basic')
        self.frame_8 = ttk.Frame(self.notebook_mode)
        self.frame2 = ttk.Frame(self.frame_8)
        self.button_gen = ttk.Button(self.frame2)
        self.button_gen.configure(text='Plot (F5)')
        self.button_gen.pack(fill='x', side='top')
        self.button_gen.configure(command=self.on_use_expr)
        self.button_gen.bind('<1>', self.callback, add='')
        self.button1 = ttk.Button(self.frame2)
        self.button1.configure(text='Generate')
        self.button1.pack(fill='x', pady='5', side='top')
        self.button1.configure(command=self.on_gen_expr)
        self.button_expr_help = ttk.Button(self.frame2)
        self.button_expr_help.configure(text='Help')
        self.button_expr_help.pack(pady='10', side='top')
        self.button_expr_help.configure(command=self.on_expr_help)
        self.frame2.configure(height='200', width='200')
        self.frame2.pack(anchor='n', side='left')
        self.scrollbarhelper_2 = ScrollbarHelper(self.frame_8, scrolltype='both')
        self.text_expr = tk.Text(self.scrollbarhelper_2.container)
        self.text_expr.configure(height='10', width='50')
        self.text_expr.pack(expand='true', fill='both', side='top')
        self.scrollbarhelper_2.add_child(self.text_expr)
        self.scrollbarhelper_2.configure(usemousewheel=False)
        self.scrollbarhelper_2.pack(expand='true', fill='both', padx='5', side='top')
        self.frame_6 = ttk.Frame(self.frame_8)
        self.entry_err = ttk.Entry(self.frame_6)
        self.eval_err_msg = tk.StringVar(value='')
        self.entry_err.configure(state='readonly', textvariable=self.eval_err_msg)
        self.entry_err.pack(expand='false', fill='x', side='top')
        self.frame_6.configure(height='200', width='200')
        self.frame_6.pack(expand='false', fill='x', ipadx='5', padx='5', side='bottom')
        self.frame_8.configure(height='200', padding='5', width='200')
        self.frame_8.pack(side='top')
        self.notebook_mode.add(self.frame_8, text='Expressions')
        self.notebook_mode.configure(height='200', width='200')
        self.notebook_mode.pack(expand='true', fill='both', side='top')
        self.notebook_mode.bind('<<NotebookTabChanged>>', self.on_tab_change, add='')
        self.frame_1.configure(height='150', padding='5', width='150')
        self.frame_1.pack(expand='true', fill='both', side='bottom')
        self.frame_11.configure(height='150', width='150')
        self.frame_11.pack(expand='true', fill='both', side='top')
        self.panedwindow_1.add(self.frame_11, weight='1')
        self.panedwindow_1.configure(height='600', width='800')
        self.panedwindow_1.pack(expand='true', fill='both', side='top')
        self.frame_5.configure(height='200', width='200')
        self.frame_5.pack(expand='true', fill='both', side='top')
        self.menu_2 = tk.Menu(self.toplevel_main)
        self.submenu_1 = tk.Menu(self.menu_2)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_1, label='File')
        self.mi_command_1 = 1
        self.submenu_1.add('command', accelerator='Ctrl+O', label='Open Directory...')
        self.submenu_1.entryconfigure(self.mi_command_1, command=self.on_open_dir)
        self.mi_command_export = 2
        self.submenu_1.add('command', accelerator='Ctrl+E', label='Export Trace Data...')
        self.submenu_1.entryconfigure(self.mi_command_export, command=self.on_export)
        self.mi_separator3 = 3
        self.submenu_1.add('separator')
        self.mi_command_info = 4
        self.submenu_1.add('command', accelerator='F1', label='File Info...')
        self.submenu_1.entryconfigure(self.mi_command_info, command=self.on_click_info)
        self.mi_separator_1 = 5
        self.submenu_1.add('separator')
        self.mi_command_loadexpr = 6
        self.submenu_1.add('command', accelerator='Ctrl+L', label='Load Expressions...')
        self.submenu_1.entryconfigure(self.mi_command_loadexpr, command=self.on_load_expr)
        self.mi_command_saveexpr = 7
        self.submenu_1.add('command', accelerator='Ctrl+S', label='Save Expressions...')
        self.submenu_1.entryconfigure(self.mi_command_saveexpr, command=self.on_save_expr)
        self.mi_separator_3 = 8
        self.submenu_1.add('separator')
        self.mi_command_exit = 9
        self.submenu_1.add('command', label='Exit')
        self.submenu_1.entryconfigure(self.mi_command_exit, command=self.on_exit_cmd)
        self.submenu_2 = tk.Menu(self.menu_2)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_2, label='Plot')
        self.show_legend = tk.StringVar(value='')
        self.mi_checkbutton_showlegend = 1
        self.submenu_2.add('checkbutton', label='Show Legend', offvalue='0', onvalue='1', variable=self.show_legend)
        self.submenu_2.entryconfigure(self.mi_checkbutton_showlegend, command=self.on_show_legend)
        self.short_names = tk.StringVar(value='')
        self.mi_checkbutton_shortnames = 2
        self.submenu_2.add('checkbutton', label='Short Names', offvalue='0', onvalue='1', variable=self.short_names)
        self.submenu_2.entryconfigure(self.mi_checkbutton_shortnames, command=self.on_show_shortnames)
        self.always_show_names = tk.StringVar(value='')
        self.mi_checkbutton_alwaysnames = 3
        self.submenu_2.add('checkbutton', label='Always Show Names', offvalue='0', onvalue='1', variable=self.always_show_names)
        self.submenu_2.entryconfigure(self.mi_checkbutton_alwaysnames, command=self.on_show_names_always)
        self.logf = tk.StringVar(value='')
        self.mi_checkbutton_logf = 4
        self.submenu_2.add('checkbutton', label='Logarithmic Frequency', offvalue='0', onvalue='1', variable=self.logf)
        self.submenu_2.entryconfigure(self.mi_checkbutton_logf, command=self.on_change_logf)
        self.mi_separator1 = 5
        self.submenu_2.add('separator')
        self.mi_command_plot_expr = 6
        self.submenu_2.add('command', accelerator='F5', label='Update Plot From Expressions')
        self.submenu_2.entryconfigure(self.mi_command_plot_expr, command=self.on_use_expr)
        self.mi_separator2 = 7
        self.submenu_2.add('separator')
        self.mi_command_kaiser = 8
        self.submenu_2.add('command', label='TD Kaiser Argument...')
        self.submenu_2.entryconfigure(self.mi_command_kaiser, command=self.on_set_kaiser)
        self.submenu_3 = tk.Menu(self.menu_2)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_3, label='Tools')
        self.mi_command_cursors = 1
        self.submenu_3.add('command', accelerator='F3', label='Trace Cursors')
        self.submenu_3.entryconfigure(self.mi_command_cursors, command=self.on_cursor_cmd)
        self.mi_command_3 = 2
        self.submenu_3.add('command', label='Optimum RL Calculator')
        self.submenu_3.entryconfigure(self.mi_command_3, command=self.on_call_optrlcalc)
        self.submenu_4 = tk.Menu(self.menu_2, tearoff='false')
        self.menu_2.add(tk.CASCADE, menu=self.submenu_4, label='Help')
        self.mi_command_4 = 0
        self.submenu_4.add('command', label='About')
        self.submenu_4.entryconfigure(self.mi_command_4, command=self.on_menu_about)
        self.toplevel_main.configure(menu=self.menu_2)
        self.toplevel_main.configure(height='200', width='200')
        self.toplevel_main.overrideredirect('False')
        self.toplevel_main.title('S-Parameter Viewer')

        # Main widget
        self.mainwindow = self.toplevel_main
    
    def run(self):
        self.mainwindow.mainloop()

    def on_select_plotmode(self, event=None):
        pass

    def on_select_file(self, event=None):
        pass

    def on_use_expr(self):
        pass

    def callback(self, event=None):
        pass

    def on_gen_expr(self):
        pass

    def on_expr_help(self):
        pass

    def on_tab_change(self, event=None):
        pass

    def on_open_dir(self):
        pass

    def on_export(self):
        pass

    def on_click_info(self):
        pass

    def on_load_expr(self):
        pass

    def on_save_expr(self):
        pass

    def on_exit_cmd(self):
        pass

    def on_show_legend(self):
        pass

    def on_show_shortnames(self):
        pass

    def on_show_names_always(self):
        pass

    def on_change_logf(self):
        pass

    def on_set_kaiser(self):
        pass

    def on_cursor_cmd(self):
        pass

    def on_call_optrlcalc(self):
        pass

    def on_menu_about(self):
        pass


if __name__ == '__main__':
    app = SparamviewerPygubuApp()
    app.run()


