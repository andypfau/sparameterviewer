from tkinter import END
from .log_dialog_pygubu import PygubuApp
from lib import TkText, AppGlobal, TkCommon
from .settings import Settings

import logging





class LogHandler(logging.Handler):

    instance: "LogHandler"
    
    @staticmethod
    def set_up():
        LogHandler.instance = LogHandler(Settings.log_level)
        logging.getLogger().addHandler(LogHandler.instance)
        def settings_changed():
            LogHandler.instance.setLevel(Settings.log_level)
        Settings.attach(settings_changed)
    
    
    def __init__(self, level):
        self.entries = []
        self._observers = []
        super().__init__(level)
    

    def clear(self):
        self.entries = []
        self.notify()


    def emit(self, record):
        self.entries.append(f'{record.levelname}: {record.message} ({record.exc_text})')
        self.notify()


    def notify(self):
        for callback in self._observers:
            try:
                callback()
            except: pass


    def attach(self, callback: "callable[None,None]"):
        self._observers.append(callback)

    
    def detach(self, callback: "callable[None,None]"):
        try:
            self._observers.remove[callback]
        except: pass



# extend auto-generated UI code
class SparamviewerLogDialog(PygubuApp):
    def __init__(self, master):
        super().__init__(master)

        TkCommon.default_keyhandler(self.toplevel_log, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=False,**kwargs))
        AppGlobal.set_toplevel_icon(self.toplevel_log)

        TkText.default_keyhandler(self.toplevel_log, readonly=True, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=True,**kwargs))
        self.update_log_text()

        if Settings.log_level >= logging.ERROR:
            self.log_level.set('Error')
        elif Settings.log_level >= logging.WARNING:
            self.log_level.set('Warning')
        elif Settings.log_level >= logging.INFO:
            self.log_level.set('Info')
        else:
            self.log_level.set('Debug')

        def update_log_callback():
            self.update_log_text()
        LogHandler.instance.attach(update_log_callback)

        def on_close():
            LogHandler.instance.detach(update_log_callback)
            self.toplevel_log.destroy()
        self.toplevel_log.protocol("WM_DELETE_WINDOW", on_close)
    

    def update_log_text(self):
        text = '\n'.join(reversed(LogHandler.instance.entries))
        TkText.set_text(self.log_text, text)
    

    def on_check_for_global_keystrokes(self, is_textbox, key, ctrl, alt, **kwargs):
        
        logging.debug(f'Got key {key}')
        if key=='Escape':
            self.toplevel_log.destroy()
            return 'break'
        
        if is_textbox:
            return 'break' # ignore all others, as this is read-only
        else:
            return # invoke default handler


    def on_clear(self):
        LogHandler.instance.clear()
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
        else:
            raise ValueError(f'Invalid log level: "{self.log_level.get()}"')
