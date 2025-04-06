from .main_window_ui import MainWindowUi

import pathlib
from PyQt6 import QtCore, QtGui, QtWidgets



class MainWindow(MainWindowUi):

    def __init__(self, startup_files: list[str]):
        super().__init__()

        for path in startup_files:
            self.add_fileview_item(pathlib.Path(path).absolute())

        self.plot.axes.plot([0,1,2,3,4], [10,1,20,3,40])
    

    def on_exit(self):
        self.close()
