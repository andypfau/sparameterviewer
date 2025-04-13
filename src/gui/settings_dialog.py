from .settings_dialog_ui import SettingsDialogUi, SettingsTab
from .simple_dialogs import info_dialog
from .help import show_help
from .settings import Settings, ParamMode, PhaseUnit, PlotUnit, PlotUnit2, CsvSeparator
from .simple_dialogs import open_file_dialog
from .plot_widget import PlotWidget
from .qt_helper import QtHelper
from lib.utils import is_windows
import pathlib
import logging


class SettingsDialog(SettingsDialogUi):

    CSV_SEPARATOR_NAMES = {
        CsvSeparator.Tab: 'Tab',
        CsvSeparator.Comma: 'Comma',
        CsvSeparator.Semicolon: 'Semicolon',
    }

    TD_MINSIZE_NAMES = {
        0: 'No Padding',
        1024: '1k',
        1024*2: '2k',
        1024*4: '4k',
        1024*8: '8k',
        1024*16: '16k',
        1024*32: '32k',
        1024*64: '64k',
        1024*128: '128k',
        1024*256: '256k',
    }

    WINDOW_NAMES = {
        'boxcar': 'Rectangular (No Windowing)',
        'hann': 'Hann',
        'hamming': 'Hamming',
        'kaiser': 'Kaiser',
        'flattop': 'Flat Top',
        'blackman': 'Blackman',
        'tukey': 'Tukey',
    }

    PHASE_UNIT_NAMES = {
        CsvSeparator.Tab: 'Tab',
        CsvSeparator.Comma: 'Comma',
        CsvSeparator.Semicolon: 'Semicolon',
    }


    def __init__(self, parent):
        super().__init__(parent)
        self.ui_set_csvset_options(list(SettingsDialog.CSV_SEPARATOR_NAMES.values()))
        self.ui_set_td_window_options(list(SettingsDialog.WINDOW_NAMES.values()))
        self.ui_set_td_minsize_options(list(SettingsDialog.TD_MINSIZE_NAMES.values()))
        self.ui_set_plotstysle_options(PlotWidget.get_plot_styles())
        self.ui_set_font_options(QtHelper.get_all_available_font_families(monospace_only=True))
    

    def show_modal_dialog(self, tab: SettingsTab = None):
        if tab:
            self.ui_select_tab(tab)
        self.apply_settings_to_controls()
        Settings.attach(self.apply_settings_to_controls)
        super().ui_show_modal()
    

    def apply_settings_to_controls(self):
        try:
            self.ui_radians = Settings.phase_unit == PhaseUnit.Radians
            self.ui_csvsep = SettingsDialog.CSV_SEPARATOR_NAMES[Settings.csv_separator]
            self.ui_td_window = SettingsDialog.WINDOW_NAMES[Settings.window_type]
            self.ui_td_window_param = Settings.window_arg
            self.ui_td_minsize = SettingsDialog.TD_MINSIZE_NAMES[Settings.tdr_minsize]
            self.ui_td_shift = Settings.tdr_shift
            self.ui_td_z = Settings.tdr_impedance
            self.ui_comment_expr = Settings.comment_existing_expr
            self.ui_extract_zip = Settings.extract_zip
            self.ui_ext_ed = Settings.ext_editor_cmd
            self.ui_plotstyle = Settings.plot_style
            self.ui_font = Settings.editor_font
            self.ui_indicate_ext_ed_error(not self.is_ext_ed_valid(Settings.ext_editor_cmd))
        except Exception as ex:
            logging.error('Unable to apply setting values to settings dialog')
            logging.exception(ex)


    @staticmethod
    def ensure_external_editor_is_set(parent) -> bool:
        if (not Settings.ext_editor_cmd) or (not pathlib.Path(Settings.ext_editor_cmd).exists()):
            info_dialog('External Editor', f'No external editor specified. Please select one.')
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
        Settings.phase_unit = PhaseUnit.Radians if self.ui_radians else PhaseUnit.Degrees


    def on_csvsep_change(self):
        for symbol, name in SettingsDialog.CSV_SEPARATOR_NAMES.items():
            if name == self.ui_csvsep:
                Settings.csv_separator = symbol
                break
    
    
    def on_td_window_changed(self):
        for window, name in SettingsDialog.WINDOW_NAMES.items():
            if name == self.ui_td_window:
                Settings.window_type = window
                break
    
    
    def on_td_window_param_changed(self):
        Settings.window_arg = self.ui_td_window_param
    
    
    def on_td_minsize_changed(self):
        for size, name in SettingsDialog.TD_MINSIZE_NAMES.items():
            if name == self.ui_td_minsize:
                Settings.tdr_minsize = size
                break
    
    
    def on_td_shift_changed(self):
        Settings.tdr_shift = self.ui_td_shift
    

    def on_td_z_changed(self):
        Settings.tdr_impedance = self.ui_td_z

    
    def on_zip_change(self):
        Settings.extract_zip = self.ui_extract_zip
    
    
    def on_comment_change(self):
        Settings.comment_existing_expr = self.ui_comment_expr
    
    
    def on_ext_ed_change(self):
        is_valid = self.is_ext_ed_valid(self.ui_ext_ed)
        was_valid = self.is_ext_ed_valid(Settings.ext_editor_cmd)
        if is_valid or (not was_valid):
            Settings.ext_editor_cmd = self.ui_ext_ed
        self.ui_indicate_ext_ed_error(not is_valid)


    def on_help(self):
        show_help('settings.md')


    def on_plotstyle_change(self):
        Settings.plot_style = self.ui_plotstyle


    def on_font_change(self):
        Settings.editor_font = self.ui_font
