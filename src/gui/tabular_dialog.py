import tkinter as tk
from tkinter import filedialog
import dataclasses
import math
import re
import pandas as pd
import numpy as np
import itertools


from .tabular_dialog_pygubuui import PygubuAppUI
from lib import SParamFile, PlotData, Si, AppGlobal, Clipboard



class TabularDataset:
    @property
    def name(self) -> str:
        raise NotImplementedError()
    @property
    def name(self) -> str:
        raise NotImplementedError()
    @property
    def xcol(self) -> str:
        raise NotImplementedError()
    @property
    def ycols(self) -> list[str]:
        raise NotImplementedError()
    @property
    def xcol_data(self) -> np.ndarray:
        raise NotImplementedError()
    @property
    def ycol_datas(self) -> list[np.ndarray]:
        raise NotImplementedError()
    @property
    def is_spar(self) -> bool:
        raise NotImplementedError()
    
@dataclasses.dataclass
class TabularDatasetSFile(TabularDataset):
    file: SParamFile
    @property
    def name(self) -> str:
        return self.file.name
    @property
    def xcol(self) -> str:
        return 'Frequency'
    @property
    def ycols(self) -> list[str]:
        cols = []
        for ep in range(self.file.nw.nports):
            for ip in range(self.file.nw.nports):
                cols.append(f'S{ep+1},{ip+1}')
        return cols
    @property
    def xcol_data(self) -> np.ndarray:
        return self.file.nw.f
    @property
    def ycol_datas(self) -> list[np.ndarray]:
        result = []
        for ep in range(self.file.nw.nports):
            for ip in range(self.file.nw.nports):
                result.append(self.file.nw.s[:,ep-1,ip-1])
        return result
    @property
    def is_spar(self) -> bool:
        return True
    
@dataclasses.dataclass
class TabularDatasetPlot(TabularDataset):
    plot: PlotData
    @property
    def name(self) -> str:
        return self.plot.name
    @property
    def xcol(self) -> str:
        return self.plot.x.name
    @property
    def ycols(self) -> list[str]:
        cols = [self.plot.y.name]
        if (self.plot.z is not None):
            cols.append(self.plot.z.name)
        return cols
    @property
    def xcol_data(self) -> np.ndarray:
        return self.plot.x.values
    @property
    def ycol_datas(self) -> list[np.ndarray]:
        result = [self.plot.y.values]
        if (self.plot.z is not None):
            result.append(self.plot.z.values)
        return result
    @property
    def is_spar(self) -> bool:
        return False

@dataclasses.dataclass
class FormattedTabularDataset:
    name: str
    xcol: str
    ycols: list[str]
    xcol_data: np.ndarray
    ycol_datas: list[np.ndarray]

    


