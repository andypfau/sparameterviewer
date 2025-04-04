from tkinter import END
from .log_dialog_pygubuui import PygubuAppUI
from .log_handler import LogHandler
from lib import TkText, AppGlobal, TkCommon
from .settings import Settings

import logging



# extend auto-generated UI code
class SparamviewerLogDialog(PygubuAppUI):
    def __init__(self, master):
        super().__init__(master)

        TkCommon.default_keyhandler(self.toplevel_log, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=False,**kwargs))
        AppGlobal.set_toplevel_icon(self.toplevel_log)

        TkText.default_keyhandler(self.toplevel_log, readonly=True, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=True,**kwargs))
        self.update_log_text()

        if Settings.log_level >= logging.CRITICAL:
            self.log_level.set('Critical')
        elif Settings.log_level >= logging.ERROR:
            self.log_level.set('Error')
        elif Settings.log_level >= logging.WARNING:
            self.log_level.set('Warning')
        elif Settings.log_level >= logging.INFO:
            self.log_level.set('Info')
        else:
            self.log_level.set('Debug')

        def update_log_callback():
            self.update_log_text()
        LogHandler.inst().attach(update_log_callback)

        def on_close():
            LogHandler.inst().detach(update_log_callback)
            self.toplevel_log.destroy()
        self.toplevel_log.protocol("WM_DELETE_WINDOW", on_close)
        

    def run(self, focus: bool = True):
        if focus:
            self.mainwindow.focus_force()
        super().run()
    

    def update_log_text(self):
        text = '\n'.join(reversed(LogHandler.inst().get_messages(Settings.log_level)))
        TkText.set_text(self.log_text, text)
    

    def on_check_for_global_keystrokes(self, is_textbox, key, ctrl, alt, **kwargs):
        
        if key=='Escape':
            self.toplevel_log.destroy()
            return 'break'
        
        if is_textbox:
            return 'break' # ignore all others, as this is read-only
        else:
            return # invoke default handler


    def on_clear(self):
        LogHandler.inst().clear()
        #TkText.set_text(self.toplevel_log, '')


    def on_set_level(self, event=None):
        if self.log_level.get() == 'Debug':
            Settings.log_level = logging.DEBUG
        elif self.log_level.get() == 'Info':
            Settings.log_level = logging.INFO
        elif self.log_level.get() == 'Warning':
            Settings.log_level = logging.WARNING
        elif self.log_level.get() == 'Error':
            Settings.log_level = logging.ERROR
        elif self.log_level.get() == 'Critical':
            Settings.log_level = logging.CRITICAL
        else:
            raise ValueError(f'Invalid log level: "{self.log_level.get()}"')
        self.update_log_text()
