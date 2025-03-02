#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk


class PygubuAppUI:
    def __init__(self, master=None, data_pool=None):
        # build ui
        self.toplevel_axes = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_axes.configure(height=200, width=200)
        self.frame_15 = ttk.Frame(self.toplevel_axes)
        self.frame_15.configure(height=200, padding=10, width=200)
        self.labelframe_7 = ttk.Labelframe(self.frame_15)
        self.labelframe_7.configure(
            height=200,
            padding=5,
            relief="flat",
            text='Vertical / Y',
            width=200)
        self.combo_y = ttk.Combobox(self.labelframe_7, name="combo_y")
        self.y_var = tk.StringVar()
        self.combo_y.configure(textvariable=self.y_var, validate="all")
        self.combo_y.pack(side="top")
        _validatecmd = (self.combo_y.register(self.on_y), "%P", "%V")
        self.combo_y.configure(validatecommand=_validatecmd)
        self.labelframe_7.grid(column=0, row=0)
        self.labelframe_6 = ttk.Labelframe(self.frame_15)
        self.labelframe_6.configure(
            height=200,
            padding=5,
            relief="flat",
            text='Horizontal / X',
            width=200)
        self.combo_x = ttk.Combobox(self.labelframe_6, name="combo_x")
        self.x_var = tk.StringVar()
        self.combo_x.configure(textvariable=self.x_var, validate="all")
        self.combo_x.pack(side="top")
        _validatecmd = (self.combo_x.register(self.on_x), "%P", "%V")
        self.combo_x.configure(validatecommand=_validatecmd)
        self.labelframe_6.grid(column=1, row=1)
        self.frame1 = ttk.Frame(self.frame_15)
        self.frame1.configure(height=200, width=200)
        self.frame2 = ttk.Frame(self.frame1)
        self.frame2.configure(height=200, width=200)
        self.separator2 = ttk.Separator(self.frame2)
        self.separator2.configure(orient="vertical")
        self.separator2.pack(expand=True, fill="y", side="left")
        self.label1 = ttk.Label(self.frame2)
        self.label1.configure(
            justify="center",
            padding=10,
            text='    Plot    ')
        self.label1.pack(side="right")
        self.frame2.pack(anchor="sw", expand=True, fill="both", side="top")
        self.separator1 = ttk.Separator(self.frame1)
        self.separator1.configure(orient="horizontal")
        self.separator1.pack(expand=True, fill="x", side="bottom")
        self.frame1.grid(column=1, row=0)
        self.frame_15.pack(side="top")

        # Main widget
        self.mainwindow = self.toplevel_axes

    def run(self):
        self.mainwindow.mainloop()

    def on_y(self, p_entry_value, v_condition):
        pass

    def on_x(self, p_entry_value, v_condition):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
