#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper


class PygubuAppUI:
    def __init__(self, master=None):
        # build ui
        self.tabular_dialog = tk.Tk() if master is None else tk.Toplevel(master)
        self.tabular_dialog.configure(height=500, width=600)
        self.tabular_dialog.overrideredirect("False")
        self.tabular_dialog.title("Tabular Data")
        self.frame_5 = ttk.Frame(self.tabular_dialog)
        self.frame_5.configure(height=200, width=200)
        self.frame1 = ttk.Frame(self.frame_5)
        self.frame1.configure(height=200, padding=0, width=200)
        self.combobox_file = ttk.Combobox(self.frame1, name="combobox_file")
        self.combobox_file.pack(fill="x", padx=5, pady=5, side="top")
        self.combobox_file.bind(
            "<<ComboboxSelected>>",
            self.on_select_file,
            add="")
        self.combobox_format = ttk.Combobox(
            self.frame1, name="combobox_format")
        self.combobox_format.pack(padx=5, pady=5, side="left")
        self.combobox_format.bind(
            "<<ComboboxSelected>>",
            self.on_change_format,
            add="")
        self.frame1.pack(fill="x", side="top")
        self.frame2 = ttk.Frame(self.frame_5)
        self.frame2.configure(height=200, width=200)
        self.scrollbarhelper1 = ScrollbarHelper(self.frame2, scrolltype="both")
        self.scrollbarhelper1.configure(usemousewheel=False)
        self.listbox = ttk.Treeview(
            self.scrollbarhelper1.container, name="listbox")
        self.listbox.configure(selectmode="extended")
        self.listbox.pack(expand=True, fill="both", side="top")
        self.scrollbarhelper1.add_child(self.listbox)
        self.scrollbarhelper1.pack(
            expand=True,
            fill="both",
            padx=5,
            pady=5,
            side="top")
        self.frame2.pack(expand=True, fill="both", side="bottom")
        self.frame_5.pack(expand=True, fill="both", side="top")
        self.menu_2 = tk.Menu(self.tabular_dialog)
        self.submenu_1 = tk.Menu(
            self.menu_2,
            cursor="arrow",
            font="TkDefaultFont",
            tearoff=False)
        self.menu_2.add(
            tk.CASCADE,
            menu=self.submenu_1,
            font="TkDefaultFont",
            label='File')
        self.submenu_1.add(
            "command",
            command=self.on_save_single,
            label='Save...')
        self.submenu_1.add(
            "command",
            command=self.on_save_all,
            label='Save All...')
        self.submenu_2 = tk.Menu(self.menu_2, tearoff=False)
        self.menu_2.add(tk.CASCADE, menu=self.submenu_2, label='Edit')
        self.submenu_2.add("command", command=self.on_copy, label='Copy')
        self.tabular_dialog.configure(menu=self.menu_2)

        # Main widget
        self.mainwindow = self.tabular_dialog

    def run(self):
        self.mainwindow.mainloop()

    def on_select_file(self, event=None):
        pass

    def on_change_format(self, event=None):
        pass

    def on_save_single(self):
        pass

    def on_save_all(self):
        pass

    def on_copy(self):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
