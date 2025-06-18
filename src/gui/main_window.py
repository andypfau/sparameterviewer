from .main_window_ui import MainWindowUi
from .helpers.log_handler import LogHandler
from .helpers.simple_dialogs import info_dialog, warning_dialog, error_dialog, exception_dialog, okcancel_dialog, yesno_dialog, open_directory_dialog, open_file_dialog, save_file_dialog, custom_buttons_dialog
from .helpers.help import show_help
from .components.param_selector import ParamSelector
from .components.plot_widget import PlotWidget
from .components.filesys_browser import FilesysBrowserItemType
from .tabular_dialog import TabularDialog
from .rl_dialog import RlDialog
from .settings_dialog import SettingsDialog, SettingsTab
from .filter_dialog import FilterDialog, FilterDialogUi
from .text_dialog import TextDialog
from .log_dialog import LogDialog
from .about_dialog import AboutDialog

import matplotlib.backend_bases
import matplotlib.backend_bases
from lib.si import SiFormat
from lib import Clipboard
from lib import AppPaths
from lib import sparam_to_timedomain, group_delay, v2db, start_process, shorten_path, is_ext_supported_archive, is_ext_supported_file, find_files_in_archive, get_unique_id, any_common_elements, string_to_enum, enum_to_string, is_running_from_binary, choose_smart_db_scale
from lib import SiValue
from lib import SParamFile
from lib import PlotHelper
from lib import ExpressionParser, DefaultAction
from lib import PathExt
from lib import Settings, PlotType, PhaseProcessing, PhaseUnit, CursorSnap, ColorAssignment, Parameters, YQuantity, TdResponse, SmithNorm
from info import Info

import pathlib
import math
import copy
import logging
import traceback
import time
import numpy as np
import re
import os
import scipy.signal
from typing import Optional, Callable



