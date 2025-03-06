#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper


class PygubuAppUI:
    def __init__(self, master=None, data_pool=None):
        # build ui
        self.toplevel_main = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_main.configure(height=200, width=200)
        self.toplevel_main.overrideredirect("False")
        self.toplevel_main.title("S-Parameter Viewer")
        self.frame_5 = ttk.Frame(self.toplevel_main)
        self.frame_5.configure(height=200, width=200)
        self.panedwindow_1 = ttk.Panedwindow(self.frame_5, orient="vertical")
        self.panedwindow_1.configure(height=600, width=800)
        self.frame_3 = ttk.Frame(self.panedwindow_1)
        self.frame_3.configure(height=150, padding=5, width=150)
        self.frame_plot = ttk.Frame(self.frame_3)
        self.frame_plot.configure(height=150, width=150)
        self.frame_plot.pack(expand=True, fill="both", side="top")
        self.frame_3.pack(expand=True, fill="both", side="top")
        self.panedwindow_1.add(self.frame_3, weight="3")
        self.frame_11 = ttk.Frame(self.panedwindow_1)
        self.frame_11.configure(height=150, width=150)
        self.frame_2 = ttk.Frame(self.frame_11)
        self.frame_2.configure(height=50, padding=5, width=150)
        self.combobox_mode = ttk.Combobox(self.frame_2)
        self.combobox_mode.configure(state="readonly")
        self.combobox_mode.pack(expand=True, fill="x", side="left")
        self.combobox_mode.bind(
            "<<ComboboxSelected>>",
            self.on_select_plotmode,
            add="")
        self.combobox_unit = ttk.Combobox(self.frame_2)
        self.combobox_unit.configure(state="readonly")
        self.combobox_unit.pack(padx=5, side="right")
        self.combobox_unit.bind(
            "<<ComboboxSelected>>",
            self.on_select_plotunit,
            add="")
        self.frame_2.pack(expand=False, fill="x", side="top")
        self.frame_6 = ttk.Frame(self.frame_11)
        self.frame_6.configure(height=200, width=200)
        self.entry_err = ttk.Entry(self.frame_6)
        self.eval_err_msg = tk.StringVar()
        self.entry_err.configure(
            state="readonly",
            textvariable=self.eval_err_msg)
        self.entry_err.pack(expand=False, fill="x", side="bottom")
        self.frame_6.pack(
            expand=False,
            fill="x",
            ipadx=5,
            padx=5,
            side="bottom")
        self.frame_1 = ttk.Frame(self.frame_11)
        self.frame_1.configure(height=150, padding=5, width=150)
        self.notebook_mode = ttk.Notebook(self.frame_1)
        self.notebook_mode.configure(height=200, width=200)
        self.frame_4 = ttk.Frame(self.notebook_mode)
        self.frame_4.configure(height=200, padding=5, width=200)
        self.frame_7 = ttk.Frame(self.frame_4)
        self.frame_7.configure(height=200, padding=5, width=200)
        self.entry_6 = ttk.Entry(self.frame_7)
        self.search_str = tk.StringVar()
        self.entry_6.configure(textvariable=self.search_str)
        self.entry_6.pack(fill="x", pady=2, side="top")
        self.entry_6.bind("<KeyPress>", self.on_search_press_key, add="")
        self.scrollbarhelper_1 = ScrollbarHelper(
            self.frame_7, scrolltype="vertical")
        self.scrollbarhelper_1.configure(usemousewheel=True)
        self.treeview_files = ttk.Treeview(self.scrollbarhelper_1.container)
        self.treeview_files.configure(selectmode="extended")
        self.treeview_files.pack(expand=True, fill="both", side="top")
        self.treeview_files.bind(
            "<<TreeviewSelect>>",
            self.on_select_file,
            add="")
        self.scrollbarhelper_1.add_child(self.treeview_files)
        self.scrollbarhelper_1.pack(expand=True, fill="both", side="top")
        self.frame_7.pack(expand=True, fill="both", side="top")
        self.frame_4.pack(expand=True, fill="both", side="bottom")
        self.notebook_mode.add(self.frame_4, text='Files/Basic')
        self.frame_8 = ttk.Frame(self.notebook_mode)
        self.frame_8.configure(height=150, padding=5, width=200)
        self.frame2 = ttk.Frame(self.frame_8)
        self.frame2.configure(height=150, width=200)
        self.button_use_expr = ttk.Button(self.frame2)
        self.button_use_expr.configure(text='Plot (F5)')
        self.button_use_expr.pack(fill="x", side="top")
        self.button_use_expr.configure(command=self.on_use_expr)
        self.button_use_expr.bind("<1>", self.callback, add="")
        self.button_gen_expr = ttk.Button(self.frame2)
        self.button_gen_expr.configure(text='Template...')
        self.button_gen_expr.pack(fill="x", pady=5, side="top")
        self.button1 = ttk.Button(self.frame2)
        self.button1.configure(text='Help')
        self.button1.pack(fill="x", pady=15, side="top")
        self.button1.configure(command=self.on_expr_help)
        self.frame2.pack(anchor="n", side="left")
        self.scrollbarhelper_2 = ScrollbarHelper(
            self.frame_8, scrolltype="both")
        self.scrollbarhelper_2.configure(usemousewheel=False)
        self.text_expr = tk.Text(self.scrollbarhelper_2.container)
        self.text_expr.configure(height=5, width=50)
        self.text_expr.pack(expand=True, fill="both", side="top")
        self.scrollbarhelper_2.add_child(self.text_expr)
        self.scrollbarhelper_2.pack(
            expand=True, fill="both", padx=5, side="top")
        self.frame_8.pack(side="top")
        self.notebook_mode.add(self.frame_8, text='Expressions')
        self.notebook_mode.pack(expand=True, fill="both", side="top")
        self.notebook_mode.bind(
            "<<NotebookTabChanged>>",
            self.on_tab_change,
            add="")
        self.frame_1.pack(expand=True, fill="both", side="bottom")
        self.frame_11.pack(expand=True, fill="both", side="top")
        self.panedwindow_1.add(self.frame_11, weight="1")
        self.panedwindow_1.pack(expand=True, fill="both", side="top")
        self.frame_5.pack(expand=True, fill="both", side="top")
        self.menu_2 = tk.Menu(self.toplevel_main)
        self.menu_2.configure(cursor="arrow")
        self.topmenu_main_files = tk.Menu(self.menu_2)
        self.menu_2.add(tk.CASCADE, menu=self.topmenu_main_files, label='File')
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+O",
            command=self.on_open_dir,
            label='Open Directory...')
        self.topmenu_main_files.add(
            "command",
            command=self.on_append_dir,
            label='Append Directory...')
        self.menuitem_recent = tk.Menu(self.topmenu_main_files, tearoff=False)
        self.topmenu_main_files.add(
            tk.CASCADE,
            menu=self.menuitem_recent,
            label='Recent Directories')
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+F5",
            command=self.on_reload_all_files,
            label='Reload All Files')
        self.topmenu_main_files.add("separator")
        self.topmenu_main_files.add(
            "command",
            command=self.on_save_plot_graphic,
            label='Save Plot Image...')
        self.topmenu_main_files.add("separator")
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+I",
            command=self.on_click_info,
            label='File Info')
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+T",
            command=self.on_view_tabular,
            label='View Tabular Data')
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+E",
            command=self.on_click_open_externally,
            label='Open File Externally')
        self.topmenu_main_files.add("separator")
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+L",
            command=self.on_load_expr,
            label='Load Expressions...')
        self.topmenu_main_files.add(
            "command",
            accelerator="Ctrl+S",
            command=self.on_save_expr,
            label='Save Expressions...')
        self.topmenu_main_files.add("separator")
        self.topmenu_main_files.add(
            "command", command=self.on_exit_cmd, label='Exit')
        self.submenu_2 = tk.Menu(self.menu_2)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_2, label='Plot')
        self.show_legend = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_show_legend,
            label='Show Legend',
            offvalue=0,
            onvalue=1,
            variable=self.show_legend)
        self.hide_single_legend = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_hide_single_legend,
            label='Hide Single-Item Legend',
            offvalue=0,
            onvalue=1,
            variable=self.hide_single_legend)
        self.short_legend = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_short_legend,
            label='Shorten Legend Items',
            offvalue=0,
            onvalue=1,
            variable=self.short_legend)
        self.submenu_2.add("separator")
        self.submenu_2.add(
            "command",
            command=self.on_copy_plot_image_to_clipboard,
            label='Copy Image to Clipboard')
        self.submenu_2.add("separator")
        self.logf = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_change_logf,
            label='Logarithmic Frequency',
            offvalue=0,
            onvalue=1,
            variable=self.logf)
        self.submenu_2.add("separator")
        self.lock_plot_xaxis = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_lock_xaxis,
            label='Lock X-Axis',
            offvalue=0,
            onvalue=1,
            variable=self.lock_plot_xaxis)
        self.lock_plot_yaxis = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_lock_yaxis,
            label='Lock Y-Axis',
            offvalue=0,
            onvalue=1,
            variable=self.lock_plot_yaxis)
        self.submenu_2.add(
            "command",
            command=self.on_lock_axes,
            label='Lock both axes')
        self.submenu_2.add(
            "command",
            command=self.on_unlock_axes,
            label='Unlock both axes')
        self.submenu_2.add(
            "command",
            command=self.on_rescale_locked_axes,
            label='Re-scale locked axes')
        self.submenu_2.add(
            "command",
            command=self.on_manual_axes,
            label='Manual axes...')
        self.submenu_2.add("separator")
        self.plot_mark_points = tk.StringVar()
        self.submenu_2.add(
            "checkbutton",
            command=self.on_mark_points,
            label='Mark Points',
            offvalue=0,
            onvalue=1,
            variable=self.plot_mark_points)
        self.submenu_2.add("separator")
        self.submenu_2.add(
            "command",
            accelerator="F5",
            command=self.on_use_expr,
            label='Update Plot From Expressions')
        self.submenu_3 = tk.Menu(self.menu_2)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_3, label='Tools')
        self.submenu_3.add(
            "command",
            accelerator="F3",
            command=self.on_cursor_cmd,
            label='Trace Cursors')
        self.submenu_3.add(
            "command",
            command=self.on_call_optrlcalc,
            label='Return Loss Integrator')
        self.submenu_3.add("separator")
        self.submenu_3.add(
            "command",
            command=self.on_show_error_log_click,
            label='Error Log')
        self.submenu_3.add("separator")
        self.submenu_3.add(
            "command",
            command=self.on_open_settings_click,
            label='Settings')
        self.submenu_4 = tk.Menu(self.menu_2, tearoff=False)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_4, label='Help')
        self.submenu_4.add(
            "command",
            accelerator="F1",
            command=self.on_menu_help,
            label='Help')
        self.submenu_4.add(
            "command",
            command=self.on_menu_about,
            label='About')
        self.toplevel_main.configure(menu=self.menu_2)

        # Main widget
        self.mainwindow = self.toplevel_main

    def run(self):
        self.mainwindow.mainloop()

    def on_select_plotmode(self, event=None):
        pass

    def on_select_plotunit(self, event=None):
        pass

    def on_search_press_key(self, event=None):
        pass

    def on_select_file(self, event=None):
        pass

    def on_use_expr(self):
        pass

    def callback(self, event=None):
        pass

    def on_expr_help(self):
        pass

    def on_tab_change(self, event=None):
        pass

    def on_open_dir(self):
        pass

    def on_append_dir(self):
        pass

    def on_reload_all_files(self):
        pass

    def on_save_plot_graphic(self):
        pass

    def on_click_info(self):
        pass

    def on_view_tabular(self):
        pass

    def on_click_open_externally(self):
        pass

    def on_load_expr(self):
        pass

    def on_save_expr(self):
        pass

    def on_exit_cmd(self):
        pass

    def on_show_legend(self):
        pass

    def on_hide_single_legend(self):
        pass

    def on_short_legend(self):
        pass

    def on_copy_plot_image_to_clipboard(self):
        pass

    def on_change_logf(self):
        pass

    def on_lock_xaxis(self):
        pass

    def on_lock_yaxis(self):
        pass

    def on_lock_axes(self):
        pass

    def on_unlock_axes(self):
        pass

    def on_rescale_locked_axes(self):
        pass

    def on_manual_axes(self):
        pass

    def on_mark_points(self):
        pass

    def on_cursor_cmd(self):
        pass

    def on_call_optrlcalc(self):
        pass

    def on_show_error_log_click(self):
        pass

    def on_open_settings_click(self):
        pass

    def on_menu_help(self):
        pass

    def on_menu_about(self):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
