#!/usr/bin/python3
import tkinter as tk
import tkinter.ttk as ttk


class PygubuAppUI:
    def __init__(self, master=None):
        # build ui
        self.toplevel_rl = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_rl.configure(height=600, width=400)
        self.toplevel_rl.title("Optimum RL Calculator")
        self.frame_9 = ttk.Frame(self.toplevel_rl)
        self.frame_9.configure(height=400, padding=10, width=200)
        self.labelframe_1 = ttk.Labelframe(self.frame_9)
        self.labelframe_1.configure(
            height=200,
            padding=5,
            text='File and Port',
            width=200)
        self.combobox_files = ttk.Combobox(self.labelframe_1)
        self.combobox_files.configure(state="readonly")
        self.combobox_files.pack(expand=True, fill="x", side="left")
        self.combobox_files.bind(
            "<<ComboboxSelected>>",
            self.on_change,
            add="")
        self.label_5 = ttk.Label(self.labelframe_1)
        self.label_5.configure(text=' Port')
        self.label_5.pack(side="left")
        self.spinbox_1 = ttk.Spinbox(self.labelframe_1)
        self.port = tk.StringVar()
        self.spinbox_1.configure(
            from_=1,
            increment=1,
            textvariable=self.port,
            to=99,
            width=5)
        self.spinbox_1.pack(padx=0, side="left")
        self.labelframe_1.pack(expand=False, fill="x", side="top")
        self.labelframe_2 = ttk.Labelframe(self.frame_9)
        self.labelframe_2.configure(
            height=200,
            padding=5,
            text='Integration Range',
            width=200)
        self.entry_1 = ttk.Entry(self.labelframe_2)
        self.int0 = tk.StringVar()
        self.entry_1.configure(textvariable=self.int0)
        self.entry_1.pack(side="left")
        self.label_1 = ttk.Label(self.labelframe_2)
        self.label_1.configure(text='to')
        self.label_1.pack(side="left")
        self.entry_2 = ttk.Entry(self.labelframe_2)
        self.int1 = tk.StringVar()
        self.entry_2.configure(textvariable=self.int1)
        self.entry_2.pack(side="left")
        self.label_2 = ttk.Label(self.labelframe_2)
        self.label_2.configure(text='GHz')
        self.label_2.pack(side="left")
        self.labelframe_2.pack(fill="x", side="top")
        self.labelframe_3 = ttk.Labelframe(self.frame_9)
        self.labelframe_3.configure(
            height=200,
            padding=5,
            text='Target Range',
            width=200)
        self.entry_3 = ttk.Entry(self.labelframe_3)
        self.tgt0 = tk.StringVar()
        self.entry_3.configure(textvariable=self.tgt0)
        self.entry_3.pack(side="left")
        self.label_3 = ttk.Label(self.labelframe_3)
        self.label_3.configure(text='to')
        self.label_3.pack(side="left")
        self.entry_4 = ttk.Entry(self.labelframe_3)
        self.tgt1 = tk.StringVar()
        self.entry_4.configure(textvariable=self.tgt1)
        self.entry_4.pack(side="left")
        self.label_4 = ttk.Label(self.labelframe_3)
        self.label_4.configure(text='GHz')
        self.label_4.pack(side="left")
        self.labelframe_3.pack(fill="x", side="top")
        self.labelframe_4 = ttk.Labelframe(self.frame_9)
        self.labelframe_4.configure(
            height=200, padding=5, text='Result', width=200)
        self.frame_10 = ttk.Frame(self.labelframe_4)
        self.frame_10.configure(height=200, width=200)
        self.result_box = tk.Text(self.frame_10, name="result_box")
        self.result_box.configure(
            height=3,
            relief="flat",
            setgrid=False,
            state="disabled",
            width=50)
        self.result_box.pack(expand=True, fill="x", side="top")
        self.frame2 = ttk.Frame(self.frame_10)
        self.frame2.configure(height=200, width=200)
        self.radiobutton1 = ttk.Radiobutton(self.frame2)
        self.plot_kind = tk.StringVar(value='rl_vs_f')
        self.radiobutton1.configure(
            text='RL vs. Frequency',
            value="rl_vs_f",
            variable=self.plot_kind)
        self.radiobutton1.grid(column=0, pady=5, row=0)
        self.radiobutton2 = ttk.Radiobutton(self.frame2)
        self.radiobutton2.configure(
            text='RL Histogram',
            value="rl_hist",
            variable=self.plot_kind)
        self.radiobutton2.grid(column=1, padx=10, pady=5, row=0)
        self.frame2.pack(fill="x", side="top")
        self.frame_rlplot = ttk.Frame(self.frame_10)
        self.frame_rlplot.configure(height=400, width=600)
        self.frame_rlplot.pack(expand=True, fill="both", side="top")
        self.entry_5 = ttk.Entry(self.frame_10)
        self.err_msg = tk.StringVar()
        self.entry_5.configure(state="readonly", textvariable=self.err_msg)
        self.entry_5.pack(expand=False, fill="x", side="top")
        self.frame_10.pack(expand=True, fill="both", side="top")
        self.labelframe_4.pack(expand=True, fill="both", side="top")
        self.frame_9.pack(expand=True, fill="both", side="top")

        # Main widget
        self.mainwindow = self.toplevel_rl

    def run(self):
        self.mainwindow.mainloop()

    def on_change(self, event=None):
        pass


if __name__ == "__main__":
    app = PygubuAppUI()
    app.run()
