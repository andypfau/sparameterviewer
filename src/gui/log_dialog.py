from tkinter import END
from log_dialog_pygubu import SparamviewerPygubuApp
from lib import TkText, AppGlobal, TkCommon

import logging


# extend auto-generated UI code
class SparamviewerLogDialog(SparamviewerPygubuApp):
    def __init__(self, master, title: str, text: str):
        super().__init__(master)

        TkCommon.default_keyhandler(self.toplevel_log, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=False,**kwargs))
        AppGlobal.set_toplevel_icon(self.toplevel_log)
        self.toplevel_log.title(title)

        TkText.default_keyhandler(self.toplevel_log, readonly=True, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=True,**kwargs))
        TkText.set_text(self.toplevel_log, text)
    

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
        TkText.set_text(self.toplevel_log, '')


    def on_set_level(self, event=None):
        ...
