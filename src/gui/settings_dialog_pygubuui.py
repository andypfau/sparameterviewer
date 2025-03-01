#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk


class PygubuAppUI:
    def __init__(self, master=None, data_pool=None):
        # build ui
        self.toplevel_settings = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_settings.configure(height=200, width=200)
        self.toplevel_settings.title("Settings")
        self.frame_13 = ttk.Frame(self.toplevel_settings)
        self.frame_13.configure(height=200, padding=10, width=200)
        self.labelframe_5 = ttk.Labelframe(self.frame_13)
        self.labelframe_5.configure(
            height=200,
            padding=5,
            text='Time-Domain Transform',
            width=200)
        self.label_6 = ttk.Label(self.labelframe_5)
        self.label_6.configure(text='Window:')
        self.label_6.grid(column=0, row=0, sticky="w")
        self.combobox_window = ttk.Combobox(
            self.labelframe_5, name="combobox_window")
        self.combobox_window.grid(column=1, padx=5, pady=3, row=0, sticky="w")
        self.combobox_window.bind(
            "<<ComboboxSelected>>", self.on_win_sel, add="")
        self.label_7 = ttk.Label(self.labelframe_5)
        self.label_7.configure(text='Parameter:')
        self.label_7.grid(column=0, row=1, sticky="w")
        self.spinbox_3 = ttk.Spinbox(self.labelframe_5)
        self.win_param = tk.DoubleVar()
        self.spinbox_3.configure(
            from_=0,
            increment=0.1,
            textvariable=self.win_param,
            to=1000)
        self.spinbox_3.grid(column=1, padx=5, pady=3, row=1, sticky="w")
        self.spinbox_3.bind("<<Decrement>>", self.on_change_arg, add="")
        self.spinbox_3.bind("<<Increment>>", self.on_change_arg, add="")
        self.label_8 = ttk.Label(self.labelframe_5)
        self.label_8.configure(text='Shift:')
        self.label_8.grid(column=0, row=2, sticky="w")
        self.frame_12 = ttk.Frame(self.labelframe_5)
        self.frame_12.configure(height=200, width=200)
        self.spinbox_2 = ttk.Spinbox(self.frame_12)
        self.shift_ps = tk.DoubleVar()
        self.spinbox_2.configure(
            from_=-10000,
            increment=10,
            textvariable=self.shift_ps,
            to=10000)
        self.spinbox_2.pack(padx=5, pady=3, side="left")
        self.spinbox_2.bind("<<Decrement>>", self.on_change_shift, add="")
        self.spinbox_2.bind("<<Increment>>", self.on_change_shift, add="")
        self.label_10 = ttk.Label(self.frame_12)
        self.label_10.configure(text='ps')
        self.label_10.pack(side="top")
        self.frame_12.grid(column=1, row=2)
        self.checkbox_impedance = ttk.Checkbutton(
            self.labelframe_5, name="checkbox_impedance")
        self.impedance = tk.StringVar()
        self.checkbox_impedance.configure(
            offvalue="gamma",
            onvalue="impedance",
            text='Convert to Impedance',
            variable=self.impedance)
        self.checkbox_impedance.grid(
            column=1, padx=5, pady=3, row=3, sticky="w")
        self.checkbox_impedance.configure(command=self.on_impedance_change)
        self.checkbox_impedance.bind("<1>", self.callback, add="")
        self.labelframe_5.pack(
            anchor="w",
            fill="x",
            ipadx=5,
            ipady=5,
            padx=5,
            pady=5,
            side="top")
        self.labelframe_8 = ttk.Labelframe(self.frame_13)
        self.labelframe_8.configure(height=200, text='Theme', width=200)
        self.combobox_theme = ttk.Combobox(
            self.labelframe_8, name="combobox_theme")
        self.combobox_theme.grid(column=1, padx=3, pady=3, row=0, sticky="w")
        self.combobox_theme.bind(
            "<<ComboboxSelected>>",
            self.on_theme_sel,
            add="")
        self.label1 = ttk.Label(self.labelframe_8)
        self.label1.configure(text='GUI:')
        self.label1.grid(column=0, padx=3, pady=3, row=0)
        self.label2 = ttk.Label(self.labelframe_8)
        self.label2.configure(text='Plot:')
        self.label2.grid(column=0, padx=3, pady=3, row=1)
        self.combobox_plotstyle = ttk.Combobox(
            self.labelframe_8, name="combobox_plotstyle")
        self.combobox_plotstyle.grid(
            column=1, padx=3, pady=3, row=1, sticky="w")
        self.combobox_plotstyle.bind(
            "<<ComboboxSelected>>",
            self.on_plotstyle_sel,
            add="")
        self.labelframe_8.pack(
            anchor="w",
            fill="x",
            ipadx=5,
            ipady=5,
            padx=5,
            pady=5,
            side="top")
        self.labelframe1 = ttk.Labelframe(self.frame_13)
        self.labelframe1.configure(height=200, text='Miscellaneous', width=200)
        self.checkbutton1 = ttk.Checkbutton(self.labelframe1)
        self.comment_existing_expr = tk.StringVar()
        self.checkbutton1.configure(
            cursor="arrow",
            offvalue="keep",
            onvalue="comment",
            text='Comment-Out Existing Expressions',
            variable=self.comment_existing_expr)
        self.checkbutton1.pack(anchor="w", side="top")
        self.checkbutton1.configure(command=self.on_comment_expr_change)
        self.checkbutton2 = ttk.Checkbutton(self.labelframe1)
        self.extract_zip = tk.StringVar()
        self.checkbutton2.configure(
            cursor="arrow",
            offvalue="ignore",
            onvalue="extract",
            text='Extract .zip-Files',
            variable=self.extract_zip)
        self.checkbutton2.pack(anchor="w", side="top")
        self.checkbutton2.configure(command=self.on_comment_expr_change)
        self.labelframe1.pack(
            anchor="w",
            fill="x",
            ipadx=5,
            ipady=5,
            padx=5,
            pady=5,
            side="top")
        self.ext_ed_box = ttk.Labelframe(self.frame_13, name="ext_ed_box")
        self.ext_ed_box.configure(
            height=200, text='External Editor', width=200)
        self.entry_ext_ed = ttk.Entry(self.ext_ed_box, name="entry_ext_ed")
        self.ext_ed = tk.StringVar()
        self.entry_ext_ed.configure(textvariable=self.ext_ed)
        self.entry_ext_ed.pack(expand=True, fill="x", padx=10, side="left")
        self.button1 = ttk.Button(self.ext_ed_box)
        self.button1.configure(text='...')
        self.button1.pack(expand=False, side="right")
        self.button1.configure(command=self.on_sel_ext_editor)
        self.ext_ed_box.pack(
            anchor="w",
            fill="x",
            ipadx=5,
            ipady=5,
            padx=5,
            pady=5,
            side="top")
        self.frame_13.pack(expand=True, fill="both")

        # Main widget
        self.mainwindow = self.toplevel_settings

    def run(self):
        self.mainwindow.mainloop()

    def on_win_sel(self, event=None):
        pass

    def on_change_arg(self, event=None):
        pass

    def on_change_shift(self, event=None):
        pass

    def on_impedance_change(self):
        pass

    def callback(self, event=None):
        pass

    def on_theme_sel(self, event=None):
        pass

    def on_plotstyle_sel(self, event=None):
        pass

    def on_comment_expr_change(self):
        pass

    def on_sel_ext_editor(self):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
