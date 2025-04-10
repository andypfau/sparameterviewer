#!/bin/python

import sys, os, logging
from PyQt6 import QtWidgets

from gui.main_window import MainWindow
from gui.log_handler import LogHandler
from gui.settings import Settings
from gui.qt_helper import QtHelper
from lib import AppGlobal


if __name__ == '__main__':

    
    LOG_FORMAT = '%(asctime)s: %(message)s (%(filename)s:%(lineno)d:%(funcName)s, %(levelname)s)'
    logging.captureWarnings(True)
    logging.basicConfig(level=logging.ERROR, format=LOG_FORMAT, stream=None)
    logging.getLogger().setLevel(logging.DEBUG)
    
    LogHandler.inst()  # trigger initialization

    try:
        # add a second logger that logs critical errors to file
        logToFile = logging.FileHandler(os.path.join(AppGlobal.get_log_dir(), 'sparamviewer.log'))
        logToFile.setFormatter(logging.Formatter(LOG_FORMAT))
        logToFile.setLevel(logging.ERROR)
        logging.getLogger().addHandler(logToFile)
    except Exception as ex:
        pass # ignore

    try:
        # disable log stuff I am not interested in
        logging.getLogger('matplotlib.font_manager').disabled = True
        logging.getLogger('matplotlib.ticker').disabled = True
        logging.getLogger('PIL.PngImagePlugin').disabled = True
    except Exception as ex:
        pass # ignore

    # splashscreen (pyinstaller only)
    if AppGlobal.is_running_from_binary():
        try:
            import pyi_splash
            pyi_splash.close()
        except Exception as ex:
            pass # not started from pyinstaller, ignore

    try:
        app = QtWidgets.QApplication(sys.argv)

        try:
            available_fonts = QtHelper.get_available_fonts()
            if (not Settings.editor_font) or (Settings.editor_font not in available_fonts):
                preferred_fonts = AppGlobal.get_preferred_monospace_fonts()
                for preferred_font in preferred_fonts:
                    if preferred_font in available_fonts:
                        Settings.editor_font = preferred_font
                        logging.info(f'Chose monospace font "{Settings.editor_font}"')
                        break
        except:
            pass
            
        filenames = sys.argv[1:]
        main_dialog = MainWindow(filenames)
        main_dialog.show()
        app.exec()
    
    except Exception as ex:
        logging.exception('Error in main loop: {ex}')
        sys.exit(1)
