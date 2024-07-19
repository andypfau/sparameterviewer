import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from pygubu.widgets.scrollbarhelper import ScrollbarHelper
import dataclasses
import math
import cmath
import logging

from lib import Clipboard
from lib import SParamFile
from lib import PlotData



class TabularDataset:
    def display_name(self):
        raise NotImplementedError()
    
@dataclasses.dataclass
class TabularDatasetFile(TabularDataset):
    file: SParamFile
    
@dataclasses.dataclass
class TabularDatasetPlot(TabularDataset):
    plot: PlotData
    


class TabularDialog:

    def __init__(self, datasets: list[TabularDataset], initial_selection: int, master=None):
        
        assert initial_selection < len(datasets)
        self.datasets = datasets
        self.clipboard_data = ''

        def get_display_name(item):
            if isinstance(item, TabularDatasetFile):
                return 'File ' + item.file.name
            if isinstance(item, TabularDatasetPlot):
                return 'Plot ' + item.plot.name
            raise ValueError()
        
        self.toplevel_info = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_info.configure(height=600, width=800)
        self.toplevel_info.title("Tabular Data")
        
        self.frame1 = ttk.Frame(self.toplevel_info)
        self.frame1.configure(padding=10)
        self.frame1.pack(expand="true", fill="x", side="top")
        self.combobox_file = ttk.Combobox(self.frame1)
        self.combobox_file.configure(state="readonly")
        self.combobox_file.bind("<<ComboboxSelected>>", self.on_select_file, add="")
        self.combobox_file['values'] = [get_display_name(item) for item in self.datasets]
        self.combobox_file.current(initial_selection)
        self.combobox_file.pack(side='top', expand='true', fill='x')
        self.combobox_format = ttk.Combobox(self.frame1)
        self.combobox_format.configure(state="readonly")
        self.combobox_format.bind("<<ComboboxSelected>>", self.on_change_format, add="")
        self.combobox_format['values'] = ['Mag / dB', 'Mag (linear)', 'Complex', 'Phase / Rad', 'Phase / Deg']
        self.combobox_format.current(0)
        self.combobox_format.pack(side='left')
        self.button_copy = ttk.Button(self.frame1)
        self.button_copy.configure(text='Copy')
        self.button_copy.configure(command=self.on_copy)
        self.button_copy.pack(side='right')
        
        self.frame2 = ttk.Frame(self.toplevel_info)
        self.frame2.configure(padding=10)
        self.scrollbarhelper1 = ScrollbarHelper(self.frame2, scrolltype="both")
        self.scrollbarhelper1.configure(usemousewheel=False)
        self.listbox = ttk.Treeview(self.scrollbarhelper1.container, columns=[])
        self.listbox.pack(expand="true", fill="both", side="top")
        self.listbox.column("#0", width=0, stretch=tk.NO)
        self.listbox.heading("#0", text="", anchor=tk.W)
        self.scrollbarhelper1.add_child(self.listbox)
        self.scrollbarhelper1.pack(expand="true", fill="both", side="bottom")
        self.frame2.pack(expand="true", fill="both", side="top")
        
        self.mainwindow = self.toplevel_info
        
        self.update_data()
    

    def run(self):
        self.mainwindow.mainloop()
    

    def on_change_format(self, event=None):
        self.update_data()

    
    def on_select_file(self, event=None):
        self.update_data()
    

    def update_data(self):
        
        if len(self.datasets) < 1:
            return
        
        item = self.datasets[self.combobox_file.current()]
        if isinstance(item, TabularDatasetFile):
            self.plot_sparam_file(item.file)
        elif isinstance(item, TabularDatasetPlot):
            self.plot_plot_data(item.plot)
        else:
            raise ValueError()
        
    
    def plot_sparam_file(self, file: SParamFile):

        cols = ['Frequency']
        for ep in range(file.nw.nports):
            for ip in range(file.nw.nports):
                cols.append(f'S{ep+1},{ip+1}')
        rows = []
        for i,f in enumerate(file.nw.f):
            row = [f]
            for ep in range(file.nw.nports):
                for ip in range(file.nw.nports):
                    #row.append(f'\t{v2db(file.nw.s[i,ep-1,ip-1]):+.4g} dB')
                    row.append(file.nw.s[i,ep-1,ip-1])
            rows.append(row)
        
        self.plot_data(cols, rows)
    
    
    def plot_plot_data(self, data: PlotData):

        if data.z is not None:
            cols = [data.x.name, data.y.name, data.z.name]
            rows = [[x,y,z] for (x,y,z) in zip(data.x.values, data.y.values, data.z.values)]
        else:
            cols = [data.x.name, data.y.name]
            rows = [[x,y] for (x,y) in zip(data.x.values, data.y.values)]
        
        self.plot_data(cols, rows)

        
    def plot_data(self, cols: list[str], rows: list[list[complex]]):

        self.listbox['columns'] = cols
        for col in cols:
            self.listbox.column(col, anchor=tk.E, width=120)
            self.listbox.heading(col, text=col, anchor=tk.E)

        f_formatter = lambda f,u: f'{f/1e9:.4g} GHz' if u else f'{f:.4g}'

        format_selection = self.combobox_format.current()
        if format_selection==0:
            formatter = lambda x,u: f'{20*math.log10(max(1e-15,abs(x))):+.4g}' + (' dB' if u else '')
        elif format_selection==1:
            formatter = lambda x,u: f'{abs(x):.4g}'
        elif format_selection==2:
            formatter = lambda x,u: f'{x.real:.4g}{x.imag:+.4g}j'
        elif format_selection==3:
            formatter = lambda x,u: f'{cmath.phase(x):4g}'
        elif format_selection==4:
            formatter = lambda x,u: f'{cmath.phase(x)*math.pi/180:.4g}' + ('°' if u else '')
        else:
            raise ValueError(f'Invalid combobox selection: {format}')
        
        self.listbox.delete(*self.listbox.get_children())
        self.clipboard_data = '\t'.join(cols) + '\n'
        for row in rows:
            formatted_row = [f_formatter(row[0],True)] + ['\t'+formatter(x,True) for x in row[1:]]
            self.listbox.insert('', 'end', values=formatted_row)
            self.clipboard_data += '\t'.join([f_formatter(row[0],False)] + [formatter(x,False) for x in row[1:]]) + '\n'


    def on_copy(self):
        try:
            Clipboard.copy_string(self.clipboard_data)
        except Exception as ex:
            logging.exception(f'Copying CSV-data to clipboard failed: {ex}')
            messagebox.showerror('Error', str(ex))
