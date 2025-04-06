from .main_window_ui import MainWindowUi
from .log_handler import LogHandler
from .settings import Settings
from .simple_dialogs import info_dialog, warning_dialog, error_dialog, exception_dialog, okcancel_dialog, yesno_dialog
from lib.si import SiFmt
from lib import Clipboard
from lib import open_file_in_default_viewer, sparam_to_timedomain, get_sparam_name
from lib import Si
from lib import SParamFile
from lib import PlotHelper
from lib import ExpressionParser
from lib import Clipboard
from info import Info

import pathlib
import appdirs
import math
import copy
import logging
import traceback
import datetime
import numpy as np
import re
import os
import zipfile
import matplotlib.pyplot as pyplot
from matplotlib.figure import Figure
import scipy.signal
from PyQt6 import QtCore, QtGui, QtWidgets



MAX_DIRECTORY_HISTORY_SIZE = 10



class MainWindow(MainWindowUi):

    def __init__(self, filenames: list[str]):
        super().__init__()
        
        self.directories: list[str] = []
        self.next_file_tag = 1
        self.files: list[SParamFile] = []
        self.generated_expressions = ''
        self.plot_mouse_down = False
        #self.cursor_dialog: SparamviewerCursorDialog = None
        self.plot_axes_are_valid = False
        self.lock_xaxis = False
        self.lock_yaxis = False

        try:
            self.initially_load_files_or_directory(filenames)
            self.update_plot()
        
        except Exception as ex:
            Settings.reset()
            logging.exception(f'Unable to init main dialog: {ex}')
            exception_dialog('Error', f'Error ({ex}); maybe corrupted config... reset, try again next time')


    
    def initially_load_files_or_directory(self, filenames_or_directory: "list[str]"):
        if len(filenames_or_directory)<1:
            filenames_or_directory = [appdirs.user_data_dir()]

        is_dir = os.path.isdir(filenames_or_directory[0])
        if is_dir:
            directory = filenames_or_directory
            absdir = os.path.abspath(directory[0])
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(only_select_first=True)
        else:
            filenames = filenames_or_directory
            if not Settings.extract_zip:
                contains_archives = False
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in ['.zip']:
                        contains_archives = True
                        break
                if contains_archives:
                    if yesno_dialog('Extract .zip Files', 'A .zip-file was selected, but the option to extract .zip-files is disabled. Do you want to enable it?'):
                        Settings.extract_zip = True
            absdir = os.path.split(filenames[0])[0]
            self.directories = [absdir]
            self.load_files_in_directory(absdir)
            self.update_file_list(selected_filenames=filenames)
    

    def update_most_recent_directories_menu(self):
        self.update_files_history(Settings.last_directories)
        
    
    def add_to_most_recent_directories(self, dir: str):
        if dir in Settings.last_directories:
            idx = Settings.last_directories.index(dir)
            del Settings.last_directories[idx]
        
        Settings.last_directories.insert(0, dir)
        
        while len(Settings.last_directories) > MAX_DIRECTORY_HISTORY_SIZE:
            del Settings.last_directories[-1]
        
        Settings.save()

        self.update_most_recent_directories_menu()


    def load_files_in_directory(self, dir: str):

        self.add_to_most_recent_directories(dir)

        try:

            absdir = os.path.abspath(dir)
            
            def filetype_matches(path):
                ext = os.path.splitext(path)[1]
                return re.match(r'(\.ci?ti)|(\.s[0-9]+p)', ext, re.IGNORECASE)
        
            def load_file(filename, archive_path=None):
                try:
                    tag = f'file{self.next_file_tag}'
                    file = SParamFile(filename, tag=tag, archive_path=archive_path)
                    self.files.append(file)
                    self.next_file_tag += 1
                except Exception as ex:
                    logging.info(f'Ignoring file <{filename}>: {ex}')
            
            def find_all_files(path):
                all_items = [os.path.join(path,f) for f in os.listdir(path)]
                return sorted(list([f for f in all_items if os.path.isfile(f)]))

            all_files = find_all_files(absdir)

            for filename in all_files:
                if not filetype_matches(filename):
                    continue
                load_file(filename)

            if Settings.extract_zip:
                for zip_filename in all_files:
                    ext = os.path.splitext(zip_filename)[1].lower()
                    if ext != '.zip':
                        continue
                    try:
                        with zipfile.ZipFile(zip_filename, 'r') as zf:
                            for internal_name in zf.namelist():
                                if not filetype_matches(internal_name):
                                    continue
                                load_file(internal_name, archive_path=zip_filename)
                    except Exception as ex:
                        logging.warning(f'Unable to open zip file <{zip_filename}>: {ex}')
        
        except Exception as ex:
            logging.exception(f'Unable to load files: {ex}')
            raise ex


    def reload_all_files(self):
        self.clear_loaded_files()
        for dir in self.directories:
            self.load_files_in_directory(dir)
        self.update_file_list()


    def get_file_prop_str(self, file: "SParamFile") -> str:
        if file.loaded():
            return f'{file.nw.number_of_ports}-port, {Si(min(file.nw.f),"Hz")} to {Si(max(file.nw.f),"Hz")}'
        elif file.error():
            return '[loading failed]'
        else:
            return '[not loaded]'


    def update_file_in_list(self, file: "SParamFile"):
        
        tag = file.tag
        name_str = file.name
        prop_str = self.get_file_prop_str(file)
        
        self.treeview_files.item(tag, values=(name_str,prop_str))
    

    def update_file_list(self, selected_filenames: "list[str]" = [], only_select_first: bool = False):
        
        if len(selected_filenames) == 0 and not only_select_first:
            search = self.search_str.get()
            if len(search) != 0:
                previously_selected_files = []
            else:
                previously_selected_files = self.get_selected_files()
                search = None
        else:
            previously_selected_files = []
            search = None
            self.search_str.set('')

        self.treeview_files.delete(*self.treeview_files.get_children())
        selected_archives = set()
        for i,file in enumerate(self.files):
            
            tag = file.tag
            name_str = file.name
            prop_str = self.get_file_prop_str(file)
            
            self.treeview_files.insert('', 'end', tag, values=(name_str,prop_str))
            
            do_select = False
            if only_select_first and i==0:
                do_select = True
            elif file.tag in [s.tag for s in previously_selected_files]:
                do_select = True
            elif os.path.abspath(file.file_path) in [os.path.abspath(f) for f in selected_filenames]:
                do_select = True
            elif (file.archive_path is not None) and (os.path.abspath(file.archive_path) in [os.path.abspath(f) for f in selected_filenames]):
                if file.archive_path not in selected_archives:
                    # only select the 1st file in any archive, to avoid excessive loading time
                    selected_archives.add(file.archive_path)
                    do_select = True
            elif search is not None:
                try:
                    if re.search(search, file.filename, re.IGNORECASE):
                        do_select = True
                except:
                    pass
            
            if do_select:
                self.treeview_files.selection_add(tag)


    def get_selected_files(self) -> "list[SParamFile]":
        selected_files = []
        for file in self.files:
            if file.tag in self.treeview_files.selection():
                selected_files.append(file)
        return selected_files
    

    def update_plot(self):
        logging.error('update_plot not implemented')
    