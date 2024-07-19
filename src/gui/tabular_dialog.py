import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from pygubu.widgets.scrollbarhelper import ScrollbarHelper
import dataclasses
import math
import cmath
import logging

from lib import Clipboard, SParamFile, PlotData, Si



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

    
    DISPLAY_PREC = 4
    EXPORT_PREC  = 8


    def __init__(self, datasets: list[TabularDataset], initial_selection: int, master=None):
        
        assert initial_selection < len(datasets)
        self.datasets = datasets
        self.clipboard_data = ''

        def get_display_name(item):
            if isinstance(item, TabularDatasetFile):
                return 'File: ' + item.file.name
            if isinstance(item, TabularDatasetPlot):
                return 'Plot: ' + item.plot.name
            raise ValueError()
        
        self.toplevel_tabular = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_tabular.configure(height=600, width=800)
        self.toplevel_tabular.title("Tabular Data")
        
        self.frame_top = ttk.Frame(self.toplevel_tabular)
        self.frame_top.configure(padding=10)
        self.combobox_file = ttk.Combobox(self.frame_top)
        self.combobox_file.configure(state="readonly")
        self.combobox_file.bind("<<ComboboxSelected>>", self.on_select_file, add="")
        self.combobox_file['values'] = [get_display_name(item) for item in self.datasets]
        self.combobox_file.current(initial_selection)
        self.combobox_file.pack(side='top', fill='x')
        self.combobox_format = ttk.Combobox(self.frame_top)
        self.combobox_format.configure(state="readonly")
        self.combobox_format.bind("<<ComboboxSelected>>", self.on_change_format, add="")
        self.combobox_format['values'] = ['Mag / dB', 'Mag (linear)', 'Complex', 'Phase / Rad', 'Phase / Deg']
        self.combobox_format.current(0)
        self.combobox_format.pack(side='left')
        self.frame_top.pack(fill="x", side="top")
        
        self.frame_main = ttk.Frame(self.toplevel_tabular)
        self.frame_main.configure(padding=10)
        self.scrollbarhelper1 = ScrollbarHelper(self.frame_main, scrolltype="both")
        self.scrollbarhelper1.configure(usemousewheel=False)
        self.listbox = ttk.Treeview(self.scrollbarhelper1.container, columns=[])
        self.listbox.column("#0", width=0, stretch=tk.NO)
        self.listbox.heading("#0", text="", anchor=tk.W)
        self.listbox.pack(fill="both", side="top")
        self.scrollbarhelper1.add_child(self.listbox)
        self.scrollbarhelper1.pack(fill="both", side="top", expand='true')
        self.frame_main.pack(fill='both', side="top", expand='true')
        
        self.menu_main = tk.Menu(self.toplevel_tabular)
        self.submenu_file = tk.Menu(self.menu_main, tearoff="false")
        self.menu_main.add(tk.CASCADE, menu=self.submenu_file, label='File')
        self.submenu_file.add("command", command=self.on_save_single, label='Save...')
        #self.submenu_file.add("command", command=self.on_save_all, label='Save All...')
        self.submenu_edit = tk.Menu(self.menu_main)
        self.menu_main.add(tk.CASCADE, menu=self.submenu_edit, label='Edit')
        self.submenu_edit.add("command", command=self.on_copy, label='Copy')
        self.toplevel_tabular.configure(menu=self.menu_main)
        
        self.mainwindow = self.toplevel_tabular
        
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
            self.listbox.column(col, anchor=tk.E, width=100, minwidth=60, stretch=0)
            self.listbox.heading(col, text=col, anchor=tk.E)

        xfmt_disp, yfmt_disp = self.get_formatters(for_display=True)
        xfmt_copy, yfmt_copy = self.get_formatters(for_display=False)
        
        self.listbox.delete(*self.listbox.get_children())
        self.clipboard_data = '\t'.join(cols) + '\n'
        for row in rows:
            display_row   = [xfmt_disp(row[0])] + ['\t'+yfmt_disp(y) for y in row[1:]]
            clipboard_row = [xfmt_copy(row[0])] + ['\t'+yfmt_copy(y) for y in row[1:]]
            self.listbox.insert('', 'end', values=display_row)
            self.clipboard_data += '\t'.join(clipboard_row) + '\n'
    
    
    def get_formatters(self, for_display: bool):

        prec = TabularDialog.DISPLAY_PREC if for_display else TabularDialog.EXPORT_PREC
        
        x_formatter = lambda x: str(Si(x, significant_digits=prec))
        
        format_selection = self.combobox_format.current()
        if format_selection==0:
            y_formatter = lambda y: f'{20*math.log10(max(1e-15,abs(y))):+.{prec}g}'
        elif format_selection==1:
            y_formatter = lambda y: str(Si(abs(y), significant_digits=prec))
        elif format_selection==2:
            def complex_formatter(y):
                if y.imag==0:
                    return f'{y.real:.{prec}g}'
                if y.real==0:
                    return f'{y.imag:.{prec}g}j'
                return f'{y.real:.{prec}g}{y.imag:+.{prec}g}j'
            y_formatter = complex_formatter
        elif format_selection==3:
            y_formatter = lambda y: f'{cmath.phase(y):.{prec}g}'
        elif format_selection==4:
            y_formatter = lambda y: f'{cmath.phase(y)*math.pi/180:.{prec}g}'
        else:
            raise ValueError(f'Invalid combobox selection: {format}')
        
        return x_formatter, y_formatter


    def on_save_single(self):
        self.save(all_datasets=False)

    def on_save_all(self):
        self.save(all_datasets=True)


    def save(self, all_datasets: bool = False):
        if all_datasets:
            filename = filedialog.asksaveasfilename(
                title='Save All Tabular Data', confirmoverwrite=True, defaultextension='.xlsx',
                filetypes=(
                    ('Spreadsheet','.xlsx'),
                    ('All Files','*'),
                ))
        else:
            filename = filedialog.asksaveasfilename(
                title='Save Tabular Data', confirmoverwrite=True, defaultextension='.csv',
                filetypes=(
                    ('CSV','.csv'),
                    ('Spreadsheet','.xlsx'),
                    ('All Files','*'),
                ))
        
        if not filename:
            return

        if filename.lower().endswith('xlsx') or all_datasets:
            self.save_spreadsheet(filename, all_datasets=all_datasets)
        else:
            self.save_csv(filename)


    def save_csv(self, filename):
        raise NotImplementedError()


    def save_spreadsheet(self, filename, all_datasets: bool = False):
        if all_datasets:
            raise NotImplementedError()
        raise NotImplementedError()


    def on_copy(self):
        try:
            Clipboard.copy_string(self.clipboard_data)
        except Exception as ex:
            logging.exception(f'Copying CSV-data to clipboard failed: {ex}')
            messagebox.showerror('Error', str(ex))
