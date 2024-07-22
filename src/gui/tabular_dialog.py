import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from pygubu.widgets.scrollbarhelper import ScrollbarHelper
import dataclasses
import math
import cmath
import logging
import io
import pandas as pd

from lib import Clipboard, SParamFile, PlotData, Si, AppGlobal



class TabularDataset:
    @property
    def name(self) -> str:
        raise NotImplementedError()
    @property
    def columns(self) -> list[str]:
        raise NotImplementedError()
    @property
    def rows(self) -> list[list[complex]]:
        raise NotImplementedError()
    
@dataclasses.dataclass
class TabularDatasetFile(TabularDataset):
    file: SParamFile
    @property
    def name(self) -> str:
        return self.file.name
    @property
    def columns(self) -> list[str]:
        cols = ['Frequency']
        for ep in range(self.file.nw.nports):
            for ip in range(self.file.nw.nports):
                cols.append(f'S{ep+1},{ip+1}')
        return cols
    @property
    def rows(self) -> list[list[complex]]:
        rows = []
        for i,f in enumerate(self.file.nw.f):
            row = [f]
            for ep in range(self.file.nw.nports):
                for ip in range(self.file.nw.nports):
                    row.append(self.file.nw.s[i,ep-1,ip-1])
            rows.append(row)
        return rows
    
@dataclasses.dataclass
class TabularDatasetPlot(TabularDataset):
    plot: PlotData
    @property
    def name(self) -> str:
        return self.plot.name
    @property
    def columns(self) -> list[str]:
        if self.plot.z is not None:
            return [self.plot.x.name, self.plot.y.name, self.plot.z.name]
        else:
            return [self.plot.x.name, self.plot.y.name]
    @property
    def rows(self) -> list[list[complex]]:
        if self.plot.z is not None:
            return [[x,y,z] for (x,y,z) in zip(self.plot.x.values, self.plot.y.values, self.plot.z.values)]
        else:
            return [[x,y] for (x,y) in zip(self.plot.x.values, self.plot.y.values)]
    


