#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk


class PygubuAppUI:
    def __init__(self, master=None):
        # build ui
        self.toplevel_axes = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_axes.configure(height=200, width=200)
        self.frame_15 = ttk.Frame(self.toplevel_axes)
        self.frame_15.configure(height=200, padding=10, width=200)
        self.labelframe_7 = ttk.Labelframe(self.frame_15)
        self.labelframe_7.configure(
            height=200,
            padding=5,
            text='Vertical / Y',
            width=200)
        self.label_15 = ttk.Label(self.labelframe_7)
        self.label_15.configure(text='Top:')
        self.label_15.grid(column=0, row=0, sticky="w")
        self.entry_7 = ttk.Entry(self.labelframe_7)
        self.y1_var = tk.StringVar()
        self.entry_7.configure(textvariable=self.y1_var, validate="all")
        self.entry_7.grid(column=1, padx=5, pady=5, row=0, sticky="w")
        _validatecmd = (self.entry_7.register(self.on_y1), "%P", "%V")
        self.entry_7.configure(validatecommand=_validatecmd)
        self.label_14 = ttk.Label(self.labelframe_7)
        self.label_14.configure(text='Bottom:')
        self.label_14.grid(column=0, row=1, sticky="w")
        self.entry_8 = ttk.Entry(self.labelframe_7)
        self.y0_var = tk.StringVar()
        self.entry_8.configure(textvariable=self.y0_var, validate="all")
        self.entry_8.grid(column=1, padx=5, pady=5, row=1, sticky="w")
        _validatecmd = (self.entry_8.register(self.on_y0), "%P", "%V")
        self.entry_8.configure(validatecommand=_validatecmd)
        self.checkbutton_4 = ttk.Checkbutton(
            self.labelframe_7, name="checkbutton_4")
        self.yauto_var = tk.StringVar()
        self.checkbutton_4.configure(
            offvalue="manual",
            onvalue="auto",
            text='Automatic',
            variable=self.yauto_var)
        self.checkbutton_4.grid(column=0, columnspan=2, padx=5, pady=3, row=2)
        self.labelframe_7.pack(ipadx=5, ipady=5, padx=5, pady=5, side="left")
        self.labelframe_6 = ttk.Labelframe(self.frame_15)
        self.labelframe_6.configure(
            height=200,
            padding=5,
            text='Horizontal / X',
            width=200)
        self.label_11 = ttk.Label(self.labelframe_6)
        self.label_11.configure(text='Left:')
        self.label_11.grid(column=0, row=0, sticky="w")
        self.entry_9 = ttk.Entry(self.labelframe_6)
        self.x0_var = tk.StringVar()
        self.entry_9.configure(textvariable=self.x0_var, validate="all")
        self.entry_9.grid(column=0, padx=5, pady=5, row=1, sticky="w")
        _validatecmd = (self.entry_9.register(self.on_x0), "%P", "%V")
        self.entry_9.configure(validatecommand=_validatecmd)
        self.label_12 = ttk.Label(self.labelframe_6)
        self.label_12.configure(text='Right:')
        self.label_12.grid(column=1, row=0, sticky="w")
        self.entry_10 = ttk.Entry(self.labelframe_6)
        self.x1_var = tk.StringVar()
        self.entry_10.configure(textvariable=self.x1_var, validate="all")
        self.entry_10.grid(column=1, padx=5, pady=5, row=1, sticky="w")
        _validatecmd = (self.entry_10.register(self.on_x1), "%P", "%V")
        self.entry_10.configure(validatecommand=_validatecmd)
        self.checkbutton_3 = ttk.Checkbutton(
            self.labelframe_6, name="checkbutton_3")
        self.xauto_var = tk.StringVar()
        self.checkbutton_3.configure(
            offvalue="manual",
            onvalue="auto",
            text='Automatic',
            variable=self.xauto_var)
        self.checkbutton_3.grid(column=0, columnspan=2, padx=5, pady=3, row=2)
        self.labelframe_6.pack(ipadx=5, ipady=5, padx=5, pady=5, side="right")
        self.frame_15.pack()

        # Main widget
        self.mainwindow = self.toplevel_axes

    def run(self):
        self.mainwindow.mainloop()

    def on_y1(self, p_entry_value, v_condition):
        pass

    def on_y0(self, p_entry_value, v_condition):
        pass

    def on_x0(self, p_entry_value, v_condition):
        pass

    def on_x1(self, p_entry_value, v_condition):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
