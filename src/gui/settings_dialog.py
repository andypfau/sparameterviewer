from .settings_dialog_ui import SettingsDialogUi, SettingsTab
from .helpers.simple_dialogs import okcancel_dialog
from .helpers.simple_dialogs import open_file_dialog
from .helpers.qt_helper import QtHelper
from .components.plot_widget import PlotWidget
from lib import Settings, PhaseUnit, CsvSeparator, CursorSnap, ColorAssignment, LogNegativeHandling, MainWindowLayout
from lib.utils import is_windows, window_has_argument, enum_to_string, string_to_enum
import pathlib
import logging


class SettingsDialog(SettingsDialogUi):

    CSV_SEPARATOR_NAMES = {
        CsvSeparator.Tab: '⇥  Tab',
        CsvSeparator.Comma: ',  Comma',
        CsvSeparator.Semicolon: ';  Semicolon',
    }

    CURSOR_SNAP_NAMES = {
        CursorSnap.X: 'Closest X-Coordinate',
        CursorSnap.Point: 'Closest Point',
    }

    LOGNEG_NAMES = {
        LogNegativeHandling.Abs: 'Take Absolute, Ignore Zeros',
        LogNegativeHandling.Ignore: 'Ignore Values ≤0',
        LogNegativeHandling.Fail: 'Ignore Entire Trace If ≤0',
    }

    MAINWINLAYOUT_NAMES = {
        MainWindowLayout.Vertical: 'Stacked',
        MainWindowLayout.Wide: 'Wide',
        MainWindowLayout.Ultrawide: 'Ultra-Wide',
    }


    def __init__(self, parent):
        super().__init__(parent)
        self.ui_set_csvset_options(list(SettingsDialog.CSV_SEPARATOR_NAMES.values()))
        self.ui_set_plotstysle_options(PlotWidget.get_plot_styles())
        self.ui_set_font_options(QtHelper.get_all_available_font_families(monospace_only=True))
        self.ui_set_cursor_snap_options(list(SettingsDialog.CURSOR_SNAP_NAMES.values()))
        self.ui_set_logxneg_options(list(SettingsDialog.LOGNEG_NAMES.values()))
        self.ui_set_logyneg_options(list(SettingsDialog.LOGNEG_NAMES.values()))
        self.ui_set_mainwinlayout_options(list(SettingsDialog.MAINWINLAYOUT_NAMES.values()))
    

    def show_modal_dialog(self, tab: SettingsTab = None):
        if tab:
            self.ui_select_tab(int(tab))
        self.apply_settings_to_controls()
        Settings.attach(self.on_settings_change)
        super().ui_show_modal()
    

    def on_settings_change(self, attributes: list[str]):
        self.apply_settings_to_controls()


    def apply_settings_to_controls(self):
        try:
            self.ui_radians = Settings.export_phase_unit == PhaseUnit.Radians
            self.ui_csvsep = enum_to_string(Settings.csv_separator, SettingsDialog.CSV_SEPARATOR_NAMES)
            self.ui_logxneg = enum_to_string(Settings.logx_negative_handling, SettingsDialog.LOGNEG_NAMES)
            self.ui_logyneg = enum_to_string(Settings.logy_negative_handling, SettingsDialog.LOGNEG_NAMES)
            self.ui_cursor_snap = enum_to_string(Settings.cursor_snap, SettingsDialog.CURSOR_SNAP_NAMES)
            self.ui_comment_expr = Settings.comment_existing_expr
            self.ui_extract_zip = Settings.extract_zip
            self.ui_warn_timeout = Settings.warn_timeout_s
            self.ui_ext_ed = Settings.ext_editor_cmd
            self.ui_plotstyle = Settings.plot_style
            self.ui_font = Settings.editor_font
            self.ui_all_complex = Settings.treat_all_as_complex
            self.ui_singletrace_individualcolor = Settings.singlefile_individualcolor
            self.ui_verbose = Settings.verbose
            self.ui_mainwin_layout = enum_to_string(Settings.mainwindow_layout, SettingsDialog.MAINWINLAYOUT_NAMES)
            self.ui_simplified_plot = Settings.simplified_plot_sel
            self.ui_simplified_params = Settings.simplified_param_sel
            self.ui_simplified_noexpr = Settings.simplified_no_expressions
            self.ui_simplified_browser = Settings.simplified_browser
            self.ui_maxhist = Settings.path_history_maxsize
            self.ui_indicate_ext_ed_error(not self.is_ext_ed_valid(Settings.ext_editor_cmd))
        except Exception as ex:
            logging.error('Unable to apply setting values to settings dialog')
            logging.exception(ex)


    @staticmethod
    def ensure_external_editor_is_set(parent) -> bool:
        if not Settings.ext_editor_cmd:
            if not okcancel_dialog('External Editor', 'No external editor specified. Please select one.', informative_text='A dialog will open where you can select the binary of an external editor of your choice.'):
                return False
            if not SettingsDialog._let_user_select_ext_editor(parent):
                return False
        return True


    @staticmethod
    def _let_user_select_ext_editor(parent, binary_path: str = None) -> bool:
        if binary_path is None:
            binary_path = Settings.ext_editor_cmd
        if is_windows():
            filetypes = [('Binaries', '.exe'), ('All Files', '*')]
        else:
            filetypes = [('All Files', '*')]
        binary_path = open_file_dialog(parent, title='Select External Editor', filetypes=filetypes, initial_filename=binary_path)
        if not binary_path:
            return False
        
        Settings.ext_editor_cmd = binary_path

        return True
    

    def is_ext_ed_valid(self, ext_ed: str):
        if not ext_ed:
            return False
        path = pathlib.Path(ext_ed)
        if not path.exists():
            return False
        if not path.is_file():
            return False
        return True
    

    def on_browse_ext_ed(self):
        SettingsDialog._let_user_select_ext_editor(self, self.ui_ext_ed)
    

    def on_phase_unit_change(self):
        Settings.export_phase_unit = PhaseUnit.Radians if self.ui_radians else PhaseUnit.Degrees


    def on_csvsep_change(self):
        Settings.csv_separator = string_to_enum(self.ui_csvsep, SettingsDialog.CSV_SEPARATOR_NAMES)

    
    def on_zip_change(self):
        Settings.extract_zip = self.ui_extract_zip


    def on_cursor_snap_changed(self):
        Settings.cursor_snap = string_to_enum(self.ui_cursor_snap, SettingsDialog.CURSOR_SNAP_NAMES)
    
    
    def on_comment_change(self):
        Settings.comment_existing_expr = self.ui_comment_expr
    
    
    def on_ext_ed_change(self):
        is_valid = self.is_ext_ed_valid(self.ui_ext_ed)
        was_valid = self.is_ext_ed_valid(Settings.ext_editor_cmd)
        if is_valid or (not was_valid):
            Settings.ext_editor_cmd = self.ui_ext_ed
        self.ui_indicate_ext_ed_error(not is_valid)


    def on_plotstyle_change(self):
        Settings.plot_style = self.ui_plotstyle


    def on_font_change(self):
        Settings.editor_font = self.ui_font


    def _on_warn_timeout_changed(self):
        Settings.warn_timeout_s = self.ui_warn_timeout
    
    
    def on_allcomplex_changed(self):
        Settings.treat_all_as_complex = self.ui_all_complex


    def on_verbose_changed(self):
        Settings.verbose = self.ui_verbose


    def on_logxneg_changed(self):
        Settings.logx_negative_handling = string_to_enum(self.ui_logxneg, SettingsDialog.LOGNEG_NAMES)


    def on_logyneg_changed(self):
        Settings.logy_negative_handling = string_to_enum(self.ui_logyneg, SettingsDialog.LOGNEG_NAMES)


    def on_mainwinlayout_changed(self):
        Settings.mainwindow_layout = string_to_enum(self.ui_mainwin_layout, SettingsDialog.MAINWINLAYOUT_NAMES)
    
    
    def on_simple_plot_changed(self):
        Settings.simplified_plot_sel = self.ui_simplified_plot
    
    
    def on_simple_params_changed(self):
        Settings.simplified_param_sel = self.ui_simplified_params


    def on_simple_noexpr_changed(self):
        Settings.simplified_no_expressions = self.ui_simplified_noexpr


    def on_simple_browser_changed(self):
        Settings.simplified_browser = self.ui_simplified_browser


    def on_singletracecolor_changed(self):
        Settings.singlefile_individualcolor = self.ui_singletrace_individualcolor


    def on_maxhist_change(self):
        Settings.path_history_maxsize = self.ui_maxhist
