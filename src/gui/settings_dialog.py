from .settings_dialog_ui import SettingsDialogUi, SettingsTab
from .settings import Settings
from .simple_dialogs import open_file_dialog
from lib.utils import is_windows
import pathlib
import logging


class SettingsDialog(SettingsDialogUi):

    CSV_SEPARATORS = {
        '\t': 'Tab',
        ',': 'Comma',
        ';': 'Semicolon',
    }

    TD_MINSIZES = {
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

    WINDOWS = {
        'boxcar': 'Rectangular (No Windowing)',
        'hann': 'Hann',
        'hamming': 'Hamming',
        'kaiser': 'Kaiser',
        'flattop': 'Flat Top',
        'blackman': 'Blackman',
        'tukey': 'Tukey',
    }


    def __init__(self, parent):
        super().__init__(parent)
        self.ui_set_csvset_options(list(SettingsDialog.CSV_SEPARATORS.values()))
        self.ui_set_td_window_options(list(SettingsDialog.WINDOWS.values()))
        self.ui_set_td_minsize_options(list(SettingsDialog.TD_MINSIZES.values()))
    

    def show_modal_dialog(self, tab: SettingsTab = None):
        if tab is not None:
            self.ui_select_tab(tab)
        self.apply_settings_to_controls()
        Settings.attach(self.apply_settings_to_controls)
        super().ui_show_modal()
    

    def apply_settings_to_controls(self):
        try:
            self.ui_phase_unit = Settings.phase_unit
            self.ui_csvsep = SettingsDialog.CSV_SEPARATORS[Settings.csv_separator]
            self.ui_td_window = SettingsDialog.WINDOWS[Settings.window_type]
            self.ui_td_window_param = Settings.window_arg
            self.ui_td_minsize = SettingsDialog.TD_MINSIZES[Settings.tdr_minsize]
            self.ui_td_shift = Settings.tdr_shift
            self.ui_td_z = Settings.tdr_impedance
            self.ui_comment_expr = Settings.comment_existing_expr
            self.ui_extract_zip = Settings.extract_zip
            self.ui_ext_ed = Settings.ext_editor_cmd
            self.ui_indicate_ext_ed_error(not self.is_ext_ed_valid(Settings.ext_editor_cmd))
        except Exception as ex:
            logging.error('Unable to apply setting values to settings dialog')
            logging.exception(ex)


    @staticmethod
    def let_user_select_ext_editor(parent, binary_path: str = None) -> bool:
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
        SettingsDialog.let_user_select_ext_editor(self, self.ui_ext_ed)
    

    def on_phase_unit_change(self):
        Settings.phase_unit = self.ui_phase_unit


    def on_csvsep_change(self):
        for symbol, name in SettingsDialog.CSV_SEPARATORS.items():
            if name == self.ui_csvsep:
                Settings.csv_separator = symbol
                break
    
    
    def on_td_window_changed(self):
        for window, name in SettingsDialog.WINDOWS.items():
            if name == self.ui_td_window:
                Settings.window_type = window
                break
    
    
    def on_td_window_param_changed(self):
        Settings.window_arg = self.ui_td_window_param
    
    
    def on_td_minsize_changed(self):
        for size, name in SettingsDialog.TD_MINSIZES.items():
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
