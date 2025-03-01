import tkinter as tk
from tkinter import filedialog
import dataclasses
import io
import re
import math
import itertools
import pandas as pd
import numpy as np
import copy


from .tabular_dialog_pygubuui import PygubuAppUI
from lib import SParamFile, PlotData, Si, AppGlobal, Clipboard, TkCommon, TkText



class TabularDatasetBase:
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
    
class TabularDataset(TabularDatasetBase):
    def __init__(self, name: str, xcol: str, ycols: list[str], xcol_data: np.ndarray, ycol_datas: list[np.ndarray], is_spar: bool):
        self._name, self._xcol, self._ycols, self._xcol_data, self._ycol_datas, self._is_spar = name, xcol, ycols, xcol_data, ycol_datas, is_spar
    @property
    def name(self) -> str:
        return self._name
    @property
    def xcol(self) -> str:
        return self._xcol
    @property
    def ycols(self) -> list[str]:
        return self._ycols
    @property
    def xcol_data(self) -> np.ndarray:
        return self._xcol_data
    @property
    def ycol_datas(self) -> list[np.ndarray]:
        return self._ycol_datas
    @property
    def is_spar(self) -> bool:
        return self._is_spar
    
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
    


class TabularDialog(PygubuAppUI):

    
    DISPLAY_PREC = 5
    FORMATS = ['Mag / dB, Phase / Rad', 'Mag / dB, Phase / Deg', 'Mag / dB', 'Mag (linear)', 'Real, Imaginary', 'Phase / Rad', 'Phase / Deg']
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

        def on_change_filter(*args, **kwargs):
            self.on_change_filter()
        self.filter_x.trace_add('write', on_change_filter)
        self.filter_cols.trace_add('write', on_change_filter)
        
        TkCommon.default_keyhandler(self.tabular_dialog, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))
        TkText.default_keyhandler(self.entry_x, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))
        TkText.default_keyhandler(self.entry_cols, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(**kwargs))

        self.update_data()
    

    def on_check_for_global_keystrokes(self, key, ctrl, alt, **kwargs):
        no_mod = not ctrl and not alt
        if key=='Escape' and no_mod:
            self.on_clear_filter()
            return 'break'
        return
    

    def on_change_filter(self):
        self.update_data()


    def on_clear_filter(self):
        self.filter_x.set('')
        self.filter_cols.set('')
        

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
        dataset = self.filter_dataset(dataset)

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

        ds_fmt = self.format_dataset(self.filter_dataset(dataset))

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
        ds_fmt = self.format_dataset(self.filter_dataset(dataset))
        df = self.get_dataframe(ds_fmt)
        sio = io.StringIO()
        df.to_csv(sio, index=None, sep=separator)
        Clipboard.copy_string(sio.getvalue())

        
    def copy_data_numpy(self, dataset: "TabularDataset"):
        dataset = self.filter_dataset(dataset)
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
        dataframes = [self.get_dataframe(self.filter_dataset(dataset)) for dataset in self.datasets]

        writer = pd.ExcelWriter(filename)
        for name,df in zip(names,dataframes):
            df.to_excel(writer, sheet_name=name, index=None, freeze_panes=[1,0])
        writer.close()
    

    def get_filters(self):
        
        def parse_x(s):
            s = s.strip()
            if s=='':
                return any
            
            def extract_float(s):
                if (m := re.match(r'^[-+]?(?:\d+\.?|\.\d)\d*(?:[Ee][-+]?\d+)?', s)):
                    return float(m.group()), s[len(m.group()):].strip()
                return False
            
            if s.startswith('*'):
                s = s[1:].strip()
                if s.startswith('-'):
                    s = s[1:].strip()
                    if (m := extract_float(s)):
                        (b,s) = m
                        if s == '':
                            return -1e99,b
                    
            if (m := extract_float(s)):
                (a,s) = m
                s = s.strip()
                if s.startswith('-'):
                    s = s[1:].strip()
                    if (m := extract_float(s)):
                        (b,s) = m
                        if s.strip() == '':
                            return a,b
                    elif s.startswith('*'):
                        s = s[1:].strip()
                        if s.strip() == '':
                            return a,+1e99

            return None
        
        def parse_cols(s):
            s = s.strip()
            if s=='':
                return any
            parts = [p for p in re.split(r'\s+', s) if p!='']
            return parts

        filter_x = parse_x(self.filter_x.get())
        filter_cols = parse_cols(self.filter_cols.get())

        return filter_x, filter_cols


    def filter_dataset(self, dataset: TabularDataset) -> TabularDataset:
        
        ycols = dataset.ycols
        xcol_data = dataset.xcol_data
        ycol_datas = dataset.ycol_datas

        filter_x, filter_cols = self.get_filters()

        if not dataset.is_spar:
            filter_cols = any  # ignore filter
        
        if filter_x is None or filter_cols is None:
            return TabularDataset('', '', [''], np.zeros([0]), [np.zeros([0])], False)
        
        if filter_cols is not any:
            ycols_filtered = []
            ycol_datas_filtered = []
            for col in filter_cols:
                for colname,coldata in zip(ycols, ycol_datas):
                    if colname == col:
                        ycols_filtered.append(colname)
                        ycol_datas_filtered.append(coldata)
                        break
            ycols, ycol_datas = ycols_filtered, ycol_datas_filtered
        
        if filter_x is not any:
            (x1, x2) = filter_x
            mask = (xcol_data >= x1) & (xcol_data <= x2)
            xcol_data = xcol_data[mask]
            for i in range(len(ycol_datas)):
                ycol_datas[i] = ycol_datas[i][mask]
        
        return TabularDataset(dataset.name, dataset.xcol, ycols, xcol_data, ycol_datas, dataset.is_spar)


    def format_dataset(self, dataset: TabularDataset) -> TabularDataset:
        
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
                    [20*np.log10(np.maximum(1e-15,np.abs(col))) for col in ycol_datas],
                    [np.angle(col) for col in ycol_datas])
            
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

            elif selected_format == 'Real, Imaginary':
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
        
        return TabularDataset( dataset.name, dataset.xcol, ycols, dataset.xcol_data, ycol_datas, dataset.is_spar)
    

    def stringify_row(self, row: list[complex]) -> list[str]:
        return \
            [ str(Si(row[0],significant_digits=TabularDialog.DISPLAY_PREC)) ] + \
            list([ f'{y:.{TabularDialog.DISPLAY_PREC}g}' for y in row[1:] ])
