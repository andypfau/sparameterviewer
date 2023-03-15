#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk
from pygubu.widgets.scrollbarhelper import ScrollbarHelper


class SparamviewerPygubuApp:
    def __init__(self, master=None):
        # build ui
        self.toplevel_cursor = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_cursor.configure(height=600, width=400)
        self.toplevel_cursor.title("Trace Cursors")
        self.frame3 = ttk.Frame(self.toplevel_cursor)
        self.frame3.configure(height=200, padding=10, width=200)
        self.labelframe1 = ttk.Labelframe(self.frame3)
        self.labelframe1.configure(height=200, text='Selection', width=200)
        self.combobox_c1 = ttk.Combobox(self.labelframe1)
        self.combobox_c1.configure(state="readonly")
        self.combobox_c1.grid(column=1, row=0)
        self.combobox_c1.bind(
            "<<ComboboxSelected>>",
            self.on_sel_trace1,
            add="")
        self.combobox_c2 = ttk.Combobox(self.labelframe1)
        self.combobox_c2.configure(state="readonly")
        self.combobox_c2.grid(column=1, row=1)
        self.combobox_c2.bind(
            "<<ComboboxSelected>>",
            self.on_sel_trace2,
            add="")
        self.checkbutton_auto_cursor = ttk.Checkbutton(self.labelframe1)
        self.var_auto_cursor = tk.StringVar()
        self.checkbutton_auto_cursor.configure(
            offvalue="manual",
            onvalue="auto",
            text='Auto',
            variable=self.var_auto_cursor)
        self.checkbutton_auto_cursor.grid(column=0, row=2)
        self.checkbutton_auto_cursor.configure(command=self.on_auto_cursor)
        self.checkbutton_auto_trace = ttk.Checkbutton(self.labelframe1)
        self.var_auto_trace = tk.StringVar()
        self.checkbutton_auto_trace.configure(
            offvalue="manual",
            onvalue="auto",
            text='Auto',
            variable=self.var_auto_trace)
        self.checkbutton_auto_trace.grid(column=1, row=2)
        self.checkbutton_auto_trace.configure(command=self.on_auto_trace)
        self.radiobutton_c1 = ttk.Radiobutton(self.labelframe1)
        self.var_selected_cursor = tk.StringVar(value='cursor_1')
        self.radiobutton_c1.configure(
            text='Cursor 1',
            value="cursor_1",
            variable=self.var_selected_cursor)
        self.radiobutton_c1.grid(column=0, row=0)
        self.radiobutton_c1.configure(command=self.on_sel_cursor1)
        self.radiobutton_c2 = ttk.Radiobutton(self.labelframe1)
        self.radiobutton_c2.configure(
            text='Cursor 2',
            value="cursor_2",
            variable=self.var_selected_cursor)
        self.radiobutton_c2.grid(column=0, row=1)
        self.radiobutton_c2.configure(command=self.on_sel_cursor2)
        self.checkbutton_syncx = ttk.Checkbutton(self.labelframe1)
        self.var_sync_x = tk.StringVar()
        self.checkbutton_syncx.configure(
            offvalue="indep",
            onvalue="sync",
            text='Sync X',
            variable=self.var_sync_x)
        self.checkbutton_syncx.grid(column=2, row=2)
        self.checkbutton_syncx.configure(command=self.on_sync_x)
        self.labelframe1.pack(expand="false", fill="x", side="top")
        self.labelframe2 = ttk.Labelframe(self.frame3)
        self.labelframe2.configure(
            height=200,
            padding=5,
            text='Readouts',
            width=200)
        self.scrollbarhelper2 = ScrollbarHelper(
            self.labelframe2, scrolltype="both")
        self.scrollbarhelper2.configure(usemousewheel=False)
        self.text_readout = tk.Text(self.scrollbarhelper2.container)
        self.text_readout.configure(height=5, width=60)
        self.text_readout.pack(expand="true", fill="both", side="top")
        self.scrollbarhelper2.add_child(self.text_readout)
        self.scrollbarhelper2.pack(expand="true", fill="both", side="top")
        self.labelframe2.pack(expand="true", fill="both", side="top")
        self.frame3.pack(expand="true", fill="both", side="top")

        # Main widget
        self.mainwindow = self.toplevel_cursor

    def run(self):
        self.mainwindow.mainloop()

    def on_sel_trace1(self, event=None):
        pass

    def on_sel_trace2(self, event=None):
        pass

    def on_auto_cursor(self):
        pass

    def on_auto_trace(self):
        pass

    def on_sel_cursor1(self):
        pass

    def on_sel_cursor2(self):
        pass

    def on_sync_x(self):
        pass


if __name__ == "__main__":
    app = SparamviewerPygubuApp()
    app.run()
