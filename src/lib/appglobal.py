from tkinter import Toplevel
import os
import logging
import sys
import tkinter

from .utils import is_windows


class AppGlobal:


    @staticmethod
    def get_root_dir() -> str:
        lib_dir = os.path.abspath(os.path.dirname(__file__))
        src_dir = os.path.dirname(lib_dir)
        app_dir = os.path.dirname(src_dir)
        return app_dir


    @staticmethod
    def get_log_dir() -> str:
        return AppGlobal.get_root_dir()


    @staticmethod
    def get_help_dir() -> str:
        root_dir = AppGlobal.get_root_dir()
        if AppGlobal.is_running_from_binary():
            help_dir = os.path.join(root_dir, '_internal', 'doc')
            if os.path.exists(help_dir):
                return help_dir
        return os.path.join(root_dir, 'doc')


    @staticmethod
    def is_running_from_binary() -> bool:
        try:
            # see <https://pyinstaller.org/en/stable/runtime-information.html>
            if getattr(sys, 'frozen', False):
                return True
        except:
            pass # ignore
        return False


    @staticmethod
    def set_toplevel_icon(toplevel: Toplevel):
        try:
            
            dir = AppGlobal.get_root_dir()
            if not os.path.exists(os.path.join(dir, 'res')):
                dir = os.path.dirname(dir) # look in parent folder

            if is_windows():
                toplevel.iconbitmap(os.path.join(dir, 'res/sparamviewer.ico'))
            else:
                try:
                    img = tkinter.PhotoImage(file=os.path.join(dir, 'res/sparamviewer.png'))
                    toplevel.tk.call('wm', 'iconphoto', toplevel._w, img)
                except:
                    toplevel.iconbitmap('@' + os.path.join(dir, 'res/sparamviewer.xbm'))

        except Exception as ex:
            logging.exception(f'Unable to set toplevel icon: {ex}')
