#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk


class PygubuApp:
    def __init__(self, master=None):
        # build ui
        self.toplevel_axes = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_axes.configure(height=200, width=200)
        self.frame_15 = ttk.Frame(self.toplevel_axes)
        self.frame_15.configure(height=200, padding=10, width=200)
        self.labelframe_6 = ttk.Labelframe(self.frame_15)
        self.labelframe_6.configure(
            height=200,
            padding=5,
            text='Horizontal / X',
            width=200)
        self.label_11 = ttk.Label(self.labelframe_6)
        self.label_11.configure(text='Left:')
        self.label_11.grid(column=0, row=0, sticky="w")
        self.spinbox_4 = ttk.Spinbox(self.labelframe_6)
        self.x0 = tk.DoubleVar()
        self.spinbox_4.configure(
            from_=0,
            increment=0.1,
            textvariable=self.x0,
            to=1000)
        self.spinbox_4.grid(column=0, padx=5, pady=3, row=1, sticky="w")
        self.spinbox_4.bind("<<Decrement>>", self.on_change_arg, add="")
        self.spinbox_4.bind("<<Increment>>", self.on_change_arg, add="")
        self.label_12 = ttk.Label(self.labelframe_6)
        self.label_12.configure(text='Right:')
        self.label_12.grid(column=1, row=0, sticky="w")
        self.checkbutton_3 = ttk.Checkbutton(self.labelframe_6)
        self.xauto = tk.StringVar()
        self.checkbutton_3.configure(
            offvalue="manual",
            onvalue="auto",
            text='Automatic',
            variable=self.xauto)
        self.checkbutton_3.grid(column=0, columnspan=2, padx=5, pady=3, row=2)
        self.checkbutton_3.configure(command=self.on_impedance_change)
        self.checkbutton_3.bind("<1>", self.callback, add="")
        self.spinbox_6 = ttk.Spinbox(self.labelframe_6)
        self.x1 = tk.DoubleVar()
        self.spinbox_6.configure(
            from_=0,
            increment=0.1,
            textvariable=self.x1,
            to=1000)
        self.spinbox_6.grid(column=1, padx=5, pady=3, row=1, sticky="w")
        self.spinbox_6.bind("<<Decrement>>", self.on_change_arg, add="")
        self.spinbox_6.bind("<<Increment>>", self.on_change_arg, add="")
        self.labelframe_6.pack(ipadx=5, ipady=5, padx=5, pady=5, side="right")
        self.labelframe_7 = ttk.Labelframe(self.frame_15)
        self.labelframe_7.configure(
            height=200,
            padding=5,
            text='Vertical / Y',
            width=200)
        self.label_14 = ttk.Label(self.labelframe_7)
        self.label_14.configure(text='Bottom:')
        self.label_14.grid(column=0, row=1, sticky="w")
        self.spinbox_7 = ttk.Spinbox(self.labelframe_7)
        self.y0 = tk.DoubleVar()
        self.spinbox_7.configure(
            from_=0,
            increment=0.1,
            textvariable=self.y0,
            to=1000)
        self.spinbox_7.grid(column=1, padx=5, pady=3, row=1, sticky="w")
        self.spinbox_7.bind("<<Decrement>>", self.on_change_arg, add="")
        self.spinbox_7.bind("<<Increment>>", self.on_change_arg, add="")
        self.label_15 = ttk.Label(self.labelframe_7)
        self.label_15.configure(text='Top:')
        self.label_15.grid(column=0, row=0, sticky="w")
        self.checkbutton_4 = ttk.Checkbutton(self.labelframe_7)
        self.yauto = tk.StringVar()
        self.checkbutton_4.configure(
            offvalue="manual",
            onvalue="auto",
            text='Automatic',
            variable=self.yauto)
        self.checkbutton_4.grid(column=0, columnspan=2, padx=5, pady=3, row=2)
        self.checkbutton_4.configure(command=self.on_impedance_change)
        self.checkbutton_4.bind("<1>", self.callback, add="")
        self.spinbox_8 = ttk.Spinbox(self.labelframe_7)
        self.y1 = tk.DoubleVar()
        self.spinbox_8.configure(
            from_=0,
            increment=0.1,
            textvariable=self.y1,
            to=1000)
        self.spinbox_8.grid(column=1, padx=5, pady=3, row=0, sticky="w")
        self.spinbox_8.bind("<<Decrement>>", self.on_change_arg, add="")
        self.spinbox_8.bind("<<Increment>>", self.on_change_arg, add="")
        self.labelframe_7.pack(ipadx=5, ipady=5, padx=5, pady=5, side="left")
        self.frame_15.pack()

        # Main widget
        self.mainwindow = self.toplevel_axes

    def run(self):
        self.mainwindow.mainloop()

    def on_change_arg(self, event=None):
        pass

    def on_impedance_change(self):
        pass

    def callback(self, event=None):
        pass


if __name__ == "__main__":
    app = PygubuApp()
    app.run()
