#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper


class PygubuApp:
    def __init__(self, master=None):
        # build ui
        self.toplevel_log = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_log.configure(height=200, width=200)
        self.toplevel_log.title("Log")
        self.frame4 = ttk.Frame(self.toplevel_log)
        self.frame4.configure(height=200, width=200)
        self.scrollbarhelper4 = ScrollbarHelper(self.frame4, scrolltype="both")
        self.scrollbarhelper4.configure(usemousewheel=False)
        self.log_text = tk.Text(self.scrollbarhelper4.container)
        self.log_text.configure(height=25, width=150, wrap="none")
        self.log_text.pack(expand="true", fill="both", side="top")
        self.scrollbarhelper4.add_child(self.log_text)
        self.scrollbarhelper4.pack(expand="true", fill="both", side="top")
        self.frame4.pack(
            expand="true",
            fill="both",
            padx=5,
            pady=5,
            side="top")
        self.frame5 = ttk.Frame(self.toplevel_log)
        self.frame5.configure(height=200, width=200)
        self.combobox1 = ttk.Combobox(self.frame5)
        self.log_level = tk.StringVar()
        self.combobox1.configure(
            state="readonly",
            textvariable=self.log_level,
            values='Debug Info Warning Error')
        self.combobox1.pack(side="left")
        self.combobox1.bind("<<ComboboxSelected>>", self.on_set_level, add="")
        self.button2 = ttk.Button(self.frame5)
        self.button2.configure(text='Clear')
        self.button2.pack(side="right")
        self.button2.configure(command=self.on_clear)
        self.frame5.pack(
            expand="true",
            fill="x",
            padx=5,
            pady=5,
            side="bottom")

        # Main widget
        self.mainwindow = self.toplevel_log

    def run(self):
        self.mainwindow.mainloop()

    def on_set_level(self, event=None):
        pass

    def on_clear(self):
        pass


if __name__ == "__main__":
    app = PygubuApp()
    app.run()
