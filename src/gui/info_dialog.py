#!/bin/python3

from tkinter import END
from .info_dialog_pygubuui import PygubuAppUI
from lib import TkText, AppGlobal, TkCommon

import logging


# extend auto-generated UI code
class SparamviewerInfoDialog(PygubuAppUI):
    def __init__(self, master, title: str, text: str):
        super().__init__(master)

        TkCommon.default_keyhandler(self.toplevel_info, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=False,**kwargs))
        AppGlobal.set_toplevel_icon(self.toplevel_info)
        self.toplevel_info.title(title)

        TkText.default_keyhandler(self.text_info, readonly=True, custom_handler=lambda **kwargs: self.on_check_for_global_keystrokes(is_textbox=True,**kwargs))
        TkText.set_text(self.text_info, text)
        

    def run(self, focus: bool = True):
        if focus:
            self.mainwindow.focus_force()
        super().run()
    

    def on_check_for_global_keystrokes(self, is_textbox, key, ctrl, alt, **kwargs):
        
        if key=='Escape':
            self.toplevel_info.destroy()
            return 'break'
        
        if is_textbox:
            return 'break' # ignore all others, as this is read-only
        else:
            return # invoke default handler
