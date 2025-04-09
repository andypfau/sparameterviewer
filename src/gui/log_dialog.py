from .log_dialog_ui import LogDialogUi
from .log_handler import LogHandler
from .settings import Settings
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
        LogHandler.inst().attach(self.update_log_text)
        self.ui_set_level_strings([name for name in LogDialog.Levels.keys()])
        try:
            for name,level in LogDialog.Levels.items():
                if level >= Settings.log_level:
                    self.ui_level_str = name
                    break
        except:
            pass
    

    def show_dialog(self):
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

        
    def on_close(self):
        LogHandler.inst().detach(self.update_log_text)
