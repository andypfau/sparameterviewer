from .log_dialog_ui import LogDialogUi
from .helpers.log_handler import LogHandler
from .helpers.simple_dialogs import okcancel_dialog
from .helpers.settings import Settings
from lib import AppPaths
import logging


class LogDialog(LogDialogUi):

    Levels = {
        'Debug': logging.DEBUG,
        'Info': logging.INFO,
        'Warning': logging.WARNING,
        'Error': logging.ERROR,
        'Critical': logging.CRITICAL,
    }
    

    def __init__(self, parent):
        super().__init__(parent)
        self.ui_set_level_strings([name for name in LogDialog.Levels.keys()])
        try:
            for name,level in LogDialog.Levels.items():
                if level >= Settings.log_level:
                    self.ui_level_str = name
                    break
        except:
            pass
    

    def show_dialog(self):
        LogHandler.inst().attach(self.update_log_text)
        super().ui_show()
    

    def update_log_text(self):
        text = '\n'.join(reversed(LogHandler.inst().get_messages(Settings.log_level)))
        self.ui_set_logtext(text)


    def on_select_level(self):
        for name,level in LogDialog.Levels.items():
            if name == self.ui_level_str:
                Settings.log_level = level
                break
        self.update_log_text()


    def on_clear(self):
        if not okcancel_dialog('Clear Log', 'All log entries will be deleted.', detailed_text=f'You can still find the whole log in <{AppPaths.get_log_path()}>'):
            return
        LogHandler.inst().clear()
