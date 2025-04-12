from .main_window_ui import MainWindowUi
from .log_handler import LogHandler
from .settings import Settings
from .tabular_dialog import TabularDialog
from .rl_dialog import RlDialog
from .settings_dialog import SettingsDialog, SettingsTab
from .filter_dialog import FilterDialog
from .cursor_dialog import CursorDialog
from .info_dialog import InfoDialog
from .log_dialog import LogDialog
from .axes_dialog import AxesDialog
from .about_dialog import AboutDialog
from .simple_dialogs import info_dialog, warning_dialog, error_dialog, exception_dialog, okcancel_dialog, yesno_dialog, open_directory_dialog, open_file_dialog, save_file_dialog
from .help import show_help
from lib.si import SiFmt
from lib import Clipboard
from lib import AppPaths
from lib import open_file_in_default_viewer, sparam_to_timedomain, get_sparam_name, group_delay, v2db, start_process
from lib import Si
from lib import SParamFile
from lib import PlotHelper
from lib import ExpressionParser
from info import Info

import pathlib
import math
import copy
import logging
import traceback
import datetime
import numpy as np
import re
import os
import zipfile
import enum
import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
import scipy.signal
from PyQt6 import QtCore, QtGui, QtWidgets



class MainWindow(MainWindowUi):

    MAX_DIRECTORY_HISTORY_SIZE = 10


    class Mode(enum.StrEnum):
        All = 'All S-Parameters'
        AllFwd = 'All S-Parameters (reciprocal)'
        IL = 'Insertion Loss'
        IlFwd = 'Insertion Loss (reciprocal)'
        S21 = 'Insertion Loss S21'
        RL = 'Return Loss / Impedance'
        S11 = 'Return Loss S11'
        S22 = 'Return Loss S22'
        S33 = 'Return Loss S33'
        S44 = 'Return Loss S44'
        Expr = 'Expression-Based'


    class Unit(enum.StrEnum):
        Off = '—'
        dB = 'dB'
        LinMag = 'Lin Mag'
        LogMag = 'Log Mag'
        ReIm = 'Real+Imag'
        Real = 'Real'
        Imag = 'Imag'
        ReImPolar = 'Polar'
        SmithY = 'Smith (Z)'
        SmithZ = 'Smith (Y)'
        Impulse = 'Impulse Resp.'
        Step = 'Step Resp.'


    class Unit2(enum.StrEnum):
        Off = '—'
        Phase = 'Phase'
        Unwrap = 'Unwrapped'
        LinRem = 'Lin. Removed'
        GDelay = 'Group Delay'


    def __init__(self, filenames: list[str]):
        super().__init__()
        
        self.directories: list[str] = []
        self.files: list[SParamFile] = []
        self.generated_expressioN_s = ''
        self.plot_mouse_down = False
        #self.cursor_dialog: SparamviewerCursorDialog = None
        self.plot_axes_are_valid = False
        self._cursor_dialog: CursorDialog = None
        self._log_dialog: LogDialog = None
            
        # create plot
        self.plot: PlotHelper = None

        self.ui_set_modes_list([str(mode) for mode in MainWindow.Mode])
        self.ui_set_units_list([str(mode) for mode in MainWindow.Unit])
        self.ui_set_units2_list([str(mode) for mode in MainWindow.Unit2])
        self.ui_set_window_title(Info.AppName)

        ## TODO: mouse events
        #def callback_click(event):
        #    if event.button and event.xdata and event.ydata:
        #        self.on_plot_mouse_down(event.button, event.xdata, event.ydata)
        #def callback_release(event):
        #    if event.button:
        #        self.on_plot_mouse_up(event.button)
        #def callback_move(event):
        #    if event.xdata and event.ydata:
        #        self.on_plot_mouse_move(event.xdata, event.ydata)
        #self.figure.canvas.callbacks.connect('button_press_event', callback_click)
        #self.figure.canvas.callbacks.connect('button_release_event', callback_release)
        #self.figure.canvas.callbacks.connect('motion_notify_event', callback_move)

        # load settings
        def load_settings():
            try:
                self.ui_mode = str(MainWindow.Mode(Settings.plot_mode))
                self.ui_unit = str(MainWindow.Unit(Settings.plot_unit))
                self.ui_unit2 = str(MainWindow.Unit2(Settings.plot_unit2))
                self.ui_expression = Settings.expression
                self.ui_show_legend = Settings.show_legend
                self.ui_hide_single_item_legend = Settings.hide_single_item_legend
                self.ui_shorten_legend = Settings.shorten_legend_items
                return None
            except Exception as ex:
                return ex
        loading_exception = load_settings()
        if loading_exception:
            exception_dialog('Error', f'Unable to load settings ({loading_exception}), trying again with pristine settings')
            loading_exception = load_settings()
            load_settings() # load again; this time no re-try
            exception_dialog('Error', f'Unable to load settings after reset ({loading_exception}), ignoring')
        Settings.attach(self.on_settings_change)

        # initialize display
        self.initially_load_files_or_directory(filenames)
        self.update_plot()

    def show(self):
        self.ui_show()


    @property
    def selected_files(self) -> list[SParamFile]:
        return [self.files[i] for i in self.ui_get_selected_fileview_indices()]


    @property
    def cursor_dialog(self) -> CursorDialog:
        if not self._cursor_dialog:
            self._cursor_dialog = CursorDialog(self)
        return self._cursor_dialog


    @property
    def log_dialog(self) -> LogDialog:
        if not self._log_dialog:
            self._log_dialog = LogDialog(self)
        return self._log_dialog

    
    def initially_load_files_or_directory(self, filenames_or_directory: "list[str]"):
        if len(filenames_or_directory)<1:
            filenames_or_directory = [AppPaths.get_default_file_dir()]

        is_dir = os.path.isdir(filenames_or_directory[0])
        if is_dir:
            directory = filenames_or_directory
            absdir = os.path.abspath(directory[0])
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(only_select_first=True)
        else:
            filenames = filenames_or_directory
            if not Settings.extract_zip:
                contains_archives = False
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.zip']:
                        contains_archives = True
                        break
                if contains_archives:
                    if yesno_dialog('Extract .zip Files', 'A .zip-file was selected, but the option to extract .zip-files is disabled. Do you want to enable it?'):
                        Settings.extract_zip = True
            absdir = os.path.split(filenames[0])[0]
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(selected_filenames=filenames)


    def on_select_mode(self):
        Settings.plot_mode = self.ui_mode
        self.update_plot()


    def on_select_unit(self):
        changed = Settings.plot_unit != self.ui_unit
        Settings.plot_unit = self.ui_unit
        if changed:
            # different kind of chart -> axes scale is probably no longer valid
            self.invalidate_axes_lock(update=False)

            # only allow phase in specific combinations
            if Settings.plot_unit not in [MainWindow.Unit.Off, MainWindow.Unit.dB, MainWindow.Unit.LinMag, MainWindow.Unit.LogMag]:
                self.ui_unit2 = MainWindow.Unit2.Off

        self.update_plot()
    

    def on_select_unit2(self):
        if Settings.plot_unit not in [MainWindow.Unit.Off, MainWindow.Unit.dB, MainWindow.Unit.LinMag, MainWindow.Unit.LogMag]:
            self.ui_unit2 = MainWindow.Unit2.Off
            return # no phase allowed

        changed = Settings.plot_unit2 != self.ui_unit2
        Settings.plot_unit2 = self.ui_unit2

        if changed:
            # different kind of chart -> axes scale is probably no longer valid
            self.invalidate_axes_lock(update=False)

        self.update_plot()
    

    def on_show_filter(self):
        all_files = [file.name for file in self.files]
        selected_files = FilterDialog(self).show_modal_dialog(all_files)
        if not selected_files:
            return
        indices = [all_files.index(file) for file in selected_files]
        self.ui_select_fileview_items(indices)
    

    def on_reload_all_files(self):
        self.reload_all_files()


    def update_most_recent_directories_menu(self):

        def make_loader_closure(dir):
            # TODO: the menu does not disappear after clicking
            def load():
                if not os.path.exists(dir):
                    logging.error(f'Cannot load recent directory <{dir}> (does not exist any more)')
                    return
                absdir = os.path.abspath(dir)
                self.directories = [absdir]
                self.clear_loaded_files()
                self.load_files_in_directory(absdir)
                self.update_file_list(only_select_first=True)
                self.add_to_most_recent_directories(dir)
            return load
        
        entries = [(pathlib.Path(path).stem, make_loader_closure(path)) for path in Settings.last_directories]
        self.ui_update_files_history(entries)
        
    
    def add_to_most_recent_directories(self, dir: str):
        if dir in Settings.last_directories:
            idx = Settings.last_directories.index(dir)
            del Settings.last_directories[idx]
        
        Settings.last_directories.insert(0, dir)
        
        while len(Settings.last_directories) > MainWindow.MAX_DIRECTORY_HISTORY_SIZE:
            del Settings.last_directories[-1]
        
        self.update_most_recent_directories_menu()


    def load_files_in_directory(self, dir: str):

        self.add_to_most_recent_directories(dir)

        try:

            absdir = os.path.abspath(dir)
            
            def filetype_matches(path):
                ext = os.path.splitext(path)[1]
                return re.match(r'(\.ci?ti)|(\.s[0-9]+p)', ext, re.IGNORECASE)
        
            def load_file(filename, archive_path=None):
                try:
                    file = SParamFile(filename, archive_path=archive_path)
                    self.files.append(file)
                except Exception as ex:
                    logging.info(f'Ignoring file <{filename}>: {ex}')
            
            def find_all_files(path):
                all_items = [os.path.join(path,f) for f in os.listdir(path)]
                return sorted(list([f for f in all_items if os.path.isfile(f)]))

            all_files = find_all_files(absdir)

            for filename in all_files:
                if not filetype_matches(filename):
                    continue
                load_file(filename)

            if Settings.extract_zip:
                for zip_filename in all_files:
                    ext = os.path.splitext(zip_filename)[1].lower()
                    if ext != '.zip':
                        continue
                    try:
                        with zipfile.ZipFile(zip_filename, 'r') as zf:
                            for internal_name in zf.namelist():
                                if not filetype_matches(internal_name):
                                    continue
                                load_file(internal_name, archive_path=zip_filename)
                    except Exception as ex:
                        logging.warning(f'Unable to open zip file <{zip_filename}>: {ex}')
        
        except Exception as ex:
            logging.exception(f'Unable to load files: {ex}')
            raise ex


    def reload_all_files(self):
        self.clear_loaded_files()
        for dir in self.directories:
            self.load_files_in_directory(dir)
        self.update_file_list()


    def clear_loaded_files(self):
        self.files = []
        self.trace_data = []


    def get_file_prop_str(self, file: "SParamFile") -> str:
        if file.loaded():
            return f'{file.nw.number_of_ports}-port, {Si(min(file.nw.f),"Hz")} to {Si(max(file.nw.f),"Hz")}'
        elif file.error():
            return '[loading failed]'
        else:
            return '[not loaded]'


    def update_file_in_list(self, file: "SParamFile"):
        self.ui_update_fileview_item(file.tag, file.name, self.get_file_prop_str(file))
    

    def update_file_list(self, selected_filenames: "list[str]" = [], only_select_first: bool = False):
        
        if len(selected_filenames) == 0 and not only_select_first:
            previously_selected_files = self.get_selected_files()
        else:
            previously_selected_files = []

        selected_archives = set()
        names_and_contents = []
        selected_file_indices = []
        rex = None
        for i,file in enumerate(self.files):
            
            file.tag = i
            name_str = file.name
            prop_str = self.get_file_prop_str(file)
            
            names_and_contents.append((name_str,prop_str))
            
            do_select = False
            if only_select_first and i==0:
                do_select = True
            elif file.tag in [s.tag for s in previously_selected_files]:
                do_select = True
            elif os.path.abspath(file.file_path) in [os.path.abspath(f) for f in selected_filenames]:
                do_select = True
            elif (file.archive_path is not None) and (os.path.abspath(file.archive_path) in [os.path.abspath(f) for f in selected_filenames]):
                if file.archive_path not in selected_archives:
                    # only select the 1st file in any archive, to avoid excessive loading time
                    selected_archives.add(file.archive_path)
                    do_select = True
            
            if do_select:
                selected_file_indices.append(file.tag)
        self.ui_set_fileview_items(names_and_contents)
        self.ui_select_fileview_items(selected_file_indices)


    def get_selected_files(self) -> "list[SParamFile]":
        selected_files = []
        for index in self.ui_get_selected_fileview_indices():
            for file in self.files:
                if file.tag == index:
                    selected_files.append(file)
                    break
        return selected_files
    

    def on_select_file(self):
        self.update_plot()


    def on_open_directory(self):
        initial_dir = self.directories[0] if len(self.directories)>0 else AppPaths.get_default_file_dir()
        dir = open_directory_dialog(self, title='Open Directory', initial_dir=initial_dir)
        if not dir:
            return
        absdir = os.path.abspath(dir)
        self.directories = [absdir]
        self.clear_loaded_files()
        self.load_files_in_directory(absdir)
        self.update_file_list(only_select_first=True)


    def on_append_directory(self):
        initial_dir = self.directories[0] if len(self.directories)>0 else AppPaths.get_default_file_dir()
        dir = open_directory_dialog(self, title='Append Directory', initial_dir=initial_dir)
        if not dir:
            return
        absdir = os.path.abspath(dir)
        if absdir not in self.directories:
            self.directories.append(absdir)
            self.load_files_in_directory(absdir)
        self.update_file_list()
    
    
    def on_trace_cursors(self):
        self.cursor_dialog.show_dialog()
    
    
    def on_rl_calc(self):
        if len(self.files) < 1:
            error_dialog('No Files', 'No files to integrate.', 'Open some files first.')
            return
        if len(self.selected_files) >= 1:
            selected = self.selected_files[0]
        else:
            selected = None
        RlDialog(self).show_modal_dialog(self.files, selected)


    def on_log(self):
        self.log_dialog.show_dialog()
    
    
    def on_settings(self):
        SettingsDialog(self).show_modal_dialog()
    
    
    def on_help(self):
        show_help()
    

    def on_about(self):
        AboutDialog(self).show_modal_dialog()


    def on_save_plot_image(self):

        if not self.plot.fig:
            info_dialog('Nothing To Save', 'Nothing to save.')
            return

        try:
            filename = save_file_dialog(self,
                title='Save Plot Graphic',
                filetypes=(
                    ('PNG','.png'),
                    ('All Files','*'),
                ))
            if not filename:
                return
            self.plot.fig.savefig(filename)
        except Exception as ex:
            error_dialog('Error', 'Exporting failed.', str(ex))
    

    def on_file_info(self):
        if len(self.selected_files)<=0:
            error_dialog('Error', 'No file selected.')
            return

        info_str = ''
        for file in self.selected_files:
            if len(info_str)>0:
                info_str+= '\n\n\n'
            info_str += self.get_info_str(file)
        InfoDialog(self).show_modal_dialog(info_str)
    
    
    def on_view_tabular(self):       
        
        datasets = []
        initial_selection = None
        for i,file in enumerate(self.files):
            if (initial_selection is None) and (file in self.selected_files):
                initial_selection = i
            datasets.append(file)
        for plot in self.plot.plots:
            datasets.append(file)
        
        TabularDialog(self).show_modal_dialog(datasets=datasets, initial_selection=initial_selection)
    

    def on_open_externally(self):

        if not SettingsDialog.ensure_external_editor_is_set(self):
            return

        files = [file.file_path for file in self.selected_files]
        try:
            start_process(Settings.ext_editor_cmd, *files)
        except Exception as ex:
            error_dialog('Open File Externally', 'Unable to open file with external editor.', str(ex))
    

    def on_load_expressions(self):

        if len(self.ui_expression.strip()) > 0:
            if not okcancel_dialog('Overwrite', 'Expressions are not empty and will be overwritten.'):
                return

        try:
            fn = open_file_dialog(self, title='Load Expressions', filetypes=[('Expressions','.py'),('Text','.txt'),('All Files','*')])
            if not fn:
                return
            with open(fn, 'r') as fp:
                py = fp.read()
            self.ui_expression = py.strip()
        except Exception as ex:
            error_dialog('Error', 'Loading expressions failed.', str(ex))
    

    def on_save_expressions(self):
        try:
            fn = save_file_dialog(self, title='Save Expressions', filetypes=[('Expressions','.py'),('Text','.txt'),('All Files','*')])
            if not fn:
                return
            with open(fn, 'w') as fp:
                fp.write(self.ui_expression.strip())
        except Exception as ex:
            error_dialog('Error', 'Saving expressions failed.', str(ex))
    

    def on_show_legend(self):
        Settings.show_legend = self.ui_show_legend
        self.update_plot()
    

    def on_hide_single_legend(self):
        Settings.hide_single_item_legend = self.ui_hide_single_item_legend
        self.update_plot()


    def on_shorten_legend(self):
        Settings.shorten_legend_items = self.ui_shorten_legend
        self.update_plot()


    def on_copy_image(self):

        if not self.plot.fig:
            info_dialog('Nothing To Copy', 'Nothing to copy.')
            return

        try:
            Clipboard.copy_figure(self.plot.fig)
        except Exception as ex:
            error_dialog('Error', 'Copying plot to clipboard failed.', str(ex))
    

    def on_lock_xaxis(self):
        if not self.ui_lock_x:
            self.update_plot()

    
    def on_lock_yaxis(self):
        if not self.ui_lock_y:
            self.update_plot()


    def on_lock_both(self):
        self.ui_lock_x = True
        self.ui_lock_y = True


    def on_unlock_axes(self):
        self.ui_lock_x = False
        self.ui_lock_y = False
        self.update_plot()
    

    def on_rescale_locked_axes(self):
        self.invalidate_axes_lock()
    
    
    def on_manual_axes(self):
        def scaling_callback(x0, x1, xauto, y0, y1, yauto):
            try:
                self.ui_lock_x = not xauto
                if not xauto:
                    self.plot.plot.set_xlim((x0,x1))
                self.ui_lock_y = not yauto
                if not yauto:
                    self.plot.plot.set_ylim((y0,y1))
            except:
                pass
            self.update_plot()
        
        (x0,x1) = self.plot.plot.get_xlim()
        (y0,y1) = self.plot.plot.get_ylim()
        AxesDialog(self).show_modal_dialog(x0, x1, not self.ui_lock_x, y0, y1, not self.ui_lock_y, scaling_callback)


    def on_update_expressions(self):
        self.ui_mode = MainWindow.Mode.Expr
        self.update_plot()

    
    def invalidate_axes_lock(self, update: bool = True):
        self.plot_axes_are_valid = False
        if update:
            self.update_plot()
    

    def on_settings_change(self):
        self.update_plot()
    
    
    def on_update_button(self):
        self.ui_mode = MainWindow.Mode.Expr
        self.update_plot()
    
    
    def on_template_button(self):
        self.ui_show_template_menu()
    
    
    def on_help_button(self):
        show_help('expressions.md')

    
    def get_info_str(self, sparam_file: SParamFile) -> str:
        
        f0, f1 = sparam_file.nw.f[0], sparam_file.nw.f[-1]
        n_pts = len(sparam_file.nw.f)
        _, fname = os.path.split(sparam_file.file_path)
        comm = '' if sparam_file.nw.comments is None else sparam_file.nw.comments
        n_ports = sparam_file.nw.s.shape[1]

        fileinfo = ''
        def fmt_tstamp(ts):
            return f'{datetime.datetime.fromtimestamp(ts):%Y-%m-%d %H:%M:%S}'
        if sparam_file.archive_path is not None:
            fileinfo += f'Archive path: {os.path.abspath(sparam_file.archive_path)}\n'
            try:
                created = fmt_tstamp(os.path.getctime(sparam_file.archive_path))
                fileinfo += f'Archive created: {created}, '
            except:
                fileinfo += f'Archive created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(sparam_file.archive_path))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(sparam_file.archive_path):,.0f} B'
                fileinfo += f'Archive size: {size}\n'
            except:
                fileinfo += f'Archive size: unknown\n'
            fileinfo += f'File path in archive: {sparam_file.file_path}\n'
        else:
            fileinfo += f'File path: {os.path.abspath(sparam_file.file_path)}\n'
            try:
                created = fmt_tstamp(os.path.getctime(sparam_file.file_path))
                fileinfo += f'File created: {created}, '
            except:
                fileinfo += f'File created: unknoown, '
            try:
                modified = fmt_tstamp(os.path.getmtime(sparam_file.file_path))
                fileinfo += f'last modified: {modified}\n'
            except:
                fileinfo += f'last modified: unknown\n'
            try:
                size = f'{os.path.getsize(sparam_file.file_path):,.0f} B'
                fileinfo += f'File size: {size}\n'
            except:
                fileinfo += f'File size: unknown\n'
        
        if (sparam_file.nw.z0 == sparam_file.nw.z0[0,0]).all():
            z0 = str(Si(sparam_file.nw.z0[0,0],'Ohm'))
        else:
            z0 = 'different for each port and/or frequency'
        
        info = f'{fname}\n'
        info += '-'*len(fname)+'\n\n'
        
        if len(comm)>0:
            for comm_line in comm.splitlines():
                info += comm_line.strip() + '\n'
            info += '\n'
        info += f'Ports: {n_ports}, reference impedance: {z0}\n'

        n_points_str = f'{n_pts:,.0f} point{"s" if n_pts!=0 else ""}'
        
        freq_steps = np.diff(sparam_file.nw.f)
        freq_equidistant = np.allclose(freq_steps,freq_steps[0])
        if freq_equidistant:
            freq_step = freq_steps[0]
            spacing_str =  f'{Si(freq_step,"Hz")} equidistant spacing'
        else:
            freq_arbitrary = True
            if np.all(sparam_file.nw.f != 0):
                freq_ratios = np.exp(np.diff(np.log(sparam_file.nw.f)))
                if np.allclose(freq_ratios,freq_ratios[0]):
                    freq_arbitrary = False
                    freq_step = np.mean(freq_steps)
                    freq_ratio = freq_ratios[0]
                    spacing_str = f'{freq_ratio:.4g}x logarithmic spacing, average spacing {Si(freq_step,"Hz")}'
            if freq_arbitrary:
                freq_step = np.mean(freq_steps)
                spacing_str =  f'non-equidistant spacing, average spacing {Si(freq_step,"Hz")}'
        
        info += f'Frequency range: {Si(f0,"Hz")} to {Si(f1,"Hz")}, {n_points_str}, {spacing_str}'
        info += '\n\n'

        info += fileinfo

        return info
    

    def show_error(self, error: "str|None", exception: Exception = None):
        if error:
            logging.error(error)
            self.ui_update_status_message('\u26A0 ' + error)
        else:
            self.ui_update_status_message('No problems found')
        if exception:
            logging.exception(exception)
    

    def update_plot(self):

        try:
            prev_xlim, prev_ylim = None, None
            if self.plot is not None:
                if self.plot.plot is not None:
                    try:
                        prev_xlim = self.plot.plot.get_xlim()
                        prev_ylim = self.plot.plot.get_ylim()
                    except:
                        pass
            
            self.ui_plot.clear()
            self.generated_expressions = ''
            self.plot = None

            self.show_error(None)              
            n_log_entries_before = len(LogHandler.inst().get_messages(logging.WARNING))

            data_expr_based = Settings.plot_mode==MainWindow.Mode.Expr

            enable_1st_y = (Settings.plot_unit != MainWindow.Unit.Off)
            enable_2nd_y = (Settings.plot_unit2 != MainWindow.Unit2.Off)
            if (Settings.plot_unit not in [MainWindow.Unit.Off, MainWindow.Unit.dB, MainWindow.Unit.LinMag, MainWindow.Unit.LogMag]):
                enable_2nd_y = False
            dual_y_axis = enable_1st_y and enable_2nd_y

            qty_db = (Settings.plot_unit == MainWindow.Unit.dB)
            qty_lin_mag = (Settings.plot_unit == MainWindow.Unit.LinMag)
            qty_log_mag = (Settings.plot_unit == MainWindow.Unit.LogMag)
            qty_re = (Settings.plot_unit in [MainWindow.Unit.ReIm, MainWindow.Unit.Real])
            qty_im = (Settings.plot_unit in [MainWindow.Unit.ReIm, MainWindow.Unit.Imag])
            
            polar = (Settings.plot_unit == MainWindow.Unit.ReImPolar)
            smith = (Settings.plot_unit in [MainWindow.Unit.SmithZ, MainWindow.Unit.SmithY])
            timedomain = (Settings.plot_unit in [MainWindow.Unit.Impulse, MainWindow.Unit.Step])
            stepresponse = (Settings.plot_unit == MainWindow.Unit.Step)
            tdr_z = (Settings.tdr_impedance)
            if Settings.plot_unit == MainWindow.Unit.SmithZ:
                smith_type = 'z'
            else:
                smith_type = 'y'
            
            if enable_2nd_y:
                qty_phase = (Settings.plot_unit2 in [MainWindow.Unit2.Phase, MainWindow.Unit2.Unwrap, MainWindow.Unit2.LinRem])
                unwrap_phase = (Settings.plot_unit2 == MainWindow.Unit2.Unwrap)
                remove_lin_phase = (Settings.plot_unit2 == MainWindow.Unit2.LinRem)
                qty_group_delay = (Settings.plot_unit2 == MainWindow.Unit2.GDelay)
            else:
                qty_phase = False
                unwrap_phase = False
                remove_lin_phase = False
                qty_group_delay = False
            
            common_plot_args = dict(show_legend=Settings.show_legend, hide_single_item_legend=Settings.hide_single_item_legend, shorten_legend=Settings.shorten_legend_items)

            if polar:
                self.plot = PlotHelper(self.ui_plot.figure, smith=False, polar=True, x_qty='Real', x_fmt=SiFmt(), x_log=False, y_qty='Imaginary', y_fmt=SiFmt(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), **common_plot_args)
            elif smith:
                smith_z = 1.0
                self.plot = PlotHelper(fig=self.ui_plot.figure, smith=True, polar=False, x_qty='', x_fmt=SiFmt(), x_log=False, y_qty='', y_fmt=SiFmt(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), smith_type=smith_type, smith_z=smith_z, **common_plot_args)
            else:
                y2q, y2f = None, None
                if timedomain:
                    xq,xf,xl = 'Time',SiFmt(unit='s',force_sign=True),False
                    if tdr_z:
                        yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(unit='Ω', force_sign=True),False
                    else:
                        yq,yf,yl = 'Step Response' if stepresponse else 'Impulse Response',SiFmt(force_sign=True),False
                else:
                    xq,xf,xl = 'Frequency',SiFmt(unit='Hz'),Settings.log_freq
                    if qty_re or qty_im:
                        yq,yf,yl = 'Level',SiFmt(unit='',use_si_prefix=False,force_sign=True),False
                    elif qty_lin_mag:
                        yq,yf,yl = 'Magnitude',SiFmt(unit='',use_si_prefix=False),False
                    elif qty_log_mag:
                        yq,yf,yl = 'Magnitude',SiFmt(unit=''),True
                    else:
                        yq,yf,yl = 'Magnitude',SiFmt(unit='dB',use_si_prefix=False,force_sign=True),False
                    if qty_phase:
                        if Settings.phase_unit=='deg':
                            y2q,y2f = 'Phase',SiFmt(unit='°',use_si_prefix=False,force_sign=True)
                        else:
                            y2q,y2f = 'Phase',SiFmt(use_si_prefix=False,force_sign=True)
                    elif qty_group_delay:
                        y2q,y2f = 'Group Delay',SiFmt(unit='s',force_sign=True)
                self.plot = PlotHelper(self.ui_plot.figure, False, False, xq, xf, xl, yq, yf, yl, y2q, y2f, **common_plot_args)


            def add_to_plot(f, sp, z0, name, style=None):

                if style is None:
                    style = '-'

                style2 = '-.'
                if style=='-':
                    style2 = '-.'
                elif style=='-.':
                    style2 = ':'
                if Settings.plot_mark_points:
                    style += 'o'
                    style2 += 'o'
                if dual_y_axis:
                    style_y2 = ':'
                else:
                    style_y2 = style
                
                def transform_phase(radians):
                    if Settings.phase_unit=='deg':
                        return radians * 180 / math.pi
                    return radians

                if polar or smith:
                    self.plot.add(np.real(sp), np.imag(sp), f, name, style)
                else:
                    if timedomain:
                        t,lev = sparam_to_timedomain(f, sp, step_response=stepresponse, shift=Settings.tdr_shift, window_type=Settings.window_type, window_arg=Settings.window_arg, min_size=Settings.tdr_minsize)
                        if tdr_z:
                            lev[lev==0] = 1e-20 # avoid division by zero in the next step
                            imp = z0 * (1+lev) / (1-lev) # convert to impedance
                            self.plot.add(t, np.real(imp), None, name, style)
                        else:
                            self.plot.add(t, lev, None, name, style)
                    elif qty_db:
                        self.plot.add(f, v2db(sp), None, name, style)
                    elif qty_lin_mag or qty_log_mag:
                        self.plot.add(f, np.abs(sp), None, name, style)
                    elif qty_re and qty_im:
                        self.plot.add(f, np.real(sp), None, name+' re', style)
                        self.plot.add(f, np.imag(sp), None, name+' im', style2)
                    elif qty_re:
                        self.plot.add(f, np.real(sp), None, name, style)
                    elif qty_im:
                        self.plot.add(f, np.imag(sp), None, name, style)
                    
                    if qty_phase:
                        if remove_lin_phase:
                            self.plot.add(f, transform_phase(scipy.signal.detrend(np.unwrap(np.angle(sp)),type='linear')), None, name, style_y2, prefer_2nd_yaxis=True)
                        elif unwrap_phase:
                            self.plot.add(f, transform_phase(np.unwrap(np.angle(sp))), None, name, style_y2, prefer_2nd_yaxis=True)
                        else:
                            self.plot.add(f, transform_phase(np.angle(sp)), None, name, style_y2, prefer_2nd_yaxis=True)
                    elif qty_group_delay:
                        self.plot.add(*group_delay(f,sp), None, name, style_y2, prefer_2nd_yaxis=True)
                    
            selected_files = self.get_selected_files()
            touched_files = []

            if data_expr_based:

                raw_exprs = self.ui_expression
                Settings.expression = raw_exprs

                ExpressionParser.touched_files = []
                ExpressionParser.eval(raw_exprs, self.files, selected_files, add_to_plot)  
                touched_files.extend(ExpressionParser.touched_files)

            else:

                if Settings.plot_mode == MainWindow.Mode.All:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif Settings.plot_mode == MainWindow.Mode.AllFwd:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif Settings.plot_mode == MainWindow.Mode.IL:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot()'
                elif Settings.plot_mode == MainWindow.Mode.IlFwd:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot()'
                elif Settings.plot_mode == MainWindow.Mode.RL:
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot()'
                elif Settings.plot_mode == MainWindow.Mode.S21:
                    self.generated_expressions += 'sel_nws().s(2,1).plot()'
                elif Settings.plot_mode == MainWindow.Mode.S11:
                    self.generated_expressions += 'sel_nws().s(1,1).plot()'
                elif Settings.plot_mode == MainWindow.Mode.S22:
                    self.generated_expressions += 'sel_nws().s(2,2).plot()'
                elif Settings.plot_mode == MainWindow.Mode.S33:
                    self.generated_expressions += 'sel_nws().s(3,3).plot()'
                elif Settings.plot_mode == MainWindow.Mode.S44:
                    self.generated_expressions += 'sel_nws().s(4,4).plot()'

                try:
                    ExpressionParser.eval(self.generated_expressions, self.files, selected_files, add_to_plot)  
                    self.show_error(None)              
                except Exception as ex:
                    logging.error(f'Unable to parse expressions: {ex} (trace: {traceback.format_exc()})')
                    self.ui_plot.clear()
                    self.show_error(f'ERROR: {ex}')
                
                touched_files = selected_files
            
            for f in touched_files:
                self.update_file_in_list(f)
            
            log_entries_after = len(LogHandler.inst().get_messages(logging.WARNING))
            n_new_entries = log_entries_after - n_log_entries_before
            if n_new_entries > 0:
                self.show_error(LogHandler.inst().get_messages(logging.WARNING)[-1])

            self.plot.render()
            self.plot.finish()

            if self.plot_axes_are_valid:
                if self.ui_lock_x and prev_xlim is not None:
                    self.plot.plot.set_xlim(prev_xlim)
                if self.ui_lock_y and prev_ylim is not None:
                    self.plot.plot.set_ylim(prev_ylim)

            self.ui_plot.draw()

            ## TODO: cursor dialog
            #if self.cursor_dialog is not None:
            #    self.cursor_dialog.clear()
            #    self.cursor_dialog.repopulate(self.plot.plots)
            
            self.plot_axes_are_valid = True

        except Exception as ex:
            self.ui_plot.clear()
            self.show_error(f'Plotting failed', ex)

