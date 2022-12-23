from tkinter import Toplevel
import os, logging
import tkinter

from .utils import is_windows


root_path = None


class AppGlobal:

    @staticmethod
    def set_root_path(new_root_path: str):
        global root_path
        root_path = new_root_path


    @staticmethod
    def get_root_path() -> str:
        global root_path
        return root_path


    @staticmethod
    def set_toplevel_icon(toplevel: Toplevel):
        try:
            
            dir = AppGlobal.get_root_path()
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
