from .settings_dialog_ui import SettingsDialogUi, SettingsTab
from .settings import Settings
from .simple_dialogs import open_file_dialog
from lib.utils import is_windows
import pathlib
import logging


class SettingsDialog(SettingsDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
    

    def show_dialog(self, tab: SettingsTab = None):
        if tab is not None:
            self.ui_select_tab(tab)
        self.apply_settings_to_controls()
        Settings.attach(self.apply_settings_to_controls)
        super().ui_show()
    

    def apply_settings_to_controls(self):
        try:
            self.ui_phase_unit = Settings.phase_unit
        except Exception as ex:
            logging.error('Unable to apply setting values to settings dialog')
            logging.exception(ex)


    @staticmethod
    def let_user_select_ext_editor(parent) -> bool:
        kwargs = []
        if is_windows():
            kwargs['filetypes'] = [('Binaries', '.exe'), ('All Files', '*')]
        else:
            kwargs['filetypes'] = [('All Files', '*')]
        if Settings.ext_editor_cmd:
            path = pathlib.Path(Settings.ext_editor_cmd)
            if path.exists():
                kwargs['initial_dir'] = str(path.parent)
        binary_path = open_file_dialog(parent, title='Select External Editor', **kwargs)
        if not binary_path:
            return False
        
        Settings.ext_editor_cmd = binary_path

        return True
    

    def on_browse_ext_ed(self):
        if not SettingsDialog.let_user_select_ext_editor():
            return
        # TODO: update text
    

    def on_phase_unit_change(self):
        Settings.phase_unit = self.ui_phase_unit