class TabularDialog:

    
    DISPLAY_PREC = 4
    EXPORT_PREC  = 8


    def __init__(self, datasets: list[TabularDataset], initial_selection: int, master=None):
        
        assert initial_selection < len(datasets)
        self.datasets = datasets

        def get_display_name(item):
            if isinstance(item, TabularDatasetFile):
                return 'File: ' + item.name
            if isinstance(item, TabularDatasetPlot):
                return 'Plot: ' + item.name
            raise ValueError()
        
        self.toplevel_tabular = tk.Tk() if master is None else tk.Toplevel(master)
        self.toplevel_tabular.configure(height=600, width=800)
        self.toplevel_tabular.title("Tabular Data")
        AppGlobal.set_toplevel_icon(self.toplevel_tabular)
        
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
        self.submenu_file.add("command", command=self.on_save_all, label='Save All...')
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


    def on_copy(self):
        dataset = self.selected_dataset
        if dataset is None:
            return
        self.copy_data(dataset)


    def on_save_single(self):
        dataset = self.selected_dataset
        if dataset is None:
            return

        filename = filedialog.asksaveasfilename(
            title='Save Tabular Data', confirmoverwrite=True, defaultextension='.csv',
            filetypes=(
                ('CSV','.csv'),
                ('Spreadsheet','.xlsx'),
                ('All Files','*'),
            ))
        if not filename:
            return

        if filename.lower().endswith('.xlsx'):
            self.save_spreadsheet(dataset, filename)
        else:
            self.save_csv(dataset, filename)
        

    def on_save_all(self):
        if len(self.datasets) < 1:
            return

        filename = filedialog.asksaveasfilename(
            title='Save All Tabular Data', confirmoverwrite=True, defaultextension='.xlsx',
            filetypes=(
                ('Spreadsheet','.xlsx'),
                ('All Files','*'),
            ))
        if not filename:
            return

        self.save_spreadsheets_all(filename)
    

    def update_data(self):
        dataset = self.selected_dataset
        if dataset is None:
            return
        self.plot_data(dataset)
    

    @property
    def selected_dataset(self) -> TabularDataset:
        if len(self.datasets) < 1:
            return None
        return self.datasets[self.combobox_file.current()]

        
    def plot_data(self, dataset: "TabularDataset"):

        x_convert, x_format = self.get_x_formatter()
        _, y_convert, y_format, y_unit = self.get_y_formatter()
        
        self.listbox['columns'] = dataset.columns
        for col in dataset.columns:
            unit = '' if (y_unit is None) else (' / ' + y_unit)
            self.listbox.column(col, anchor=tk.E, width=100, minwidth=60, stretch=0)
            self.listbox.heading(col, text=col+unit, anchor=tk.E)

        self.listbox.delete(*self.listbox.get_children())
        for row in dataset.rows:
            display_row   = [x_format(x_convert(row[0]))] + ['\t'+y_format(y_convert(y)) for y in row[1:]]
            self.listbox.insert('', 'end', values=display_row)

        
    def copy_data(self, dataset: "TabularDataset"):

        df = self.get_dataframe(dataset)
        df.to_clipboard(index=False)
    

    def get_dataframe(self, dataset: "TabularDataset") -> "pd.DataFrame":

        x_convert, _ = self.get_x_formatter()
        is_re_im, y_convert, _, y_unit = self.get_y_formatter()

        processed_cols = [dataset.columns[0]]
        for col in dataset.columns[1:]:
            unit = '' if (y_unit is None) else (' / ' + y_unit)
            if is_re_im:
                processed_cols.append(col + ' real' + unit)
                processed_cols.append(col + ' imag' + unit)
            else:
                processed_cols.append(col + unit)
        
        processed_rows = []
        for row in dataset.rows:
            col_data = [x_convert(row[0])]
            for col in row[1:]:
                if is_re_im:
                    (re,im) = y_convert(col)
                    col_data.append(re)
                    col_data.append(im)
                else:
                    col_data.append(y_convert(col))
            processed_rows.append(col_data)
        
        return pd.DataFrame(processed_rows, columns=processed_cols)


    def save_csv(self, dataset: "TabularDataset", filename: str):
        df = self.get_dataframe(dataset)
        df.to_csv(filename, sep='\t', index=None)


    def save_spreadsheet(self, dataset: "TabularDataset", filename: str):
        df = self.get_dataframe(dataset)
        df.to_excel(filename, sheet_name=dataset.name, index=None, freeze_panes=[1,0])


    def save_spreadsheets_all(self, filename: str):
        names = [dataset.name for dataset in self.datasets]
        dataframes = [self.get_dataframe(dataset) for dataset in self.datasets]

        writer = pd.ExcelWriter(filename)
        for name,df in zip(names,dataframes):
            df.to_excel(writer, sheet_name=name, index=None, freeze_panes=[1,0])
        writer.close()
    

    def get_x_formatter(self):
        
        prec = TabularDialog.DISPLAY_PREC
        
        converter = lambda value: value
        formatter = lambda value: str(Si(value, significant_digits=prec))

        return converter, formatter
    

    def get_y_formatter(self):
        
        prec = TabularDialog.DISPLAY_PREC
        format_selection = self.combobox_format.current()
        is_re_im = False

        if format_selection==0: # dB
            converter = lambda value: 20*math.log10(max(1e-15,abs(value)))
            formatter = lambda db: f'{db:.{prec}g}'
            unit = 'dB'

        elif format_selection==1: # linear
            converter = lambda value: value
            formatter = lambda linval: str(Si(linval, significant_digits=prec))
            unit = None

        elif format_selection==2: # complex
            is_re_im = True
            converter = lambda value: (value.real, value.imag)
            def complex_formatter(value):
                (re, im) = value
                if im==0:
                    return f'{re:.{prec}g}'
                if re==0:
                    return f'{im:.{prec}g}j'
                return f'{re:.{prec}g}{im:+.{prec}g}j'
            formatter = complex_formatter
            unit = None
        
        elif format_selection==3: # rad
            converter = lambda value: cmath.phase(value)
            formatter = lambda rad: f'{rad:.{prec}g}'
            unit = 'rad'
        
        elif format_selection==4: # degrees
            converter = lambda value: cmath.phase(value)*180/math.pi
            formatter = lambda deg: f'{deg:.{prec}g}'
            unit = 'deg'
        
        else:
            raise ValueError(f'Invalid combobox selection: {format}')
    
        return is_re_im, converter, formatter, unit