class MainWindow(MainWindowUi):

    CURSOR_OFF_NAME = '—'

    TIMER_INITIALIZATION_ID, TIMER_INITIALIZATION_TIMEOUT_S = get_unique_id(), 0.2
    TIMER_CURSORUPDATE_ID, TIMER_CURSOR_UPDATE_TIMEOUT_S = get_unique_id(), 25e-3
    TIMER_PLOT_UPDATE_ID, TIMER_PLOT_UPDATE_TIMEOUT_S = get_unique_id(), 10e-3
    TIMER_CLEAR_LOAD_COUNTER_ID, TIMER_CLEAR_LOAD_COUNTER_TIMEOUT_S = get_unique_id(), 0.5
    TIMER_RESCALE_GUI_ID, TIMER_RESCALE_GUI_TIMEOUT_S = get_unique_id(), 0.5

    COLOR_ASSIGNMENT_NAMES = {
        ColorAssignment.Default: 'Individual',
        ColorAssignment.ByParam: 'By Parameter',
        ColorAssignment.ByFile: 'By File',
        ColorAssignment.ByFileLoc: 'By Location',
        ColorAssignment.Monochrome: 'Monochrome',
    }


    def __init__(self, filenames: list[str]):
        self.ready = False
        self.directories: list[str] = []
        self.files: dict[PathExt,SParamFile] = {}
        self.generated_expressions = ''
        self.plot_mouse_down = False
        self.plot_axes_are_valid = False
        self._log_dialog: LogDialog|None = None
        self.cursor_event_queue: list[tuple] = []
        self.plot: PlotHelper|None = None
        self.sparamfile_list_t_start: float = -1
        self.sparamfile_list_aborted = False
        self.sparamfile_load_t_start: float = -1
        self.sparamfile_load_aborted = False
        self._last_cursor_x = [0, 0]
        self._last_cursor_trace = ['', '']
        self._smartscale_set_y = False
        self._saved_nw_name_for_template: str|None = None

        super().__init__()
        
        LogHandler.inst().attach(self.on_log_entry)

        self.clear_list_counter()
        self.clear_load_counter()
        def before_load_sparamfile(path: PathExt) -> bool:
            return self.before_load_sparamfile(path)
        def after_load_sparamfile(path: PathExt) -> bool:
            return self.after_load_sparamfile(path)
        SParamFile.before_load = before_load_sparamfile
        SParamFile.after_load = after_load_sparamfile

        self.ui_set_window_title(Info.AppName)
        self.ui_set_color_assignment_options(list(MainWindow.COLOR_ASSIGNMENT_NAMES.values()))

        self.apply_settings_to_ui()

        initial_paths = filenames
        if len(initial_paths) < 1:
            if len(Settings.path_history) > 0:
                if len(Settings.path_history) > 0:
                    dir = Settings.path_history[0]
                    if os.path.exists(dir):
                        initial_paths = [dir]
        if len(initial_paths) < 1:
            initial_paths = [AppPaths.get_default_file_dir()]
        self._initial_selection = []
        for path_str in initial_paths:
            path = PathExt(path_str)
            if path.is_file():
                self._initial_selection.append(path)
                path = path.parent
            self.add_to_most_recent_paths(str(path))
            self.ui_filesys_browser.add_toplevel(path)
        self.ui_schedule_oneshot_timer(MainWindow.TIMER_INITIALIZATION_ID, MainWindow.TIMER_INITIALIZATION_TIMEOUT_S, self.finish_initialization)

        self.update_most_recent_paths_menu()
        Settings.attach(self.on_settings_change)
        self.ready = True


    def show(self):
        self.ui_show()


    def apply_settings_to_ui(self):
        def load_settings():
            try:
                self.ui_param_selector.setSimplified(Settings.simplified_param_sel)
                self.ui_param_selector.setParams(Settings.plotted_params)
                self.ui_param_selector.setAllowExpressions(not Settings.simplified_no_expressions)
                self.ui_param_selector.setUseExpressions(Settings.use_expressions)
                self.ui_plot_selector.setPlotType(Settings.plot_type)
                self.ui_plot_selector.setYQuantity(Settings.plot_y_quantitiy)
                self.ui_plot_selector.setY2Quantity(Settings.plot_y2_quantitiy)
                self.ui_plot_selector.setTdResponse(Settings.td_response)
                self.ui_plot_selector.setPhaseUnit(Settings.phase_unit)
                self.ui_plot_selector.setPhaseProcessing(Settings.phase_processing)
                self.ui_plot_selector.setSmithNorm(Settings.smith_norm)
                self.ui_plot_selector.setTdImpedance(Settings.tdr_impedance)
                self.ui_plot_selector.setTdWindow(Settings.window_type)
                self.ui_plot_selector.setTdWindowArg(Settings.window_arg)
                self.ui_plot_selector.setTdShift(Settings.tdr_shift)
                self.ui_plot_selector.setTdMinsize(Settings.tdr_minsize)
                self.ui_plot_selector.setSimplified(Settings.simplified_plot_sel)
                self.ui_filesys_browser.setSimplified(Settings.simplified_browser)
                self.ui_enable_expressions(Settings.use_expressions)
                self.ui_show_expressions(not Settings.simplified_no_expressions)
                self.ui_color_assignment = enum_to_string(Settings.color_assignment, MainWindow.COLOR_ASSIGNMENT_NAMES)
                self.ui_semitrans_traces = Settings.plot_semitransparent
                self.ui_trace_opacity = Settings.plot_semitransparent_opacity
                self.ui_maxlegend = Settings.max_legend_items
                self.ui_expression = Settings.expression
                self.ui_show_legend = Settings.show_legend
                self.ui_hide_single_item_legend = Settings.hide_single_item_legend
                self.ui_shorten_legend = Settings.shorten_legend_items
                self.ui_mark_datapoints = Settings.plot_mark_points
                self.ui_logx = Settings.log_x
                self.ui_logy = Settings.log_y
                self.ui_smart_db = Settings.smart_db_scaling
                self.ui_layout = Settings.mainwindow_layout
                self.ui_filesys_browser.show_archives = Settings.extract_zip
                self.ui_show_smart_db = self.ui_plot_selector.plotType()==PlotType.Cartesian and self.ui_plot_selector.yQuantity()==YQuantity.Decibels
                return None
            except Exception as ex:
                return ex
        loading_exception = load_settings()
        if loading_exception:
            logging.error('Error', f'Unable to load settings ({loading_exception}), trying again with clean settings')
            loading_exception = load_settings()
            load_settings()  # load again; this time no re-try
            logging.error('Error', f'Unable to load settings after reset ({loading_exception}), ignoring')


    def finish_initialization(self):

        if is_running_from_binary():
            try:
                import pyi_splash
                pyi_splash.close()

                # attempt to fix the bug that under Windows, the main dialog goes to the background once
                #   the splash screen is closed
                try:
                    self._raise()
                except:
                    pass
                try:
                    self.activateWindow()
                except:
                    pass
            except:
                pass

        if len(self._initial_selection) > 0:
            self.ui_filesys_browser.selected_files = self._initial_selection
        else:
            self.ui_filesys_browser.select_first_file()


    def clear_list_counter(self):
        # TODO: this is not monitored anywhere!
        self.sparamfile_list_t_start = -1
        self.sparamfile_list_aborted = False


    def clear_load_counter(self):
        self.ui_show_abort_button(False)
        self.sparamfile_load_t_start = -1
        self.sparamfile_load_aborted = False


    def before_load_sparamfile(self, path: PathExt) -> bool:
        if self.sparamfile_load_aborted:
            return False
        if self.sparamfile_load_t_start < 0:
            self.sparamfile_load_t_start = time.monotonic()
        else:
            t_elapsed = time.monotonic() - self.sparamfile_load_t_start
            if t_elapsed >= Settings.warn_timeout_s:
                self.ui_show_abort_button(True)
                self.ui_update()
        return True
    
    
    def after_load_sparamfile(self, path: PathExt):
        if path not in self.files:
            return
        self.ui_filesys_browser.update_status(path, self.get_file_prop_str(self.files[path]))

    

    @property
    def log_dialog(self) -> LogDialog:
        if not self._log_dialog:
            self._log_dialog = LogDialog(self)
        return self._log_dialog


    def on_log_entry(self, record: LogHandler.Record):
        if record.level >= logging.WARNING:
            self.ui_show_status_message(record.message, record.level)
    

    def get_nw_name_for_template(self, path: PathExt) -> str:
        if path.is_in_arch():
            return path.arch_path_name
        else:
            return path.name
    
    
    def on_template_button(self):

        def selected_file_names():
            return [self.get_nw_name_for_template(file.path) for file in self.get_selected_files()]
        
        def get_reference_file_for_multifile_op() -> str|None:
            if self._saved_nw_name_for_template is None:
                info_dialog('Error', 'No reference network selected.', informative_text='Right-click a network in te fileview browser, and click "Save for Template". Then use this template again.')
                return None
            option = custom_buttons_dialog('Reference', 'How do you want to link to the reference network?',
                informative_text='Constant: insert name of reference network as constant literal.\nDynamic: use the `saved_nw()` function to refer to the currently saved network.',
                buttons=['Constant', 'Dynamic'])
            match option:
                case 0: return f'nw("{self._saved_nw_name_for_template}")'
                case 1: return f'saved_nw()'
            raise RuntimeError()

        def set_expression(*expressions):
            if Settings.simplified_no_expressions:
                return
            def comment_lines(lines: list[str]) -> list[str]:
                if not Settings.comment_existing_expr:
                    return lines
                result = []
                for line in lines:
                    line_stripped = line.strip()
                    if (line_stripped!='') and (not line_stripped.startswith('#')):
                        result.append('# ' + line_stripped)
                    else:
                        result.append(line)
                return result
            new_lines = '\n'.join([*expressions, *comment_lines(self.ui_expression.splitlines())])
            self.ui_expression = new_lines
            self.ui_param_selector.setUseExpressions(True)
            self.ui_enable_expressions(True)
            self.schedule_plot_update()
        
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
            set_expression(self.generated_expressions)

        def setup_plot(plot_type: PlotType|None = None, quantity: YQuantity|None = None):
            if plot_type:
                self.ui_plot_selector.setPlotType(plot_type)
            if quantity:
                self.ui_plot_selector.setYQuantity(quantity)

        def all_sparams():
            set_expression('sel_nws().s().plot()')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def insertion_loss():
            set_expression('sel_nws().s(il_only=True).plot()')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def insertion_loss_reciprocal():
            set_expression('sel_nws().s(fwd_il_only=True).plot()')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def return_loss():
            set_expression('sel_nws().s(rl_only=True).plot()')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def vswr():
            set_expression('sel_nws().s(rl_only=True).vswr().plot()')
            setup_plot(PlotType.Cartesian)
        
        def mismatch_loss():
            set_expression('sel_nws().s(rl_only=True).ml().plot()')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)

        def quick11():
            set_expression('quick(11)')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def quick112122():
            set_expression('quick(11)', 'quick(21)', 'quick(22)')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def quick11211222():
            set_expression('quick(11)', 'quick(21)', 'quick(12)', 'quick(22)')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)

        def quick112122313233():
            set_expression('quick(11)', 'quick(21)', 'quick(12)', 'quick(22)', 'quick(31)', 'quick(32)', 'quick(33)')
            setup_plot(PlotType.Cartesian, YQuantity.Decibels)
        
        def stability():
            set_expression('sel_nws().mu(1).plot() # should be > 1 for stable network',
                           'sel_nws().mu(2).plot() # should be > 1 for stable network')
            setup_plot(PlotType.Cartesian)
        
        def reciprocity():
            set_expression('sel_nws().reciprocity().plot() # should be 0 for reciprocal network')
            setup_plot(PlotType.Cartesian)
        
        def symmetry():
            set_expression('sel_nws().symmetry().plot() # should be 0 for symmetric network')
            setup_plot(PlotType.Cartesian)
        
        def passivity():
            set_expression('sel_nws().passivity().plot() # should be 0 for passive network')
            setup_plot(PlotType.Cartesian)
        
        def losslessness():
            set_expression('sel_nws().losslessness().plot() # should be 0 for lossless network')
            setup_plot(PlotType.Cartesian)
        
        def four_metrics():
            set_expression(
                'sel_nws().reciprocity().plot()  # should be 0 for reciprocal network\n' +
                'sel_nws().symmetry().plot()     # should be 0 for symmetric network\n' +
                'sel_nws().passivity().plot()    # should be 0 for passive network\n' +
                'sel_nws().losslessness().plot() # should be 0 for lossless network'
            )
            setup_plot(PlotType.Cartesian)
        
        def cascade():
            if not ensure_selected_file_count('>=', 2):
                return
            nws = ' ** '.join([f'nw(\'{n}\')' for n in selected_file_names()])
            set_expression(f'({nws}).s(2,1).plot()')
        
        def normalize_to_ref():
            if ref_nw := get_reference_file_for_multifile_op():
                set_expression(f'(sel_nws() / {ref_nw}).plot_sel_params()')
        
        def normalize_to_f():
            set_expression(f'sel_nws().sel_params().norm(at_f=10e9).plot()')
        
        def deembed_ref_from_others():
            if ref_nw := get_reference_file_for_multifile_op():
                set_expression(f'((~{ref_nw}) ** sel_nws()).plot_sel_params()')
        
        def deembed_ref_flipped_from_others():
            if ref_nw := get_reference_file_for_multifile_op():
                set_expression(f'(~({ref_nw}.flipped()) ** sel_nws()).plot_sel_params()')
        
        def from_others_deembed_ref():
            if ref_nw := get_reference_file_for_multifile_op():
                set_expression(f'(sel_nws() ** (~"{ref_nw}).plot_sel_params()')
        
        def from_others_deembed_ref_flipped():
            if ref_nw := get_reference_file_for_multifile_op():
                set_expression(f'(sel_nws() ** (~{ref_nw}).flipped)).plot_sel_params()')
        
        def deembed_ref_as_2xthru():
            if ref_nw := get_reference_file_for_multifile_op():
                set_expression(f"((~{ref_nw}).half(side=1)) ** sel_nws() ** (~{ref_nw}).half(side=2))).plot_sel_params()")
        
        def mixed_mode():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').s2m(['p1','p2','n1','n2']).s('dd21').plot()" for n in selected_file_names()]
            set_expression(*expressions)

        def z_renorm():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').renorm([50,75]).plot_sel_params()" for n in selected_file_names()]
            set_expression(*expressions)

        def add_tline():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').add_tl(degrees=360,frequency_hz=1e9,port=2).plot_sel_params()" for n in selected_file_names()]
            set_expression(*expressions)
        
        def z():
            set_expression('sel_nws().z(any,any).plot()')
            setup_plot(PlotType.Cartesian)
        
        def y():
            set_expression('sel_nws().y(any,any).plot()')
            setup_plot(PlotType.Cartesian)
        
        def abcd():
            set_expression('sel_nws().abcd(any,any).plot()')
            setup_plot(PlotType.Cartesian)
        
        def t():
            set_expression('sel_nws().t(any,any).plot()')
            setup_plot(PlotType.Cartesian)
        
        def stability_circles():
            set_expression('sel_nws().plot_stab(frequency_hz=1e9,port=2)')
            setup_plot(PlotType.Smith)

        def all_selected():
            if not ensure_selected_file_count('>=', 1):
                return
            expressions = [f"nw('{n}').s().plot()" for n in selected_file_names()]
            set_expression(*expressions)
        
        self.ui_show_template_menu([
            ('As Currently Selected', as_currently_selected),
            (None, None),
            ('S-Parameters', [
                ('All S-Parameters', all_sparams),
                ('Insertion Loss', insertion_loss),
                ('Insertion Loss (reciprocal)', insertion_loss_reciprocal),
                ('Return Loss', return_loss),
                ('VSWR', vswr),
                ('Mismatch Loss', mismatch_loss),
                (None, None),
                ('S11', quick11),
                ('S11, S21, S22', quick112122),
                ('S11, S21, S12, S22', quick11211222),
                ('S11, S21, S22, S31, S32, S33', quick112122313233),
            ]),
            ('Other Parameters', [
                ('Z-Matrix (Impedance)', z),
                ('Y-Matrix (Admittance)', y),
                ('ABCD-Matrix (Cascade; 2-Port Only)', abcd),
                ('T-Matrix (Scattering Transfer; Even Port Numbers Only)', t),
            ]),
            ('Network Analysis', [
                ('Stability (2-Port Only)', stability),
                ('Stability Circles (2-Port Only)', stability_circles),
                (None, None),
                ('Reciprocity (2-Port or Higher Only)', reciprocity),
                ('Symmmetry (2-Port or Higher Only)', symmetry),
                ('Passivity', passivity),
                ('Losslessness', losslessness),
                ('All of Above', four_metrics),
            ]),
            ('Operations on Individual Networks', [
                ('Normalize at Given Frequency', normalize_to_f),
                (None, None),
                ('Single-Ended to Mixed-Mode', mixed_mode),
                ('Impedance Renormalization', z_renorm),
                (None, None),
                ('Add Line To Network', add_tline),
                (None, None),
                ('Just Plot All Selected Files', all_selected),
            ]),
            ('Operations On Multiple Networks', [
                ('Cascade Selected Networks', cascade),
            ]),
            ('Operations With a Reference Network', [
                ('Normalize to Reference Network', normalize_to_ref),
                (None, None),
                ('De-Embed Reference Network From Others', deembed_ref_from_others),
                ('De-Embed Reference Network (Flipped) From Others', deembed_ref_flipped_from_others),
                ('From Others De-Embed Reference Network', from_others_deembed_ref),
                ('From Others De-Embed Reference Network (Flipped)', from_others_deembed_ref_flipped),
                (None, None),
                ('Treat Reference as 2xTHRU, De-Embed from Others', deembed_ref_as_2xthru),
            ]),
        ])


    def on_color_change(self):
        if self.ui_enable_trace_color_selector:
            Settings.color_assignment = string_to_enum(self.ui_color_assignment, MainWindow.COLOR_ASSIGNMENT_NAMES)
    

    def on_plottype_changed(self):
        if not self.ready:
            return
        Settings.plot_type = self.ui_plot_selector.plotType()
        Settings.phase_unit = self.ui_plot_selector.phaseUnit()
        Settings.phase_processing = self.ui_plot_selector.phaseProcessing()
        Settings.td_response = self.ui_plot_selector.tdResponse()
        Settings.window_type = self.ui_plot_selector.tdWindow()
        Settings.window_arg = self.ui_plot_selector.tdWindowArg()
        Settings.tdr_shift = self.ui_plot_selector.tdShift()
        Settings.tdr_minsize = self.ui_plot_selector.tdMinisize()
        Settings.smith_norm = self.ui_plot_selector.smithNorm()
        Settings.tdr_impedance = self.ui_plot_selector.tdImpedance()
        Settings.plot_y_quantitiy = self.ui_plot_selector.yQuantity()
        Settings.plot_y2_quantitiy = self.ui_plot_selector.y2Quantity()
        self.ui_show_smart_db = self.ui_plot_selector.plotType()==PlotType.Cartesian and self.ui_plot_selector.yQuantity()==YQuantity.Decibels

        self.invalidate_axes_lock(update=False)  # different kind of chart -> axes scale is probably no longer valid
        self.schedule_plot_update()


    def on_params_change(self):
        Settings.plotted_params = self.ui_param_selector.params()
        Settings.use_expressions = self.ui_param_selector.useExpressions()
        self.schedule_plot_update()
    

    def on_show_filter(self):
        result = FilterDialog(self).show_modal_dialog(list(sorted(self.files.keys())))
        currently_selected = self.ui_filesys_browser.selected_files
        match result.action:
            case FilterDialogUi.Action.Select:
                self.ui_filesys_browser.selected_files = result.files
            case FilterDialogUi.Action.Add:
                self.ui_filesys_browser.selected_files = list(set(currently_selected) | set(result.files))
            case FilterDialogUi.Action.Remove:
                self.ui_filesys_browser.selected_files = list(set(currently_selected) - set(result.files))
            case FilterDialogUi.Action.Toggle:
                self.ui_filesys_browser.selected_files = list(set(currently_selected) ^ set(result.files))
    

    def on_load_dir(self):
        title = 'Change Directory' if self.ui_filesys_browser.simplified() else 'Open Another Directory'
        dir = open_directory_dialog(self, title=title)
        if not dir:
            return
        path = PathExt(dir)
        self.add_to_most_recent_paths(str(path.absolute()))
        self.ui_filesys_browser.add_toplevel(path)


    def on_reload_all_files(self):
        self.reload_all_files()


    def update_most_recent_paths_menu(self):
        
        def make_load_function(path: str):
            def load():
                if not pathlib.Path(path).exists():
                    error_dialog('Loaing Failed', 'Cannot load recent path.', f'<{path}> does not exist any more')
                    self.update_most_recent_paths_menu()  # this will remove stale paths
                    return
                self.add_to_most_recent_paths(path)
                self.ui_filesys_browser.add_toplevel(PathExt(path))
            return load
        
        def path_for_display(path: str):
            MAX_LEN = 80
            filename = pathlib.Path(path).name
            directory = str(pathlib.Path(path).parent)
            short_directory = shorten_path(directory, MAX_LEN)
            return f'{filename} ({short_directory})'
        
        def history_dir_valid(path: str):
            try:
                return pathlib.Path(path).exists()
            except:
                return True
        
        entries = [(path_for_display(path), make_load_function(path)) for path in Settings.path_history if history_dir_valid(path)]
        self.ui_update_files_history(entries)


    def add_to_most_recent_paths(self, path: str):
        history = Settings.path_history

        if path in history:
            idx = history.index(path)
            del history[idx]
        
        history.insert(0, path)
        
        while len(history) > Settings.path_history_maxsize:
            del history[-1]
        
        Settings.path_history = history
        
        self.update_most_recent_paths_menu()


    def reload_all_files(self):
        try:
            self.ready = False
            self.clear_list_counter()
            self.ui_filesys_browser.refresh()
            self.files.clear()
            self.update_params_size()
        finally:
            self.ready = True
            self.schedule_plot_update()


    def get_file_prop_str(self, file: "SParamFile|None") -> str:
        try:
            if file:
                if file.loaded:
                    return f'{file.nw.number_of_ports}-port, {SiValue(min(file.nw.f),"Hz")} to {SiValue(max(file.nw.f),"Hz")}'
                elif file.error:
                    return '[loading failed]'
            return '[not loaded]'
        except:
            return '[loading failed]'

    

    def get_selected_files(self) -> "list[SParamFile]":
        result = []
        for path in self.ui_filesys_browser.selected_files:
            if path not in self.files:
                self.files[path] = SParamFile(path)
            result.append(self.files[path])
        return result
    
    
    def on_rl_calc(self):
        if len(self.files) < 1:
            error_dialog('No Files', 'No files to integrate.', 'Open some files first.')
            return
        all_selected_files = self.get_selected_files()
        selected_file = all_selected_files[0] if len(all_selected_files) >= 1 else None
        RlDialog(self).show_modal_dialog(self.files.values(), selected_file)


    def on_show_log(self):
        self.log_dialog.show_dialog()
    
    
    def on_statusbar_click(self):
        self.log_dialog.show_dialog()

    
    def on_settings(self):
        SettingsDialog(self).show_modal_dialog()
    
    
    def on_help(self):
        self.sparamfile_load_aborted = True
        #show_help()
    

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
            error_dialog('Error', 'Exporting failed.', detailed_text=str(ex))
    

    def on_file_info(self):
        if len(self.get_selected_files())<=0:
            error_dialog('Error', 'No file selected.')
            return

        info_str = ''
        for file in self.get_selected_files():
            if len(info_str)>0:
                info_str+= '\n\n\n'
            info_str += file.get_info_str()
        TextDialog(self).show_modal_dialog('File Info', text=info_str)
    
    
    def on_view_tabular(self):       
        
        datasets = []
        initial_selection = None
        all_selected_files = self.get_selected_files()
        for i,file in enumerate(self.files.values()):
            if (initial_selection is None) and (file in all_selected_files):
                initial_selection = i
            datasets.append(file)
        for plot in self.plot.plots:
            datasets.append(plot.data)
        
        TabularDialog(self).show_modal_dialog(datasets=datasets, initial_selection=initial_selection)
    

    def on_view_plaintext(self):
    
        if len(self.get_selected_files()) < 1:
            error_dialog('Error', 'Nothing files selected')
            return

        selected_file = self.get_selected_files()[0]
        title = f'Plaintext Data of <{selected_file.name}>'
        try:
            selected_file = self.get_selected_files()[0]
            title = f'Plaintext Data of <{selected_file.name}>'
            if selected_file.path.is_in_arch():
                TextDialog(self).show_modal_dialog(title, text=selected_file.get_plaintext())
            else:
                TextDialog(self).show_modal_dialog(title, file_path=selected_file.path)
        except Exception as ex:
            error_dialog('Error', 'Unable to load show plaintext.', detailed_text=str(ex))


    def on_open_externally(self):

        if len(self.get_selected_files()) < 1:
            error_dialog('Error', 'No files selected')
            return

        selected_files_nonarchive = [selected_file for selected_file in self.get_selected_files() if not selected_file.path.is_in_arch()]
        if len(selected_files_nonarchive) < 1:
            error_dialog('Error', 'All selected paths are archives')
            return
            
        if not SettingsDialog.ensure_external_editor_is_set(self):
            return
        
        try:
            start_process(Settings.ext_editor_cmd, *[str(file) for file in selected_files_nonarchive])
        except Exception as ex:
            error_dialog('Open File Externally', 'Unable to open file with external editor.', detailed_text=str(ex))
    

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
            error_dialog('Error', 'Loading expressions failed.', detailed_text=str(ex))
    

    def on_save_expressions(self):
        try:
            fn = save_file_dialog(self, title='Save Expressions', filetypes=[('Expressions','.py'),('Text','.txt'),('All Files','*')])
            if not fn:
                return
            with open(fn, 'w') as fp:
                fp.write(self.ui_expression.strip())
        except Exception as ex:
            error_dialog('Error', 'Saving expressions failed.', detailed_text=str(ex))
    

    def on_show_legend(self):
        Settings.show_legend = self.ui_show_legend
        self.schedule_plot_update()
    

    def on_semitrans_changed(self):
        Settings.plot_semitransparent = self.ui_semitrans_traces
        self.schedule_plot_update()
    
    
    def on_traceopacity_changed(self):
        Settings.plot_semitransparent_opacity = self.ui_trace_opacity
        self.schedule_plot_update()
    
    
    def on_maxlegend_changed(self):
        Settings.max_legend_items = self.ui_maxlegend
        self.schedule_plot_update()


    def on_hide_single_legend(self):
        Settings.hide_single_item_legend = self.ui_hide_single_item_legend
        self.schedule_plot_update()


    def on_shorten_legend(self):
        Settings.shorten_legend_items = self.ui_shorten_legend
        self.schedule_plot_update()

    
    def on_mark_datapoints_changed(self):
        Settings.plot_mark_points = self.ui_mark_datapoints
        self.schedule_plot_update()


    def on_logx_changed(self):
        Settings.log_x = self.ui_logx
        self.schedule_plot_update()


    def on_logy_changed(self):
        Settings.log_y = self.ui_logy
        self.schedule_plot_update()


    def on_copy_image(self):

        if not self.ui_plot.figure:
            info_dialog('Nothing To Copy', 'Nothing to copy.')
            return

        try:
            Clipboard.copy_figure(self.ui_plot.figure)
        except Exception as ex:
            error_dialog('Error', 'Copying plot to clipboard failed.', detailed_text=str(ex))
        
    
    def on_resize(self):
        self.ui_schedule_oneshot_timer(MainWindow.TIMER_RESCALE_GUI_ID, MainWindow.TIMER_RESCALE_GUI_TIMEOUT_S, self.after_resize, retrigger_behavior='postpone')
    

    def after_resize(self):
        try:
            self.ui_plot.draw()
        except:
            pass
    

    def on_lock_xaxis(self):
        self.ui_plot_tool = PlotWidget.Tool.Off
        if self.ui_xaxis_range.both_are_wildcard:
            (self.ui_xaxis_range.low, self.ui_xaxis_range.high) = self.plot.plot.get_xlim()
        else:
            self.ui_xaxis_range.both_are_wildcard = True
        self.schedule_plot_update()

    
    def on_lock_yaxis(self):
        self._smartscale_set_y = False
        self.ui_smart_db = False
        self.ui_plot_tool = PlotWidget.Tool.Off
        if self.ui_yaxis_range.both_are_wildcard:
            (self.ui_yaxis_range.low, self.ui_yaxis_range.high) = self.plot.plot.get_ylim()
        else:
            self.ui_yaxis_range.both_are_wildcard = True
        self.schedule_plot_update()


    def on_lock_both_axes(self):
        self._smartscale_set_y = False
        self.ui_smart_db = False
        self.ui_plot_tool = PlotWidget.Tool.Off
        if self.ui_xaxis_range.both_are_wildcard or self.ui_yaxis_range.both_are_wildcard:
            (self.ui_xaxis_range.low, self.ui_xaxis_range.high), (self.ui_yaxis_range.low, self.ui_yaxis_range.high) = self.plot.plot.get_xlim(), self.plot.plot.get_ylim()
        else:
            self.ui_xaxis_range.both_are_wildcard, self.ui_yaxis_range.both_are_wildcard = True, True
        self.schedule_plot_update()
    
    
    def on_smart_db(self):
        if not self.ui_smart_db:
            self.ui_yaxis_range.both_are_wildcard = True  # unlock axis
        Settings.smart_db_scaling = self.ui_smart_db
        self.schedule_plot_update()

    
    def on_xaxis_range_change(self):
        self.ui_smart_db = False
        self._smartscale_set_y = False
        self.schedule_plot_update()


    def on_yaxis_range_change(self):
        self.ui_smart_db = False
        self._smartscale_set_y = False
        self.schedule_plot_update()


    def on_update_plot(self):
        if self.ui_tab == MainWindowUi.Tab.Cursors:
            return
        if self.ui_tab == MainWindowUi.Tab.Expressions and not Settings.simplified_no_expressions:
            self.ui_param_selector.setUseExpressions(True)
            Settings.use_expressions = True
            self.ui_enable_expressions(True)
        self.schedule_plot_update()


    def on_update_expressions(self):
        if self.ui_tab == MainWindowUi.Tab.Cursors:
            return
        if Settings.simplified_no_expressions:
            return
        self.ui_param_selector.setUseExpressions(True)
        Settings.use_expressions = True
        self.ui_enable_expressions(True)
        self.schedule_plot_update()

    
    def invalidate_axes_lock(self, update: bool = True):
        self.plot_axes_are_valid = False
        if update:
            self.schedule_plot_update()
    

    def on_settings_change(self, attributes: list[str]):
        self.ui_filesys_browser.show_archives = Settings.extract_zip
        self.ui_layout = Settings.mainwindow_layout
        self.ui_plot_selector.setSimplified(Settings.simplified_plot_sel)
        self.ui_param_selector.setSimplified(Settings.simplified_param_sel)
        self.ui_param_selector.setAllowExpressions(not Settings.simplified_no_expressions)
        self.ui_show_expressions(not Settings.simplified_no_expressions)
        self.ui_enable_expressions(Settings.use_expressions)
        self.ui_filesys_browser.setSimplified(Settings.simplified_browser)

        if 'path_history_maxsize' in attributes:
            history = Settings.path_history
            while len(history) > Settings.path_history_maxsize:
                del history[-1]
            Settings.path_history = history
            self.update_most_recent_paths_menu()

        if any_common_elements(('show_legend','phase_unit','plot_unit','plot_unit2','hide_single_item_legend','shorten_legend_items',
                'log_x','log_y','expression','window_type','window_arg','tdr_shift','tdr_impedance','tdr_minsize',
                'plot_mark_points','color_assignment','treat_all_as_complex','singlefile_individualcolor'), attributes):
            self.schedule_plot_update()
    
    
    def on_help_button(self):
        show_help('expressions.md')


    def on_tab_change(self):
        self.ui_allow_plot_tool = self.ui_tab != MainWindowUi.Tab.Cursors
        self.prepare_cursors()


    def on_filesys_contextmenu(self, path: PathExt, toplevel_path: PathExt, item_type: FilesysBrowserItemType):
        
        def make_pin(new_path: PathExt):
            def pin():
                self.add_to_most_recent_paths(str(new_path))
                self.ui_filesys_browser.add_toplevel(new_path)
            return pin
        def make_unpin():
            def unpin():
                self.ui_filesys_browser.remove_toplevel(toplevel_path)
            return unpin
        def make_chroot(new_path: PathExt):
            def chroot():
                self.add_to_most_recent_paths(str(new_path))
                self.ui_filesys_browser.change_root(toplevel_path, new_path)
            return chroot
        def make_selall(file_path: PathExt):
            def selall():
                if file_path.is_dir():
                    files_in_path = [p for p in file_path.iterdir() if p.is_file() and is_ext_supported_file(p.suffix)]
                elif (file_path.is_file() and not file_path.is_in_arch() and is_ext_supported_archive(path.suffix)) or (file_path.is_in_arch()):
                    files_in_path = [p for p in find_files_in_archive(str(file_path)) if is_ext_supported_file(p.arch_path_suffix)]
                else:
                    files_in_path = [p for p in file_path.parent.iterdir() if p.is_file() and is_ext_supported_file(p.suffix)]
                if len(files_in_path) < 1:
                    return
                self.ui_filesys_browser.selected_files = [*files_in_path, *self.ui_filesys_browser.selected_files]
            return selall
        def make_copy_path(path: PathExt):
            def copypath():
                Clipboard.copy_string(str(path))
            return copypath
        def make_copy_name(path: PathExt):
            def copyname():
                if path.is_in_arch():
                    Clipboard.copy_string(path.arch_path_name)
                else:
                    Clipboard.copy_string(path.name)
            return copyname
        def make_save_for_template(path: PathExt):
            def savefortemplate():
                self._saved_nw_name_for_template = self.get_nw_name_for_template(path)
                if self.ui_param_selector.useExpressions():
                    self.schedule_plot_update()
            return savefortemplate

        menu = []
        is_toplevel = path == toplevel_path
        if item_type == FilesysBrowserItemType.File:
            if not self.ui_filesys_browser.simplified():
                if path.is_in_arch():  # file is inside archive
                    menu.append(('Pin this Archive', make_pin(PathExt(str(path)))))
                    menu.append(('Navigate to this Archive', make_chroot(PathExt(str(path)))))
                    menu.append((None, None))
                else:  # just some file
                    if toplevel_path != path.parent:
                        menu.append(('Pin this Directory', make_pin(path.parent)))
                        menu.append(('Navigate to this Directory', make_chroot(path.parent)))
                        menu.append((None, None))
            menu.append((f'Select All Files from Here', make_selall(path)))
            if not Settings.simplified_no_expressions:
                menu.append((None, None))
                menu.append((f'Copy Name', make_copy_name(path)))
                menu.append((f'Save for Template', make_save_for_template(path)))
        elif item_type in [FilesysBrowserItemType.Arch, FilesysBrowserItemType.Dir]:
            typename = 'Directory' if item_type==FilesysBrowserItemType.Dir else 'Archive'
            if not self.ui_filesys_browser.simplified():
                if is_toplevel:
                    menu.append((f'Unpin', make_unpin()))
                    menu.append((None, None))
                else:
                    if not self.ui_filesys_browser.simplified():
                        menu.append((f'Pin this {typename}', make_pin(path)))
                    menu.append((f'Navigate to this {typename}', make_chroot(path)))
                    menu.append((None, None))
            menu.append((f'Select All Files in Here', make_selall(path)))
            if not (self.ui_filesys_browser.simplified() and Settings.simplified_no_expressions):
                menu.append((None, None))
                menu.append((f'Copy Path', make_copy_path(path)))
        
        if len(menu) > 0:
            self.ui_filesys_show_contextmenu(menu)
    

    def on_filesys_files_changed(self):
        browser_paths = self.ui_filesys_browser.all_files

        # discard the files that are no longer displayed in the filebrowser
        for available_path in list(self.files.keys()):
            if available_path not in browser_paths:
                del self.files[available_path]
        
        # pre-load files that are newly displayed in the filebrowser
        for browser_path in browser_paths:
            if browser_path not in self.files:
                # pre-load, so that expressions can find them
                self.files[browser_path] = SParamFile(browser_path)
                # show preliminary status
                self.ui_filesys_browser.update_status(browser_path, self.get_file_prop_str(self.files[browser_path]))


    def on_filesys_selection_changed(self):
        self.update_params_size()
        self.schedule_plot_update()
    
    
    def on_cursor_x1_changed(self):
        self.update_cursor_xvalue(0, self.ui_cursor_x1.value)
    
    
    def on_cursor_x2_changed(self):
        self.update_cursor_xvalue(1, self.ui_cursor_x2.value)


    def on_cursor_select(self):
        self.update_cursors()


    def on_cursor_trace_change(self):
        if self.ui_tab != MainWindowUi.Tab.Cursors or not self.plot:
            return

        try:
            cursor_index = self.ui_cursor_index
            if not self.plot.cursors[cursor_index].enabled:
                return

            cursor = self.plot.cursors[cursor_index]
            trace_name = self.ui_cursor1_trace if cursor_index==0 else self.ui_cursor2_trace
            if trace_name == MainWindow.CURSOR_OFF_NAME:
                cursor.enable(False)
            else:
                plot_width, plot_height = self._get_plot_dimensions()
                plot, x, y, z = self.plot.get_closest_plot_point(self._last_cursor_x[cursor_index], None, name=trace_name, width=plot_width, height=plot_height)
                if plot is None:
                    return
                cursor.set(x, y, z, True, plot.color)

            self.update_cursor_readout()

        except Exception as ex:
            logging.error(f'Cursor error: {ex}')


    def on_auto_cursor_changed(self):
        self.update_cursors()


    def on_auto_cursor_trace_changed(self):
        self.update_cursors()


    def on_cursor_syncx_changed(self):
        if self.ui_tab != MainWindowUi.Tab.Cursors or not self.plot:
            return

        try:
            if not (self.plot.cursors[0].enabled and self.plot.cursors[0].enabled):
                return

            for cursor_index in [0,1]:
                cursor = self.plot.cursors[cursor_index]
                trace_name = self.ui_cursor1_trace if cursor_index==0 else self.ui_cursor2_trace
                plot_width, plot_height = self._get_plot_dimensions()
                plot, x, y, z = self.plot.get_closest_plot_point(self._last_cursor_x[cursor_index], None, name=trace_name, width=plot_width, height=plot_height)
                if plot is None:
                    continue
                cursor.set(x, y, z, True, plot.color)

            self.update_cursor_readout()

        except Exception as ex:
            logging.error(f'Cursor error: {ex}')


    def on_plot_mouse_event(self, left_btn_pressed: bool, left_btn_event: bool, x: Optional[float], y: Optional[float], x2: Optional[float], y2: Optional[float]):
        # events are handled slower than they may come in, which leads to lag; queue them, then handle them in bulk
        self.cursor_event_queue.append((left_btn_pressed, left_btn_event, x, y, x2, y2))
        self.ui_schedule_oneshot_timer(MainWindow.TIMER_CURSORUPDATE_ID, MainWindow.TIMER_CURSOR_UPDATE_TIMEOUT_S, self._on_plot_mouse_event_timed)
    

    def _on_plot_mouse_event_timed(self):
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
            self.ui_plot_tool = PlotWidget.Tool.Off

            self.ui_set_cursor_trace_list([MainWindow.CURSOR_OFF_NAME, *[plots.data.name for plots in self.plot.plots]])
            self.ui_cursor1_trace = self._last_cursor_trace[0]
            self.ui_cursor2_trace = self._last_cursor_trace[1]

            for cursor_index in [0,1]:
                cursor = self.plot.cursors[cursor_index]
                if self._last_cursor_trace[cursor_index] == MainWindow.CURSOR_OFF_NAME:
                    cursor.enable(False)
                else:
                    trace_name = self.ui_cursor1_trace if cursor_index==0 else self.ui_cursor2_trace
                    plot_width, plot_height = self._get_plot_dimensions()
                    plot, x, y, z = self.plot.get_closest_plot_point(self._last_cursor_x[cursor_index], None, name=trace_name, width=plot_width, height=plot_height)
                    if plot is None:
                        continue
                    cursor.set(x, y, z, True, plot.color)

            self.update_cursor_readout()

        else:
            if self.plot:
                self.plot.cursors[0].enable(False)
                self.plot.cursors[1].enable(False)
                self.ui_plot.draw()

    
    def _get_plot_dimensions(self) -> tuple[float,float]:
        if self.plot:
            try:
                xlim, ylim = self.plot.plot.get_xlim(), self.plot.plot.get_ylim()
                return xlim[1]-xlim[0], ylim[1]-ylim[0]
            except:
                pass
        return 1.0, 1.0

    
    def update_cursor_xvalue(self, cursor_index: int, value: float):
        if self.ui_tab != MainWindowUi.Tab.Cursors or not self.plot:
            return

        try:
            cursor = self.plot.cursors[cursor_index]
            trace_name = self.ui_cursor1_trace if cursor_index==0 else self.ui_cursor2_trace
            if trace_name == MainWindow.CURSOR_OFF_NAME:
                cursor.enable(False)
            else:
                plot_width, plot_height = self._get_plot_dimensions()
                plot, x, y, z = self.plot.get_closest_plot_point(value, None, name=trace_name, width=plot_width, height=plot_height)
                if plot is None:
                    return
                cursor.set(x, y, z, True, plot.color)

            self.update_cursor_readout()

        except Exception as ex:
            logging.error(f'Cursor error: {ex}')


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

                plot_width, plot_height = self._get_plot_dimensions()

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

        readout_x1 = SiValue(0)
        readout_y1 = ''
        readout_x2 = SiValue(0)
        readout_y2 = ''
        readout_dx = ''
        readout_dy = ''
        xf = copy.copy(self.plot.x_fmt)
        yf = copy.copy(self.plot.y_left_fmt)
        zf = copy.copy(self.plot.z_fmt)
        xf.digits += 3
        yf.digits += 3
        if zf is not None:
            zf.digits += 1
        if self.ui_cursor1_trace != MainWindow.CURSOR_OFF_NAME:
            x,y,z = self.plot.cursors[0].x, self.plot.cursors[0].y, self.plot.cursors[0].z
            self._last_cursor_x[0], self._last_cursor_trace[0] = x, self.ui_cursor1_trace
            if z is not None:
                readout_x1 = SiValue(z,spec=zf)
                readout_y1 = f'{SiValue(x,spec=xf)}, {SiValue(y,spec=yf)}'
            else:
                readout_x1 = SiValue(x,spec=xf)
                readout_y1 = f'{SiValue(y,spec=yf)}'
        else:
            self._last_cursor_trace[0] = ''
        if self.ui_cursor2_trace != MainWindow.CURSOR_OFF_NAME:
            x,y,z = self.plot.cursors[1].x, self.plot.cursors[1].y, self.plot.cursors[1].z
            self._last_cursor_x[1], self._last_cursor_trace[1] = x, self.ui_cursor2_trace
            if z is not None:
                readout_x2 = SiValue(z,spec=zf)
                readout_y2 = f'{SiValue(x,spec=xf)}, {SiValue(y,spec=yf)}'
            else:
                readout_x2 = SiValue(x,spec=xf)
                readout_y2 = f'{SiValue(y,spec=yf)}'
            if self.ui_cursor1_trace != MainWindow.CURSOR_OFF_NAME:
                dx = self.plot.cursors[1].x - self.plot.cursors[0].x
                dx_str = str(SiValue(dx,spec=xf))
                if xf.unit=='s' and dx!=0:
                    dx_str += f' = {SiValue(1/dx,unit='Hz⁻¹')}'
                if yf.unit=='dB' or yf.unit=='°':
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    readout_dx = f'{dx_str}'
                    readout_dy = f'{SiValue(dy,spec=yf)}'
                else:
                    dy = self.plot.cursors[1].y - self.plot.cursors[0].y
                    dys = SiFormat.to_significant_digits(dy, 4)
                    if self.plot.cursors[0].y==0:
                        rys = 'N/A'
                    else:
                        ry = self.plot.cursors[1].y / self.plot.cursors[0].y
                        rys = SiFormat.to_significant_digits(ry, 4)
                    readout_dx = f'{dx_str}'
                    readout_dy = f'{dys} ({rys})'
        else:
            self._last_cursor_trace[1] = ''
        
        self.ui_set_cursor_readouts(readout_x1, readout_y1, readout_x2, readout_y2, readout_dx, readout_dy)
        self.ui_plot.draw()
    

    def update_params_size(self):
        size = 0
        for file in self.get_selected_files():
            try:
                size = max(size, file.nw.number_of_ports)
            except:
                pass
        
        MIN_SIZE = 2
        self.ui_params_size = max(MIN_SIZE, size)
    

    def schedule_plot_update(self):
        self.ui_schedule_oneshot_timer(MainWindow.TIMER_PLOT_UPDATE_ID, MainWindow.TIMER_PLOT_UPDATE_TIMEOUT_S, self._after_plot_timeout)


    def _after_plot_timeout(self):
        self.prepare_cursors()
        self.update_plot()
    

    def update_plot(self):
        
        if not self.ready:
            return
        
        self.ui_abort_oneshot_timer(MainWindow.TIMER_RESCALE_GUI_ID)
        self.ui_abort_oneshot_timer(MainWindow.TIMER_CLEAR_LOAD_COUNTER_ID)

        try:
            self.ready = False  # prevent update when dialog is initializing, and also prevent recursive calls

            log_entries = LogHandler.inst().get_records(logging.WARNING)
            last_log_entry_at_start = log_entries[-1] if log_entries else None

            self.ui_plot.clear()
            self.generated_expressions = ''
            self.plot = None

            def map_opacity(x):
                return max(1e-3, min(1, x**2))  # tjis mapping makes adjustment of small values easier

            params = self.ui_param_selector.params()
            params_mask = self.ui_param_selector.paramMask() if params==Parameters.Custom else None
            use_expressions = self.ui_param_selector.useExpressions()
            plot_type = self.ui_plot_selector.plotType()
            y_qty = self.ui_plot_selector.yQuantity()
            y2_qty = self.ui_plot_selector.y2Quantity()
            tdr_z = self.ui_plot_selector.tdImpedance()
            tdr_resp = self.ui_plot_selector.tdResponse()
            tdr_shift = self.ui_plot_selector.tdShift()
            window_type = self.ui_plot_selector.tdWindow()
            window_arg = self.ui_plot_selector.tdWindowArg()
            tdr_minsize = self.ui_plot_selector.tdMinisize()
            phase_unit = self.ui_plot_selector.phaseUnit()
            phase_processing = self.ui_plot_selector.phaseProcessing()
            smith_norm = self.ui_plot_selector.smithNorm()
            smart_db_scaling = self.ui_smart_db
            log_x, log_y = self.ui_logx, self.ui_logy
            default_trace_opacity = map_opacity(self.ui_trace_opacity)
            
            common_plot_args = dict(show_legend=self.ui_show_legend, hide_single_item_legend=self.ui_hide_single_item_legend, shorten_legend=self.ui_shorten_legend, max_legend_items=self.ui_maxlegend)

            # initialize dummy data
            xq, xf, xl = '', SiFormat(), False
            yq, yf, yl = '', SiFormat(), False
            y2q, y2f = '', SiFormat()

            if plot_type == PlotType.Polar:
                self.plot = PlotHelper(self.ui_plot.figure, smith=False, polar=True, x_qty='Real', x_fmt=SiFormat(), x_log=False, y_qty='Imaginary', y_fmt=SiFormat(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFormat(unit='Hz'), **common_plot_args)
            elif plot_type == PlotType.Smith:
                smith_z = 1.0
                typ = 'y' if smith_norm==SmithNorm.Admittance else 'z'
                self.plot = PlotHelper(figure=self.ui_plot.figure, smith=True, polar=False, x_qty='', x_fmt=SiFormat(), x_log=False, y_qty='', y_fmt=SiFormat(), y_log=False, y2_fmt=None, y2_qty=None, z_qty='Frequency', z_fmt=SiFormat(unit='Hz'), smith_type=typ, smith_z=smith_z, **common_plot_args)
            elif plot_type == PlotType.TimeDomain:
                resp_name = 'Step Response' if tdr_resp==TdResponse.StepResponse else 'Impulse Response'
                xq,xf,xl = 'Time',SiFormat(unit='s',signed=True),False
                if tdr_z:
                    yq,yf,yl = resp_name,SiFormat(unit='Ω', signed=True),False
                else:
                    yq,yf,yl = resp_name,SiFormat(signed=True),False
                self.plot = PlotHelper(self.ui_plot.figure, False, False, xq, xf, xl, yq, yf, yl, y2q, y2f, **common_plot_args)
            else:
                
                xq,xf,xl = 'Frequency', SiFormat(unit='Hz'), log_x
                if y_qty in [YQuantity.Real, YQuantity.RealImag, YQuantity.Imag]:
                    yq,yf,yl = 'Level',SiFormat(unit='',prefixed=False,signed=True),log_y
                elif y_qty == YQuantity.Magnitude:
                    yq,yf,yl = 'Magnitude',SiFormat(unit='',prefixed=False),log_y
                elif y_qty == YQuantity.Decibels:
                    if log_y and Settings.verbose:
                        logging.info(f'Ignoring logarithmic Y-axis because Y-axis is in decibels')
                    yq,yf,yl = 'Magnitude',SiFormat(unit='dB',prefixed=False,signed=True),False
                
                if y2_qty == YQuantity.Phase:
                    if phase_unit == PhaseUnit.Radians:
                        y2q,y2f = 'Phase',SiFormat(prefixed=False,signed=True)
                    else:
                        y2q,y2f = 'Phase',SiFormat(unit='°',prefixed=False,signed=True)
                elif y2_qty == YQuantity.GroupDelay:
                    y2q,y2f = 'Group Delay',SiFormat(unit='s',signed=True)
                self.plot = PlotHelper(self.ui_plot.figure, False, False, xq, xf, xl, yq, yf, yl, y2q, y2f, **common_plot_args)

            available_colors = PlotWidget.get_color_cycle()
            next_color_index = 0
            color_mapping = {}
            
            all_plot_kwargs = []
            def add_to_plot_list(f, sp, z0, name, style: str = None, color: str = None, width: float = None, opacity: float = None, original_files: set[PathExt] = None, param_kind: str = None):
                nonlocal all_plot_kwargs
                all_plot_kwargs.append(dict(f=f, sp=sp, z0=z0, name=name, style=style, color=color, width=width, opacity=opacity, original_files=original_files, param_kind=param_kind))
                    
            selected_files = self.get_selected_files()

            plot_kwargs_rl, plot_kwargs_il = {}, {}
            if self.ui_semitrans_traces:
                plot_kwargs_rl['opacity'] = default_trace_opacity
                plot_kwargs_il['opacity'] = default_trace_opacity

            def make_args_str(*args, **kwargs):
                def fmt(x):
                    if isinstance(x, str):
                        return f'"{x}"'
                    return f'{x}'
                return ', '.join([
                    *[f'{fmt(a)}' for a in args],
                    *[f'{n}={fmt(a)}' for n,a in kwargs.items()]
                ])
            
            actions: list[DefaultAction] = []
            
            if params == Parameters.Custom:

                any_il, any_rl = False, False
                for i in range(params_mask.shape[0]):
                    for j in range(params_mask.shape[1]):
                        if i==j:
                            any_rl = True
                        else:
                            any_il = True
                if any_il and any_rl:
                    plot_kwargs_il['style'] = '-'
                    plot_kwargs_rl['style'] = '--'
                
                for i in range(params_mask.shape[0]):
                    for j in range(params_mask.shape[1]):
                        if params_mask[i,j]:
                            if i==j:
                                plot_kwargs = plot_kwargs_rl
                            else:
                                plot_kwargs = plot_kwargs_il
                            actions.append(DefaultAction([i+1,j+1], dict(), [], plot_kwargs))

            else:

                any_il = params & Parameters.S21 or params & Parameters.S12
                any_rl = params & Parameters.Sii or params & Parameters.S11 or params & Parameters.S22
                if any_il and any_rl:
                    plot_kwargs_il['style'] = '-'
                    plot_kwargs_rl['style'] = '--'

                if params & Parameters.S21 and params & Parameters.S12:
                    actions.append(DefaultAction([], dict(il_only=True), [], plot_kwargs_il))
                elif params & Parameters.S21:
                    actions.append(DefaultAction([], dict(fwd_il_only=True), [], plot_kwargs_il))
                elif params & Parameters.S12:
                    actions.append(DefaultAction([], dict(rev_il_only=True), [], plot_kwargs_il))
            
                if params & Parameters.Sii:
                    actions.append(DefaultAction([], dict(rl_only=True), [], plot_kwargs_rl))
                elif params & Parameters.S11:
                    actions.append(DefaultAction([11], dict(), [], plot_kwargs_rl))
                elif params & Parameters.S22:
                    actions.append(DefaultAction([22], dict(), [], plot_kwargs_rl))
            
            generated_lines = [f'sel_nws().s({make_args_str(*a.s_args,**a.s_kwargs)}).plot({make_args_str(*a.plot_args,**a.plot_kwargs)})' for a in actions]
            self.generated_expressions = '\n'.join(generated_lines)

            param_selector_is_in_use = True
            if use_expressions:

                Settings.expression = self.ui_expression
                result = ExpressionParser.eval(self.ui_expression, self.files.values(), selected_files, actions, self._saved_nw_name_for_template, add_to_plot_list)  
                param_selector_is_in_use = result.default_actions_used

            else:

                try:
                    ExpressionParser.eval(self.generated_expressions, self.files.values(), selected_files, actions, self._saved_nw_name_for_template, add_to_plot_list)  
                except Exception as ex:
                    logging.error(f'Unable to parse expressions: {ex} (trace: {traceback.format_exc()})')
                    self.ui_plot.clear()

            singlefile_colorizing = False
            if Settings.singlefile_individualcolor:
                individual_files = ['::'.join([p.full_path for p in kwargs['original_files']]) for kwargs in all_plot_kwargs]
                n_different_files = len(set(individual_files))
                if n_different_files <= 1:
                    singlefile_colorizing = True
            if singlefile_colorizing:
                self.ui_enable_trace_color_selector = False
                self.ui_color_assignment = enum_to_string(ColorAssignment.Default, MainWindow.COLOR_ASSIGNMENT_NAMES)
                color_assignment = ColorAssignment.Default
            else:
                if not self.ui_enable_trace_color_selector:
                    self.ui_color_assignment = enum_to_string(Settings.color_assignment, MainWindow.COLOR_ASSIGNMENT_NAMES)
                    self.ui_enable_trace_color_selector = True
                color_assignment = string_to_enum(self.ui_color_assignment, MainWindow.COLOR_ASSIGNMENT_NAMES)

            def add_to_plot(f, sp, z0, name, style: str = None, color: str = None, width: float = None, opacity: float = None, original_files: set[PathExt] = None, param_kind: str = None):
                nonlocal color_assignment, available_colors, next_color_index, color_mapping

                if np.all(np.isnan(sp)):
                    return

                if style is None:
                    style = '-'
                if opacity is None:
                    if self.ui_semitrans_traces:
                        opacity = default_trace_opacity

                style2 = '-.'
                if style=='-':
                    style2 = '-.'
                elif style=='-.':
                    style2 = ':'
                if self.ui_mark_datapoints:
                    style += 'o'
                    style2 += 'o'
                if y_qty!=YQuantity.Off and y2_qty!=YQuantity.Off:
                    style_y2 = ':'
                else:
                    style_y2 = style

                if not color:  # assign a color
                    key: any|None = None
                    match color_assignment:
                        case ColorAssignment.Default:
                            pass
                        case ColorAssignment.ByParam:
                            key = param_kind
                        case ColorAssignment.ByFile:
                            if original_files and len(original_files) >= 1:
                                key = '::'.join([p.full_path for p in original_files])
                        case ColorAssignment.ByFileLoc:
                            if original_files and len(original_files) >= 1:
                                def get_path(path: PathExt) -> str:
                                    if path.arch_path:
                                        return str(path)
                                    else:
                                        return str(path.parent)
                                key = '::'.join([get_path(p) for p in original_files])
                        case ColorAssignment.Monochrome:
                            key = 1
                    if key is not None:
                        if key not in color_mapping:  # use next color in the list
                            next_color = available_colors[next_color_index % len(available_colors)]
                            next_color_index += 1
                            color_mapping[key] = next_color
                        color = color_mapping[key]

                kwargs = dict(width=width, color=color, opacity=opacity)
                
                def transform_phase(radians):
                    if phase_unit==PhaseUnit.Degrees:
                        return radians * 180 / math.pi
                    return radians

                treat_as_complex = Settings.treat_all_as_complex or np.iscomplexobj(sp)
                if plot_type in [PlotType.Polar, PlotType.Smith]:
                    if treat_as_complex:
                        self.plot.add(np.real(sp), np.imag(sp), f, name, style, **kwargs)
                    else:
                        if Settings.verbose:
                            chart_type_str = 'Smith' if plot_type==PlotType.Smith else 'polar'
                            logging.info(f'The trace "{name}" is real-valued; omitting from {chart_type_str} chart')
                elif plot_type == PlotType.TimeDomain:
                    if treat_as_complex:
                        t,lev = sparam_to_timedomain(f, sp, step_response=tdr_resp==TdResponse.StepResponse, shift=tdr_shift, window_type=window_type, window_arg=window_arg, min_size=tdr_minsize)
                        if tdr_z:
                            lev[lev==0] = 1e-20 # avoid division by zero in the next step
                            imp = z0 * (1+lev) / (1-lev) # convert to impedance
                            self.plot.add(t, np.real(imp), None, name, style, **kwargs)
                        else:
                            self.plot.add(t, lev, None, name, style, **kwargs)
                    else:
                        if Settings.verbose:
                            logging.info(f'The trace "{name}" is real-valued; omitting from time-domain transformed chart')
                else:
                    if treat_as_complex:
                        if y_qty == YQuantity.Decibels:
                            self.plot.add(f, v2db(sp), None, name, style, **kwargs)
                        elif y_qty == YQuantity.Magnitude:
                            self.plot.add(f, np.abs(sp), None, name, style, **kwargs)
                        elif y_qty == YQuantity.RealImag:
                            self.plot.add(f, np.real(sp), None, name+' re', style, **kwargs)
                            self.plot.add(f, np.imag(sp), None, name+' im', style2, **kwargs)
                        elif y_qty == YQuantity.Real:
                            self.plot.add(f, np.real(sp), None, name, style, **kwargs)
                        elif y_qty == YQuantity.Imag:
                            self.plot.add(f, np.imag(sp), None, name, style, **kwargs)
                        
                        if y2_qty == YQuantity.Phase:
                            if phase_processing == PhaseProcessing.UnwrapDetrend:
                                self.plot.add(f, transform_phase(scipy.signal.detrend(np.unwrap(np.angle(sp)),type='linear')), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                            elif phase_processing == PhaseProcessing.Unwrap:
                                self.plot.add(f, transform_phase(np.unwrap(np.angle(sp))), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                            else:
                                self.plot.add(f, transform_phase(np.angle(sp)), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                        elif y2_qty == YQuantity.GroupDelay:
                            self.plot.add(*group_delay(f,sp), None, name, style_y2, prefer_2nd_yaxis=True, **kwargs)
                    else:  # real-valued data
                        if Settings.verbose:
                            logging.info(f'The trace "{name}" is real-valued; just plotting the real value, ignoring decibel/magnitude/real/imag/phase/groupdelay')
                        self.plot.add(f, sp, None, name, style, **kwargs)

            for kwargs in all_plot_kwargs:
                add_to_plot(**kwargs)
            
            self.ui_param_selector.setDimParameters(not param_selector_is_in_use)

            self.update_params_size()
            self.plot.render()
            
            if self.plot_axes_are_valid and not self.ui_xaxis_range.both_are_wildcard:
                self.plot.plot.set_xlim(self.ui_xaxis_range.low, self.ui_xaxis_range.high, auto=False)

            if plot_type == PlotType.Cartesian and y_qty == YQuantity.Decibels and smart_db_scaling and len(self.plot.plots)>=1:
                do_smart_scaling, smart_y0, smart_y = choose_smart_db_scale([plot.data.y.values for plot in self.plot.plots if plot.currently_used_axis==1])
                if do_smart_scaling:
                    self.ui_yaxis_range.low, self.ui_yaxis_range.high = smart_y0, smart_y
                    self.plot.plot.set_ylim(smart_y0, smart_y, auto=False)
                    self._smartscale_set_y = True
                else:
                    if self._smartscale_set_y:
                        (self.ui_yaxis_range.low_is_wildcard, self.ui_yaxis_range.high_is_wildcard) = (True, True)
                        self.plot.plot.set_ylim(auto=True)
                    self._smartscale_set_y = False
            else:
                if self.plot_axes_are_valid and not self.ui_yaxis_range.both_are_wildcard:
                    self.plot.plot.set_ylim(self.ui_yaxis_range.low, self.ui_yaxis_range.high, auto=False)
            
            self.ui_plot.draw()

            self.plot_axes_are_valid = True
            
            log_entries = LogHandler.inst().get_records(logging.WARNING)
            last_log_entry_at_end = log_entries[-1] if log_entries else None
            if last_log_entry_at_end == last_log_entry_at_start:
                self.ui_show_status_message(None)

        except Exception as ex:
            self.ui_plot.clear()
            logging.error(f'Plotting failed: {ex}')

        finally:
            self.ui_schedule_oneshot_timer(MainWindow.TIMER_CLEAR_LOAD_COUNTER_ID, MainWindow.TIMER_CLEAR_LOAD_COUNTER_TIMEOUT_S, self.clear_load_counter, retrigger_behavior='postpone')
            self.ready = True