class TabularDialog(PygubuAppUI):

    
    DISPLAY_PREC = 5
    FORMATS = ['Mag / dB, Phase / Rad', 'Mag / dB, Phase / Deg', 'Mag / dB', 'Mag (linear)', 'Complex', 'Phase / Rad', 'Phase / Deg']
    DEFAULT_FORMAT = 2


    def __init__(self, datasets: list[TabularDataset], initial_selection: int, master=None):
        
        super().__init__(master)
        AppGlobal.set_toplevel_icon(self.tabular_dialog)

        assert initial_selection < len(datasets)
        self.datasets = datasets

        def get_display_name(item):
            if isinstance(item, TabularDatasetSFile):
                return 'S-Param: ' + item.name
            if isinstance(item, TabularDatasetPlot):
                return 'Plot: ' + item.name
            raise ValueError()
        
        self.combobox_file['values'] = [get_display_name(item) for item in self.datasets]
        self.combobox_file.current(initial_selection)

        self.combobox_format['values'] = TabularDialog.FORMATS
        self.combobox_format.current(TabularDialog.DEFAULT_FORMAT)

        self.listbox.column("#0", width=0, stretch=tk.NO)
        self.listbox.heading("#0", text="", anchor=tk.W)

        self.update_data()
        

    def run(self, focus: bool = True):
        if focus:
            self.mainwindow.focus_force()
        super().run()
    

    def on_change_format(self, event=None):
        self.update_data()

    
    def on_select_file(self, event=None):
        
        if self.selected_dataset is not None:
            can_change_format = self.selected_dataset.is_spar
            self.combobox_format['state'] = 'readonly' if can_change_format else 'disabled'

        self.update_data()


    def on_copy_tab(self):
        dataset = self.selected_dataset
        if dataset is None:
            return
        self.copy_data_csv(dataset, '\t')


    def on_copy_semicolon(self):
        dataset = self.selected_dataset
        if dataset is None:
            return
        self.copy_data_csv(dataset, ';')


    def on_copy_numpy(self):
        dataset = self.selected_dataset
        if dataset is None:
            return
        self.copy_data_numpy(dataset)


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

        ds_fmt = self.format_dataset(dataset)

        cols = [ds_fmt.xcol] + list(ds_fmt.ycols)
        all_columns = [ds_fmt.xcol_data] + list(ds_fmt.ycol_datas)
        rows = zip(*all_columns)
        
        self.listbox['columns'] = cols
        for col in cols:
            self.listbox.column(col, anchor=tk.E, width=100, minwidth=60, stretch=0)
            self.listbox.heading(col, text=col, anchor=tk.E)

        self.listbox.delete(*self.listbox.get_children())
        for row in rows:
            formatted_row = self.stringify_row(row)
            self.listbox.insert('', 'end', values=formatted_row)

        
    def copy_data_csv(self, dataset: "TabularDataset", separator: str = '\t'):
        ds_fmt = self.format_dataset(dataset)
        df = self.get_dataframe(ds_fmt)
        df.to_clipboard(index=False, sep=separator)

        
    def copy_data_numpy(self, dataset: "TabularDataset"):
        def sanitize_name(name: str) -> str:
            return re.sub('\W|^(?=\d)', '_', name)
        def fmt(x) -> str:
            return f'{x:.{TabularDialog.DISPLAY_PREC}g}'
        py = 'import numpy as np\n'
        py += f'# {dataset.name}\n'
        py += f'{sanitize_name(dataset.xcol)} = np.array([{", ".join([fmt(x) for x in dataset.xcol_data])}])\n'
        for n,d in zip(dataset.ycols,dataset.ycol_datas):
            py += f'{sanitize_name(n)} = np.array([{", ".join([fmt(x) for x in d])}])\n'
        Clipboard.copy_string(py)
    

    def get_dataframe(self, dataset: "TabularDataset") -> "pd.DataFrame":
        data = { dataset.xcol: dataset.xcol_data }
        for name,arr in zip(dataset.ycols,dataset.ycol_datas):
            data[name] = arr
        return pd.DataFrame(data)


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
    

    def format_dataset(self, dataset: TabularDataset) -> FormattedTabularDataset:
        
        def interleave_lists(*lists):
            return list(itertools.chain(*zip(*lists)))
        
        ycols = dataset.ycols
        ycol_datas = dataset.ycol_datas

        if dataset.is_spar:
            selected_format = TabularDialog.FORMATS[self.combobox_format.current()]
            if selected_format == 'Mag / dB, Phase / Rad':
                ycols = interleave_lists(
                    [name+' / dB' for name in ycols],
                    [name+' / Rad' for name in ycols])
                ycol_datas = interleave_lists(
                    [20*np.log10(np.maximum(1e-15,np.abs(col))) for col in dataset.ycol_datas],
                    [np.angle(col) for col in dataset.ycol_datas])
            
            elif selected_format == 'Mag / dB, Phase / Deg':
                ycols = interleave_lists(
                    [name+' / dB' for name in ycols],
                    [name+' / Deg' for name in ycols])
                ycol_datas = interleave_lists(
                    [20*np.log10(np.maximum(1e-15,np.abs(col))) for col in dataset.ycol_datas],
                    [np.angle(col)*180/math.pi for col in dataset.ycol_datas])

            elif selected_format == 'Mag / dB':
                ycols = [name+' / dB' for name in ycols]
                ycol_datas = [20*np.log10(np.maximum(1e-15,np.abs(col))) for col in dataset.ycol_datas]

            elif selected_format == 'Mag (linear)':
                ycol_datas = [np.abs(col) for col in dataset.ycol_datas]

            elif selected_format == 'Complex':
                ycols = interleave_lists(
                    [name+' / re' for name in ycols],
                    [name+' / im' for name in ycols])
                ycol_datas = interleave_lists(
                    [np.real(col) for col in dataset.ycol_datas],
                    [np.imag(col) for col in dataset.ycol_datas])
            
            elif selected_format == 'Phase / Rad':
                ycols = [name+' / rad' for name in ycols]
                ycol_datas = [np.angle(col) for col in dataset.ycol_datas]
            
            elif selected_format == 'Phase / Deg':
                ycols = [name+' / deg' for name in ycols]
                ycol_datas = [np.angle(col)*180/math.pi for col in dataset.ycol_datas]
            
            else:
                raise ValueError(f'Invalid combobox selection: {format}')
        else:
            # dataset is not S-params, so formatting of the data is probably not intended
            pass
        
        return FormattedTabularDataset( dataset.name, dataset.xcol, ycols, dataset.xcol_data, ycol_datas)
    

    def stringify_row(self, row: list[complex]) -> list[str]:
        return \
            [ str(Si(row[0],significant_digits=TabularDialog.DISPLAY_PREC)) ] + \
            list([ f'{y:.{TabularDialog.DISPLAY_PREC}g}' for y in row[1:] ])
