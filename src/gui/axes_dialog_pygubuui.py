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
            text='Vertical / Y',
            width=200)
        self.entry_7 = ttk.Entry(self.labelframe_7)
        self.y_var = tk.StringVar()
        self.entry_7.configure(textvariable=self.y_var, validate="all")
        self.entry_7.pack(padx=3, pady=3, side="top")
        _validatecmd = (self.entry_7.register(self.on_y), "%P", "%V")
        self.entry_7.configure(validatecommand=_validatecmd)
        self.button1 = ttk.Button(self.labelframe_7)
        self.button1.configure(text='Auto')
        self.button1.pack(padx=3, pady=3, side="left")
        self.button1.configure(command=self.on_auto_y)
        self.button2 = ttk.Button(self.labelframe_7)
        self.button2.configure(text='Fixed')
        self.button2.pack(padx=3, pady=3, side="right")
        self.button2.configure(command=self.on_fixed_y)
        self.labelframe_7.grid(column=0, row=0)
        self.labelframe_6 = ttk.Labelframe(self.frame_15)
        self.labelframe_6.configure(
            height=200,
            padding=5,
            text='Horizontal / X',
            width=200)
        self.entry_9 = ttk.Entry(self.labelframe_6)
        self.x_var = tk.StringVar()
        self.entry_9.configure(textvariable=self.x_var, validate="all")
        self.entry_9.pack(padx=3, pady=3, side="top")
        _validatecmd = (self.entry_9.register(self.on_x), "%P", "%V")
        self.entry_9.configure(validatecommand=_validatecmd)
        self.button3 = ttk.Button(self.labelframe_6)
        self.button3.configure(text='Auto')
        self.button3.pack(padx=3, pady=3, side="left")
        self.button3.configure(command=self.on_auto_x)
        self.button4 = ttk.Button(self.labelframe_6)
        self.button4.configure(text='Fixed')
        self.button4.pack(padx=3, pady=3, side="right")
        self.button4.configure(command=self.on_fixed_x)
        self.labelframe_6.grid(column=1, row=1)
        self.label1 = ttk.Label(self.frame_15)
        self.label1.configure(text='Plot')
        self.label1.grid(column=1, row=0)
        self.frame_15.pack(side="top")

        # Main widget
        self.mainwindow = self.toplevel_axes

    def run(self):
        self.mainwindow.mainloop()

    def on_y(self, p_entry_value, v_condition):
        pass

    def on_auto_y(self):
        pass

    def on_fixed_y(self):
        pass

    def on_x(self, p_entry_value, v_condition):
        pass

    def on_auto_x(self):
        pass

    def on_fixed_x(self):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
