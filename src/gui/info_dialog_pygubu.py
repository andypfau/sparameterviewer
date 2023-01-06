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
        self.toplevel_info = tk.Tk() if master is None else tk.Toplevel(master)
        self.frame1 = ttk.Frame(self.toplevel_info)
        self.scrollbarhelper1 = ScrollbarHelper(self.frame1, scrolltype='both')
        self.text_info = tk.Text(self.scrollbarhelper1.container)
        self.text_info.configure(height='25', width='120', wrap='none')
        self.text_info.pack(expand='true', fill='both', side='top')
        self.scrollbarhelper1.add_child(self.text_info)
        self.scrollbarhelper1.configure(usemousewheel=False)
        self.scrollbarhelper1.pack(expand='true', fill='both', side='top')
        self.frame1.configure(height='200', padding='10', width='200')
        self.frame1.pack(expand='true', fill='both', side='top')
        self.toplevel_info.configure(height='600', width='800')
        self.toplevel_info.title('File Info')

        # Main widget
        self.mainwindow = self.toplevel_info
    
    def run(self):
        self.mainwindow.mainloop()


if __name__ == '__main__':
    app = SparamviewerPygubuApp()
    app.run()


