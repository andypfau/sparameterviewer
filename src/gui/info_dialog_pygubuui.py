#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper


class PygubuAppUI:
    def __init__(self, master=None):
        # build ui
        self.toplevel_info = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_info.configure(height=600, width=800)
        self.toplevel_info.title("File Info")
        self.frame1 = ttk.Frame(self.toplevel_info)
        self.frame1.configure(height=200, padding=10, width=200)
        self.scrollbarhelper1 = ScrollbarHelper(self.frame1, scrolltype="both")
        self.scrollbarhelper1.configure(usemousewheel=False)
        self.text_info = tk.Text(self.scrollbarhelper1.container)
        self.text_info.configure(height=25, width=120, wrap="none")
        self.text_info.pack(expand=True, fill="both", side="top")
        self.scrollbarhelper1.add_child(self.text_info)
        self.scrollbarhelper1.pack(expand=True, fill="both", side="top")
        self.frame1.pack(expand=True, fill="both", side="top")

        # Main widget
        self.mainwindow = self.toplevel_info

    def run(self):
        self.mainwindow.mainloop()


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
