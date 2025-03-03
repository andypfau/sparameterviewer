from tkinter import Toplevel, messagebox
import os
import logging
import sys
import tkinter
from typing import Optional

from .utils import is_windows, open_file_in_default_viewer


class AppGlobal:


    _content_dir: Optional[None] = None


    @staticmethod
    def _get_root_dir() -> str:
        lib_dir = os.path.abspath(os.path.dirname(__file__))
        src_dir = os.path.dirname(lib_dir)
        app_dir = os.path.dirname(src_dir)
        return app_dir
    

    @staticmethod
    def _get_content_dir() -> str:
        if AppGlobal._content_dir is not None:
            return AppGlobal._content_dir

        root_dir = AppGlobal._get_root_dir()
        content_dir = root_dir

        # special case for compiled app
        if AppGlobal.is_running_from_binary():
            if not os.path.exists(content_dir):
                if os.path.exists(os.path.join(content_dir, '_internal')):
                    content_dir = os.path.join(content_dir, '_internal')

        AppGlobal._content_dir = content_dir
        return content_dir


    @staticmethod
    def get_log_dir() -> str:
        return AppGlobal._get_root_dir()


    @staticmethod
    def get_resource_dir() -> str:
        return os.path.join(AppGlobal._get_content_dir(), 'res')


    @staticmethod
    def get_doc_dir() -> str:
        return os.path.join(AppGlobal._get_content_dir(), 'doc')


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
            
            if is_windows():
                toplevel.iconbitmap(os.path.join(AppGlobal.get_resource_dir(), 'sparamviewer.ico'))
            else:
                try:
                    img = tkinter.PhotoImage(file=os.path.join(AppGlobal.get_resource_dir(), 'sparamviewer.png'))
                    toplevel.tk.call('wm', 'iconphoto', toplevel._w, img)
                except:
                    toplevel.iconbitmap('@' + os.path.join(AppGlobal.get_resource_dir(), 'sparamviewer.xbm'))

        except Exception as ex:
            logging.exception(f'Unable to set toplevel icon: {ex}')



    @staticmethod
    def show_help(doc: str = 'main.md'):
        try:
            helpfile_path = os.path.join(AppGlobal.get_doc_dir(), doc)
            if not os.path.exists(helpfile_path):
                raise RuntimeError(f'<{helpfile_path}> not exists')
        except Exception as ex:
            logging.exception(f'Unable to locate documentation: {ex}')
            messagebox.showerror('Unable to locate documentation', f'Unable to locate documentation; try to locate <sparameterviewer/docs> yourself ({ex}).')
        
        try:
            open_file_in_default_viewer(helpfile_path)
        except Exception as ex:
            logging.exception(f'Unable to show documentation ({helpfile_path}): {ex}')
            messagebox.showerror('Unable to show documentation', f'Unable to show documentation; try to open <{helpfile_path}> yourself ({ex}).')
