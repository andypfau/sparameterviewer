import matplotlib.backend_bases
import matplotlib.backend_bases
from .main_window_ui import MainWindowUi
from .helpers.log_handler import LogHandler
from .helpers.settings import Settings, ParamMode, PlotUnit, PlotUnit2, PhaseUnit, CursorSnap
from .tabular_dialog import TabularDialog
from .rl_dialog import RlDialog
from .settings_dialog import SettingsDialog, SettingsTab
from .filter_dialog import FilterDialog
from .text_dialog import TextDialog
from .log_dialog import LogDialog
from .axes_dialog import AxesDialog
from .about_dialog import AboutDialog
from .helpers.simple_dialogs import info_dialog, warning_dialog, error_dialog, exception_dialog, okcancel_dialog, yesno_dialog, open_directory_dialog, open_file_dialog, save_file_dialog
from .helpers.help import show_help
from lib.si import SiFmt
from lib import Clipboard
from lib import AppPaths
from lib import open_file_in_default_viewer, sparam_to_timedomain, get_sparam_name, group_delay, v2db, start_process, shorten_path, natural_sort_key
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
import scipy.signal
from typing import Optional, Callable



class MainWindow(MainWindowUi):

    MAX_DIRECTORY_HISTORY_SIZE = 10

    CURSOR_OFF_NAME = '—'

    TIMER_CURSORS_ID = 1
    TIMER_CURSORS_TIMEOUT_S = 10e-3

    MODE_NAMES = {
        ParamMode.All: 'All S-Parameters',
        ParamMode.AllFwd: 'All S-Parameters (reciprocal)',
        ParamMode.IL: 'Insertion Loss',
        ParamMode.IlFwd: 'Insertion Loss (reciprocal)',
        ParamMode.S21: 'Insertion Loss S21',
        ParamMode.RL: 'Return Loss / Impedance',
        ParamMode.S11: 'Return Loss S11',
        ParamMode.S22: 'Return Loss S22',
        ParamMode.S33: 'Return Loss S33',
        ParamMode.S44: 'Return Loss S44',
        ParamMode.Expr: 'Expression-Based',
    }

    UNIT_NAMES = {
        PlotUnit.Off: '—',
        PlotUnit.dB: 'dB',
        PlotUnit.LogMag: 'Log Mag',
        PlotUnit.LinMag: 'Lin Mag',
        PlotUnit.ReIm: 'Real+Imag',
        PlotUnit.Real: 'Real',
        PlotUnit.Imag: 'Imag',
        PlotUnit.ReImPolar: 'Polar',
        PlotUnit.SmithZ: 'Smith (Z)',
        PlotUnit.SmithY: 'Smith (Y)',
        PlotUnit.Impulse: 'Impulse Resp.',
        PlotUnit.Step: 'Step Resp.',
    }

    UNIT2_NAMES = {
        PlotUnit2.Off: '—',
        PlotUnit2.Phase: 'Phase',
        PlotUnit2.Unwrap: 'Unwrapped',
        PlotUnit2.LinRem: 'Lin. Removed',
        PlotUnit2.GDelay: 'Group Delay',
    }


    def __init__(self, filenames: list[str]):
        self.ready = False
        self.directories: list[str] = []
        self.files: list[SParamFile] = []
        self.generated_expressions = ''
        self.plot_mouse_down = False
        self.plot_axes_are_valid = False
        self._log_dialog: LogDialog|None = None
        self.cursor_event_queue: list[tuple] = []
        self.plot: PlotHelper|None = None

        super().__init__()

        self.ui_set_modes_list(list(MainWindow.MODE_NAMES.values()))
        self.ui_set_units_list(list(MainWindow.UNIT_NAMES.values()))
        self.ui_set_units2_list(list(MainWindow.UNIT2_NAMES.values()))
        self.ui_set_window_title(Info.AppName)

        self.apply_settings_to_ui()
        Settings.attach(self.on_settings_change)
        initial_paths = filenames
        if len(initial_paths) < 1:
            initial_paths = [AppPaths.get_default_file_dir()]
        self.load_path(*initial_paths, load_file_dirs=True)
        self.ready = True
        self.update_plot()


    def show(self):
        self.ui_show()


    def apply_settings_to_ui(self):
        def load_settings():
            try:
                self.ui_mode = MainWindow.MODE_NAMES[Settings.plot_mode]
                self.ui_unit = MainWindow.UNIT_NAMES[Settings.plot_unit]
                self.ui_unit2 = MainWindow.UNIT2_NAMES[Settings.plot_unit2]
                self.ui_expression = Settings.expression
                self.ui_show_legend = Settings.show_legend
                self.ui_hide_single_item_legend = Settings.hide_single_item_legend
                self.ui_shorten_legend = Settings.shorten_legend_items
                self.ui_mark_datapoints = Settings.plot_mark_points
                self.ui_filesys_visible = Settings.filesys_showfiles
                self.ui_filesys_showfiles = Settings.filesys_showfiles
                return None
            except Exception as ex:
                return ex
        loading_exception = load_settings()
        if loading_exception:
            logging.error('Error', f'Unable to load settings ({loading_exception}), trying again with clean settings')
            loading_exception = load_settings()
            load_settings()  # load again; this time no re-try
            logging.error('Error', f'Unable to load settings after reset ({loading_exception}), ignoring')


    @property
    def selected_files(self) -> list[SParamFile]:
        return [self.files[i] for i in self.ui_get_selected_fileview_indices()]


    @property
    def log_dialog(self) -> LogDialog:
        if not self._log_dialog:
            self._log_dialog = LogDialog(self)
        return self._log_dialog
    

    def on_template_button(self):

        def selected_file_names():
            return [file.name for file in self.selected_files]

        def set_expression(*expressions):
            current = self.ui_expression
            new = '\n'.join(expressions)
            for line in current.splitlines():
                if Settings.comment_existing_expr:
                    existing_line = '#' + line.strip() if not line.startswith('#') else line.strip()
                else:
                    existing_line = line
                if len(new)>0:
                    new += '\n'
                new += existing_line
            self.ui_expression = new
            self.ui_mode = MainWindow.MODE_NAMES[ParamMode.Expr]
            self.update_plot()
        
        def ensure_selected_file_count(op, n_required):
            n = len(selected_file_names())
            if op == '>=':
                if n < n_required:
                    error_dialog('Invalid operation', f'To use this template, select at least {n_required} file{"s" if n_required!=1 else ""}.')
                    return False
            elif op == '==':
                if n != n_required:
                    error_dialog('Invalid operation', f'To use this template, select exactly {n_required} file{"s" if n_required!=1 else ""}.')
                    return False
            else:
                raise ValueError()
            return True
        
        def as_currently_selected():
            if len(self.generated_expressions) < 1:
                info_dialog('Invalid operation', 'To use this template, select anything other than Expression-Based.')
                return
            set_expression(self.generated_expressions)
        
        def all_sparams():
            set_expression('sel_nws().s().plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def insertion_loss():
            set_expression('sel_nws().s(il_only=True).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def insertion_loss_reciprocal():
            set_expression('sel_nws().s(fwd_il_only=True).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def return_loss():
            set_expression('sel_nws().s(rl_only=True).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def vswr():
            set_expression('sel_nws().s(rl_only=True).vswr().plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def mismatch_loss():
            set_expression('sel_nws().s(rl_only=True).ml().plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]

        def quick11():
            set_expression('quick(11)')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def quick112122():
            set_expression('quick(11)', 'quick(21)', 'quick(22)')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def quick11211222():
            set_expression('quick(11)', 'quick(21)', 'quick(12)', 'quick(22)')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]

        def quick112122313233():
            set_expression('quick(11)', 'quick(21)', 'quick(12)', 'quick(22)', 'quick(31)', 'quick(32)', 'quick(33)')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.dB]
        
        def stability():
            set_expression('sel_nws().mu(1).plot() # should be > 1 for stable network',
                           'sel_nws().mu(2).plot() # should be > 1 for stable network')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def reciprocity():
            set_expression('sel_nws().reciprocity().plot() # should be 0 for reciprocal network')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def passivity():
            set_expression('sel_nws().passivity().plot() # should be <= 1 for passive network')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def losslessness():
            set_expression("sel_nws().losslessness('ii').plot() # should be 1 for lossless network",
                           "sel_nws().losslessness('ij').plot() # should be 0 for lossless network")
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def cascade():
            if not ensure_selected_file_count('>=', 2):
                return
            nws = ' ** '.join([f'nw(\'{n}\')' for n in selected_file_names()])
            set_expression(f'({nws}).s(2,1).plot()')
        
        def deembed1from2():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"((nw('{n1}').invert()) ** nw('{n2}')).s(2,1).plot()")
        
        def deembed2from1():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"(nw('{n1}') ** (nw('{n2}').invert())).s(2,1).plot()")
        
        def deembed2from1flipped():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"(nw('{n1}') ** (nw('{n2}').flip().invert())).s(2,1).plot()")
        
        def deembed2xthru():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"((nw('{n1}').half(side=1)) ** nw('{n2}') **(nw('{n1}').half(side=2))).s(2,1).plot()")
        
        def ratio_of_two():
            if not ensure_selected_file_count('==', 2):
                return
            [n1, n2] = selected_file_names()
            set_expression(f"(nw('{n1}').s(2,1)/nw('{n2}').s(2,1)).plot()")
        
        def mixed_mode():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').s2m(['p1','p2','n1','n2']).s('dd21').plot()" for n in selected_file_names()]
            set_expression(*expressions)

        def z_renorm():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').renorm([50,75]).s(2,1).plot()" for n in selected_file_names()]
            set_expression(*expressions)

        def add_tline():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').add_tl(degrees=360,frequency_hz=1e9,port=2).s(2,1).plot()" for n in selected_file_names()]
            set_expression(*expressions)
        
        def z():
            set_expression('sel_nws().z(any,any).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def y():
            set_expression('sel_nws().y(any,any).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def abcd():
            set_expression('sel_nws().abcd(any,any).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def t():
            set_expression('sel_nws().t(any,any).plot()')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.LinMag]
        
        def stability_circles():
            set_expression('sel_nws().plot_stab(frequency_hz=1e9,port=2)')
            self.ui_unit = MainWindow.UNIT_NAMES[PlotUnit.SmithZ]

        def all_selected():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').s().plot()" for n in selected_file_names()]
            set_expression(*expressions)
        
        self.ui_show_template_menu({
            'As Currently Selected': as_currently_selected,
            None: None,
            'S-Parameters': {
                'All S-Parameters': all_sparams,
                'Insertion Loss': insertion_loss,
                'Insertion Loss (reciprocal)': insertion_loss_reciprocal,
                'Return Loss': return_loss,
                'VSWR': vswr,
                'Mismatch Loss': mismatch_loss,
                None: None,
                'S11': quick11,
                'S11, S21, S22': quick112122,
                'S11, S21, S12, S22': quick11211222,
                'S11, S21, S22, S31, S32, S33': quick112122313233,
            },
            'Other Parameters': {
                'Z-Matrix (Impedance)': z,
                'Y-Matrix (Admittance)': y,
                'ABCD-Matrix (Cascade; 2-Port Only)': abcd,
                'T-Matrix (Scattering Transfer; Even Port Numbers Only)': t,
            },
            'Network Analysis': {
                'Stability (2-Port Only)': stability,
                'Stability Circles (2-Port Only)': stability_circles,
                'Reciprocity (2-Port or Higher Only)': reciprocity,
                'Passivity': passivity,
                'Losslessness': losslessness,
            },
            'Operations on Selected Networks': {
                'Single-Ended to Mixed-Mode': mixed_mode,
                'Impedance Renormalization': z_renorm,
                'Add Line To Network': add_tline,
                None: None,
                'Just Plot All Selected Files': all_selected,
            },
            'Operations on Two Selected Networks': {
                'De-Embed 1st Network from 2nd': deembed1from2,
                'De-Embed 2nd Network from 1st': deembed2from1,
                'De-Embed 2nd (Flipped) Network from 1st': deembed2from1flipped,
                'Treat 1st as 2xTHRU, De-Embed from 2nd': deembed2xthru,
                'Ratio of Two Networks': ratio_of_two,
            },
            'Operations on Two or More Selected Networks': {
                'Cascade Selected Networks': cascade,
            },
        })


    def on_select_mode(self):
        for mode,name in MainWindow.MODE_NAMES.items():
            if name==self.ui_mode:
                Settings.plot_mode = mode
                self.prepare_cursors()
                self.update_plot()
                return


    def on_select_unit(self):
        for unit,name in MainWindow.UNIT_NAMES.items():
            if name==self.ui_unit:
                Settings.plot_unit = unit
                
                # different kind of chart -> axes scale is probably no longer valid
                self.invalidate_axes_lock(update=False)

                # only allow phase in specific combinations
                if Settings.plot_unit not in [PlotUnit.Off, PlotUnit.dB, PlotUnit.LinMag, PlotUnit.LogMag]:
                    self.ui_unit2 = MainWindow.UNIT2_NAMES[PlotUnit2.Off]

                self.prepare_cursors()
                self.update_plot()
    

    def on_select_unit2(self):
        for unit,name in MainWindow.UNIT2_NAMES.items():
            if name==self.ui_unit2:
                Settings.plot_unit2 = unit
                
                # different kind of chart -> axes scale is probably no longer valid
                self.invalidate_axes_lock(update=False)

                if Settings.plot_unit not in [PlotUnit.Off, PlotUnit.dB, PlotUnit.LinMag, PlotUnit.LogMag]:
                    self.ui_unit2 = MainWindow.UNIT2_NAMES[PlotUnit2.Off]
                    return # no phase allowed

                self.prepare_cursors()
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
        
        def make_load_function(dir):
            def load():
                if not pathlib.Path(dir).exists():
                    error_dialog('Loaing Failed', 'Cannot load recent directory.', f'<{dir}> does not exist any more')
                    self.update_most_recent_directories_menu()  # this will remove stale paths
                    return
                self.load_path(dir, append=Settings.history_appends)
            return load
        
        def path_for_display(path):
            MAX_LEN = 80
            filename = pathlib.Path(path).name
            directory = str(pathlib.Path(path).parent)
            short_directory = shorten_path(directory, MAX_LEN)
            return f'{filename} ({short_directory})'
        
        def history_dir_valid(dir: str):
            try:
                return pathlib.Path(dir).exists()
            except:
                return True
        entries = [(path_for_display(path), make_load_function(path)) for path in Settings.last_directories if history_dir_valid(path)]
        self.ui_update_files_history(entries)


    def add_to_most_recent_directories(self, dir: str):
        if dir in Settings.last_directories:
            idx = Settings.last_directories.index(dir)
            del Settings.last_directories[idx]
        
        Settings.last_directories.insert(0, dir)
        
        while len(Settings.last_directories) > MainWindow.MAX_DIRECTORY_HISTORY_SIZE:
            del Settings.last_directories[-1]
        
        self.update_most_recent_directories_menu()

    
    def read_single_file(self, path: str):
        abspath = str(pathlib.Path(path).absolute())

        def filetype_is_supported(path):
            ext = pathlib.Path(path).suffix
            return re.match(r'(\.ci?ti)|(\.s[0-9]+p)', ext, re.IGNORECASE)
    
        def archivetype_is_supported(path):
            ext = pathlib.Path(path).suffix
            return re.match(r'\.zip', ext, re.IGNORECASE)
    
        def load_file(filename, archive_path=None):
            try:
                file = SParamFile(filename, archive_path=archive_path)
                if file in self.files:
                    logging.debug(f'File <{filename}> is already loaded, ignoring')
                    return
                self.files.append(file)
            except Exception as ex:
                logging.warning(f'Unable to load file <{filename}>, ignoring: {ex}')
        
        try:
            if filetype_is_supported(abspath):
                load_file(abspath)
            elif Settings.extract_zip and archivetype_is_supported(abspath):
                try:
                    with zipfile.ZipFile(abspath, 'r') as zf:
                        for internal_name in zf.namelist():
                            if not filetype_is_supported(internal_name):
                                continue
                            load_file(internal_name, archive_path=abspath)
                except Exception as ex:
                    logging.warning(f'Unable to open zip file <{abspath}>: {ex}')
            else:
                logging.info(f'Unknown file type <{abspath}>, ignoring')

            self.files = list(sorted(self.files, key=lambda file: natural_sort_key(file.name)))
        
        except Exception as ex:
            logging.exception(f'Unable to load file <{abspath}>: {ex}')
            raise ex


    def read_all_files_in_directory(self, dir: str, recursive: bool = False):
        try:
            INITIAL_WARNING, WARNING_INCREMENT, MAX_WARNING = 100, 10, 1_000_000

            next_warning = INITIAL_WARNING
            n_files_loaded = 0
            def iter_files(dir: str) -> bool:
                nonlocal next_warning, n_files_loaded
                for path in pathlib.Path(dir).iterdir():
                    if path.is_file():
                        if n_files_loaded >= next_warning:
                            if next_warning < MAX_WARNING:
                                next_warning *= WARNING_INCREMENT
                            else:
                                next_warning += MAX_WARNING
                            if not yesno_dialog(
                                'Too Many Files',
                                f'Already loaded {n_files_loaded} files, with more to come. Continue?',
                                f'Will ask again after {next_warning} files'):
                                return False
                        self.read_single_file(str(path))
                        n_files_loaded += 1
                    elif path.is_dir() and recursive:
                        if not iter_files(str(path)):
                            return False
                return True
            iter_files(dir)
        
        except Exception as ex:
            logging.exception(f'Unable to load directory: {ex}')
            raise ex


    def reload_all_files(self):
        self.clear_loaded_files()
        for dir in self.directories:
            self.read_all_files_in_directory(dir)
        self.update_displayed_file_list()


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
    

    def update_displayed_file_list(self, selected_filenames: "list[str]" = [], only_select_first: bool = False):
        
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
        self.prepare_cursors()
    

    def load_path(self, *paths: str, append: bool = False, load_file_dirs: bool = False):
        append_next = append
        navigated = False
        new_files = []
        asked_for_archives = False
        for path_str in paths:
            path = pathlib.Path(path_str)
            if not path.exists():
                logging.error(f'Path <{path_str}> does not exist, ignoring')
                return
            
            if not navigated:
                abspath = str(path.absolute())
                self.ui_filesys_navigate(abspath)
                navigated = True
            
            def handle_dir(path: pathlib.Path, append: bool):
                absdir = str(path.absolute())
                self.add_to_most_recent_directories(absdir)
                if append:
                    if absdir not in self.directories:
                        self.directories.append(absdir)
                else:
                    self.clear_loaded_files()
                    self.directories = [absdir]
                self.read_all_files_in_directory(absdir)
            
            def handle_file(path: pathlib.Path, append: bool):
                abspath = str(path.absolute())
                absdir = str(path.parent)
                self.add_to_most_recent_directories(absdir)
                new_files.append(abspath)
                if append:
                    if absdir not in self.directories:
                        self.directories.append(absdir)
                else:
                    self.clear_loaded_files()
                    self.directories = [absdir]
                self.read_single_file(abspath)
            
            if path.is_dir():
                handle_dir(path, append_next)

            elif path.is_file():

                if (path.suffix.lower() == '.zip') and (not Settings.extract_zip):
                    if not asked_for_archives:
                        if yesno_dialog('Extract .zip Files', 'A .zip-file was selected, but the option to extract .zip-files is disabled. Do you want to enable it?'):
                            Settings.extract_zip = True
                        asked_for_archives = True
                    if not Settings.extract_zip:
                        continue # ignore this archive
                
                if load_file_dirs:
                    handle_dir(path.parent, append_next)
                else:
                    handle_file(path, append_next)
                
            
            else:
                logging.debug(f'Path <{path_str}> is niether file nor directory, ignoring')
            append_next = True
        
        if len(new_files) > 0:
            self.update_displayed_file_list(selected_filenames=new_files)
        elif not append:
            self.update_displayed_file_list(only_select_first=True)
        else:
            self.update_displayed_file_list()


    def on_open_directory(self):
        initial_dir = self.directories[0] if len(self.directories)>0 else None
        dir = open_directory_dialog(self, title='Open Directory', initial_dir=initial_dir)
        if not dir:
            return
        self.load_path(dir)


    def on_append_directory(self):
        initial_dir = self.directories[0] if len(self.directories)>0 else None
        dir = open_directory_dialog(self, title='Append Directory', initial_dir=initial_dir)
        if not dir:
            return
        self.load_path(dir, append=True)
    
    
    
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
    
    
    def on_statusbar_click(self):
        self.log_dialog.show_dialog()

    
    def on_settings(self):
        SettingsDialog(self).show_modal_dialog()
    
    
    def on_help(self):
        show_help()
    

    def on_about(self):
        AboutDialog(self).show_modal_dialog()


    def on_save_plot_image(self):

        if not self.ui_plot.figure:
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
            self.ui_plot.figure.savefig(filename)
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
            info_str += file.get_info_str()
        TextDialog(self).show_modal_dialog('File Info', text=info_str)
    
    
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
    

    def on_view_plaintext(self):
    
        if len(self.selected_files) < 1:
            error_dialog('Error', 'Nothing files selected')
            return

        selected_file = self.selected_files[0]
        title = f'Plaintext Data of <{selected_file.name}>'
        if selected_file.is_from_archive:
            TextDialog(self).show_modal_dialog(title, text=selected_file.get_plaintext())
        else:
            TextDialog(self).show_modal_dialog(title, file_path=selected_file.file_path)


    def on_open_externally(self):
    
        if len(self.selected_files) < 1:
            error_dialog('Error', 'Nothing files selected')
            return

        selected_files_nonarchive = [selected_file for selected_file in self.selected_files if not selected_file.is_from_archive]
        
        if len(selected_files_nonarchive) < 1:
            error_dialog('Error', 'All selected paths are archives')
            return
        
        try:
            start_process(Settings.ext_editor_cmd, *[file.file_path for file in selected_files_nonarchive])
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

    
    def on_mark_datapoints_changed(self):
        Settings.plot_mark_points = self.ui_mark_datapoints
        self.update_plot()


    def on_logx_changed(self):
        Settings.log_freq = self.ui_logx
        self.update_plot()


    def on_copy_image(self):

        if not self.ui_plot.figure:
            info_dialog('Nothing To Copy', 'Nothing to copy.')
            return

        try:
            Clipboard.copy_figure(self.ui_plot.figure)
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
        if self.ui_tab == MainWindowUi.Tab.Cursors:
            return
        self.ui_mode = MainWindow.MODE_NAMES[ParamMode.Expr]
        self.update_plot()

    
    def invalidate_axes_lock(self, update: bool = True):
        self.plot_axes_are_valid = False
        if update:
            self.update_plot()
    

    def on_settings_change(self):
        self.ui_filesys_showfiles = Settings.filesys_showfiles
        self.update_plot()
    
    
    def on_help_button(self):
        show_help('expressions.md')


    def on_tab_change(self):
        self.prepare_cursors()


    def on_filesys_doubleclick(self, path_str: str):
        path = pathlib.Path(path_str)
        if not path.exists():
            return
        abspath = str(path.absolute())
        if path.is_dir():
            self.load_path(abspath, append=Settings.filesys_doubleclick_appends)
        elif path.is_file():
            self.load_path(abspath, append=True)


    def on_filesys_contextmenu(self, path_str: str):
        path = pathlib.Path(path_str)
        if not path.exists():
            return None
        
        def switch_to_dir():
            self.load_path(path)
        def append_dir():
            self.load_path(path, append=True)
        def switch_to_file():
            self.load_path(path)
        def append_file():
            self.load_path(path, append=True)
        
        if path.is_dir():
            if Settings.filesys_doubleclick_appends:
                ps, pa = '', '*'
            else:
                ps, pa = '*', ''
            self.ui_filesys_show_contextmenu({ f'{ps}Switch to this Directory': switch_to_dir, f'{pa}Append this Directory': append_dir })
        elif path.is_file():
            self.ui_filesys_show_contextmenu({ 'Show Only This File': switch_to_file, '*Append this File': append_file })
    

    def on_filesys_select(self, path: str):
        self.ui_filesys_navigate(path)
    
        
    def on_pathbar_change(self, path: str):
        self.ui_filesys_navigate(path)


    def on_toggle_filesys(self):
        visible = not self.ui_filesys_visible
        Settings.filesys_showfiles = visible
        self.ui_filesys_visible = visible
        if visible:
            self.ui_tab = MainWindowUi.Tab.Files
    

    def on_filesys_visible_changed(self):
        Settings.filesys_showfiles = self.ui_filesys_visible


    def on_cursor_select(self):
        self.update_cursors()


    def on_cursor_trace_change(self):
        self.update_cursors()


    def on_auto_cursor_changed(self):
        self.update_cursors()


    def on_auto_cursor_trace_changed(self):
        self.update_cursors()


    def on_cursor_syncx_changed(self):
        self.update_cursors()


    def on_plot_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float], x2: Optional[float], y2: Optional[float]):
        # events are handled slower than they may come in, which leads to lag; queue them, then handle them in bulk
        self.cursor_event_queue.append((left_btn_pressed, left_btn_event, x, y, x2, y2))
        if not self.ui_is_timer_scheduled(MainWindow.TIMER_CURSORS_ID):
            self.ui_schedule_timer(MainWindow.TIMER_CURSORS_ID, MainWindow.TIMER_CURSORS_TIMEOUT_S)
    

    def on_timer_timeout(self, identifier: any):
        if identifier == MainWindow.TIMER_CURSORS_ID:
            self.on_cursor_timer_timeout()

    
    def on_cursor_timer_timeout(self):
        if len(self.cursor_event_queue) < 1:
            return
        event = self.cursor_event_queue.pop(0)
        while True:
            if len(self.cursor_event_queue) < 1:
                break
            next_event = self.cursor_event_queue[0]
            if event[0]!=next_event[0] or event[1]!=next_event[1]:
                break
            # two consecutive queued elements have the same mouse button state, so it was only a cursor move
            # ignore the 1st event, and only handle the 2nd (later) event.
            event = self.cursor_event_queue.pop(0)
            continue
        self.update_cursors(*event)


    def prepare_cursors(self):
        if self.ui_tab == MainWindowUi.Tab.Cursors:
            self.ui_plot.stop_user_action()
            if self.plot:
                self.plot.cursors[0].enable(False)
                self.plot.cursors[1].enable(False)
            self.ui_set_cursor_trace_list([MainWindow.CURSOR_OFF_NAME, *[plots.name for plots in self.plot.plots]])
            selected_files = self.selected_files
            if len(selected_files) > 0:
                self.ui_cursor1_trace = selected_files[0].name
        else:
            if self.plot:
                self.plot.cursors[0].enable(False)
                self.plot.cursors[1].enable(False)
                self.ui_plot.draw()


    def update_cursors(self, left_btn_pressed: bool = False, left_btn_event: bool = False, x: float = None, y: float = None, x2: float = None, y2: float = None):
        if self.ui_tab != MainWindowUi.Tab.Cursors or not self.plot:
            return
        
        # TODO: allow cursors on 2nd axis
        # - must hand over 2nd coordinate set, and 2nd axis with/height
        # - must remember cursor axis

        try:
            self.plot.cursors[0].enable(self.ui_cursor1_trace != MainWindow.CURSOR_OFF_NAME)
            self.plot.cursors[1].enable(self.ui_cursor1_trace != MainWindow.CURSOR_OFF_NAME)

            snap_y = Settings.cursor_snap == CursorSnap.Point
            
            if left_btn_pressed:

                plot_width, plot_height = 1.0, 1.0
                if self.plot:
                    try:
                        xlim, ylim = self.plot.plot.get_xlim(), self.plot.plot.get_ylim()
                        plot_width, plot_height = xlim[1]-xlim[0], ylim[1]-ylim[0]
                    except:
                        pass

                # find out which cursor to move
                if self.ui_auto_cursor and left_btn_event:
                    target_cursor_index, _ = self.plot.get_closest_cursor(x, y if snap_y else None, plot_width, plot_height)
                    if target_cursor_index is not None:
                        self.ui_cursor_index = target_cursor_index
                else:
                    target_cursor_index = self.ui_cursor_index
                
                # move the cursor
                if target_cursor_index is not None:

                    if self.ui_auto_cursor_trace:
                        plot, x, y, z = self.plot.get_closest_plot_point(x, y if snap_y else None, width=plot_width, height=plot_height)
                        if plot is not None:
                            if target_cursor_index==0:
                                self.ui_cursor1_trace = plot.name
                            else:
                                self.ui_cursor2_trace = plot.name
                    else:
                        selected_trace_name = self.ui_cursor1_trace if target_cursor_index==0 else self.ui_cursor2_trace
                        if selected_trace_name is not None:
                            plot, x, y, z = self.plot.get_closest_plot_point(x, y if snap_y else None, name=selected_trace_name, width=plot_width, height=plot_height)
                        else:
                            plot, x, y, z = None, None, None, None

                    if plot is not None:
                        target_cursor = self.plot.cursors[target_cursor_index]
                        target_cursor.set(x, y, z, enable=True, color=plot.color)
                        
                    if self.ui_cursor_syncx:
                        other_trace_name = self.ui_cursor2_trace if target_cursor_index==0 else self.ui_cursor1_trace
                        other_plot, x, y, z = self.plot.get_closest_plot_point(x, None, name=other_trace_name, width=plot_width, height=plot_height)
                        if other_plot is not None:
                            other_cursor_index = 1 - target_cursor_index
                            other_cursor = self.plot.cursors[other_cursor_index]
                            other_cursor.set(x, y, z, enable=True, color=other_plot.color)
            
            self.update_cursor_readout()
        except Exception as ex:
            logging.error(f'Cursor error: {ex}')
    
    
    def update_cursor_readout(self):
        if self.ui_tab != MainWindowUi.Tab.Cursors or not self.plot:
            self.ui_set_cursor_readouts()
            return

        readout_x1 = ''
        readout_y1 = ''
        readout_x2 = ''
        readout_y2 = ''
        readout_dx = ''
        readout_dy = ''
        xf = copy.copy(self.plot.x_fmt)
        yf = copy.copy(self.plot.y_left_fmt)
        zf = copy.copy(self.plot.z_fmt)
        xf.significant_digits += 3
        yf.significant_digits += 3
        if zf is not None:
            zf.significant_digits += 1
        if self.ui_cursor1_trace != MainWindow.CURSOR_OFF_NAME:
            x,y,z = self.plot.cursors[0].x, self.plot.cursors[0].y, self.plot.cursors[0].z
            if z is not None:
                readout_x1 = f'{Si(z,si_fmt=zf)}'
                readout_y1 = f'{Si(x,si_fmt=xf)}, {Si(y,si_fmt=yf)}'
            else:
                readout_x1 = f'{Si(x,si_fmt=xf)}'
                readout_y1 = f'{Si(y,si_fmt=yf)}'
        if self.ui_cursor2_trace != MainWindow.CURSOR_OFF_NAME:
            x,y,z = self.plot.cursors[1].x, self.plot.cursors[1].y, self.plot.cursors[1].z
            if z is not None:
                readout_x2 = f'{Si(z,si_fmt=zf)}'
                readout_y2 = f'{Si(x,si_fmt=xf)}, {Si(y,si_fmt=yf)}'
            else:
                readout_x2 = f'{Si(x,si_fmt=xf)}'
                readout_y2 = f'{Si(y,si_fmt=yf)}'
            if self.ui_cursor1_trace != MainWindow.CURSOR_OFF_NAME:
                dx = self.plot.cursors[1].x - self.plot.cursors[0].x
                dx_str = str(Si(dx,si_fmt=xf))
                if xf.unit=='s' and dx!=0:
                    dx_str += f' = {Si(1/dx,unit='Hz⁻¹')}'
                if yf.unit=='dB' or yf.unit=='°':
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    readout_dx = f'{dx_str}'
                    readout_dy = f'{Si(dy,si_fmt=yf)}'
                else:
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    dys = Si.to_significant_digits(dy, 4)
                    if self.plot.cursors[0].y==0:
                        rys = 'N/A'
                    else:
                        ry = self.plot.cursors[1].y / self.plot.cursors[0].y
                        rys = Si.to_significant_digits(ry, 4)
                    readout_dx = f'{dx_str}'
                    readout_dy = f'{dys} ({rys})'
        
        self.ui_set_cursor_readouts(readout_x1, readout_y1, readout_x2, readout_y2, readout_dx, readout_dy)
        self.ui_plot.draw()


    def show_error(self, error: "str|None", exception: Exception = None):
        if error:
            logging.error(error)
            self.ui_update_status_message('\u26A0 ' + error)
        else:
            self.ui_update_status_message('No problems found')
        if exception:
            logging.exception(exception)
    

    def update_plot(self):

        if not self.ready:
            return

        try:
            self.ready = False  # prevent update when dialog is initializing, and also prevent recursive calls

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

            data_expr_based = Settings.plot_mode==ParamMode.Expr

            enable_1st_y = (Settings.plot_unit != PlotUnit.Off)
            enable_2nd_y = (Settings.plot_unit2 != PlotUnit2.Off)
            if (Settings.plot_unit not in [PlotUnit.Off, PlotUnit.dB, PlotUnit.LinMag, PlotUnit.LogMag]):
                enable_2nd_y = False
            dual_y_axis = enable_1st_y and enable_2nd_y

            qty_db = (Settings.plot_unit == PlotUnit.dB)
            qty_lin_mag = (Settings.plot_unit == PlotUnit.LinMag)
            qty_log_mag = (Settings.plot_unit == PlotUnit.LogMag)
            qty_re = (Settings.plot_unit in [PlotUnit.ReIm, PlotUnit.Real])
            qty_im = (Settings.plot_unit in [PlotUnit.ReIm, PlotUnit.Imag])
            
            polar = (Settings.plot_unit == PlotUnit.ReImPolar)
            smith = (Settings.plot_unit in [PlotUnit.SmithZ, PlotUnit.SmithY])
            timedomain = (Settings.plot_unit in [PlotUnit.Impulse, PlotUnit.Step])
            stepresponse = (Settings.plot_unit == PlotUnit.Step)
            tdr_z = (Settings.tdr_impedance)
            if Settings.plot_unit == PlotUnit.SmithZ:
                smith_type = 'z'
            else:
                smith_type = 'y'
            
            if enable_2nd_y:
                qty_phase = (Settings.plot_unit2 in [PlotUnit2.Phase, PlotUnit2.Unwrap, PlotUnit2.LinRem])
                unwrap_phase = (Settings.plot_unit2 == PlotUnit2.Unwrap)
                remove_lin_phase = (Settings.plot_unit2 == PlotUnit2.LinRem)
                qty_group_delay = (Settings.plot_unit2 == PlotUnit2.GDelay)
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
                self.plot = PlotHelper(figure=self.ui_plot.figure, smith=True, polar=False, x_qty='', x_fmt=SiFmt(), x_log=False, y_qty='', y_fmt=SiFmt(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFmt(unit='Hz'), smith_type=smith_type, smith_z=smith_z, **common_plot_args)
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
                        if Settings.phase_unit==PhaseUnit.Radians:
                            y2q,y2f = 'Phase',SiFmt(use_si_prefix=False,force_sign=True)
                        else:
                            y2q,y2f = 'Phase',SiFmt(unit='°',use_si_prefix=False,force_sign=True)
                    elif qty_group_delay:
                        y2q,y2f = 'Group Delay',SiFmt(unit='s',force_sign=True)
                self.plot = PlotHelper(self.ui_plot.figure, False, False, xq, xf, xl, yq, yf, yl, y2q, y2f, **common_plot_args)


            def add_to_plot(f, sp, z0, name, style: str = None, color: str = None, width: float = None, opacity: float = None):

                if np.all(np.isnan(sp)):
                    return

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

                kwargs = dict(width=width, color=color, opacity=opacity)
                
                def transform_phase(radians):
                    if Settings.phase_unit==PhaseUnit.Degrees:
                        return radians * 180 / math.pi
                    return radians

                if polar or smith:
                    self.plot.add(np.real(sp), np.imag(sp), f, name, style, **kwargs)
                else:
                    if timedomain:
                        t,lev = sparam_to_timedomain(f, sp, step_response=stepresponse, shift=Settings.tdr_shift, window_type=Settings.window_type, window_arg=Settings.window_arg, min_size=Settings.tdr_minsize)
                        if tdr_z:
                            lev[lev==0] = 1e-20 # avoid division by zero in the next step
                            imp = z0 * (1+lev) / (1-lev) # convert to impedance
                            self.plot.add(t, np.real(imp), None, name, style, **kwargs)
                        else:
                            self.plot.add(t, lev, None, name, style, **kwargs)
                    elif qty_db:
                        self.plot.add(f, v2db(sp), None, name, style, **kwargs)
                    elif qty_lin_mag or qty_log_mag:
                        self.plot.add(f, np.abs(sp), None, name, style, **kwargs)
                    elif qty_re and qty_im:
                        self.plot.add(f, np.real(sp), None, name+' re', style, **kwargs)
                        self.plot.add(f, np.imag(sp), None, name+' im', style2, **kwargs)
                    elif qty_re:
                        self.plot.add(f, np.real(sp), None, name, style, **kwargs)
                    elif qty_im:
                        self.plot.add(f, np.imag(sp), None, name, style, **kwargs)
                    
                    if qty_phase:
                        if remove_lin_phase:
                            self.plot.add(f, transform_phase(scipy.signal.detrend(np.unwrap(np.angle(sp)),type='linear')), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                        elif unwrap_phase:
                            self.plot.add(f, transform_phase(np.unwrap(np.angle(sp))), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                        else:
                            self.plot.add(f, transform_phase(np.angle(sp)), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                    elif qty_group_delay:
                        self.plot.add(*group_delay(f,sp), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                    
            selected_files = self.get_selected_files()
            touched_files = []

            if data_expr_based:

                raw_exprs = self.ui_expression
                Settings.expression = raw_exprs

                ExpressionParser.touched_files = []
                ExpressionParser.eval(raw_exprs, self.files, selected_files, add_to_plot)  
                touched_files.extend(ExpressionParser.touched_files)

            else:

                if Settings.plot_mode == ParamMode.All:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif Settings.plot_mode == ParamMode.AllFwd:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot(style="-")\n'
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot(style="--")'
                elif Settings.plot_mode == ParamMode.IL:
                    self.generated_expressions += 'sel_nws().s(il_only=True).plot()'
                elif Settings.plot_mode == ParamMode.IlFwd:
                    self.generated_expressions += 'sel_nws().s(fwd_il_only=True).plot()'
                elif Settings.plot_mode == ParamMode.RL:
                    self.generated_expressions += 'sel_nws().s(rl_only=True).plot()'
                elif Settings.plot_mode == ParamMode.S21:
                    self.generated_expressions += 'sel_nws().s(2,1).plot()'
                elif Settings.plot_mode == ParamMode.S11:
                    self.generated_expressions += 'sel_nws().s(1,1).plot()'
                elif Settings.plot_mode == ParamMode.S22:
                    self.generated_expressions += 'sel_nws().s(2,2).plot()'
                elif Settings.plot_mode == ParamMode.S33:
                    self.generated_expressions += 'sel_nws().s(3,3).plot()'
                elif Settings.plot_mode == ParamMode.S44:
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

            if self.plot_axes_are_valid:
                if self.ui_lock_x and prev_xlim is not None:
                    self.plot.plot.set_xlim(prev_xlim)
                if self.ui_lock_y and prev_ylim is not None:
                    self.plot.plot.set_ylim(prev_ylim)

            self.ui_plot.draw()

            self.plot_axes_are_valid = True

        except Exception as ex:
            self.ui_plot.clear()
            self.show_error(f'Plotting failed', ex)

        finally:
            self.ready = True
