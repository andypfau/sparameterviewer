from .qt_helper import QtHelper
from lib import AppPaths, Settings

from PyQt6.QtWidgets import QMessageBox, QFileDialog, QCheckBox
import logging
import pathlib
from typing import Optional



def _make_dialog(title: str, text: str, informative_text: str|None, detailed_text: str|None, checkbox_text: str|None, checkbox_value: bool, icon: QMessageBox.Icon) -> QMessageBox:
    dialog = QMessageBox()
    dialog.setIcon(icon)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    QtHelper.set_dialog_icon(dialog)
    if informative_text:
        dialog.setInformativeText(informative_text)
    if detailed_text:
        dialog.setDetailedText(detailed_text)
    if checkbox_text:
        cb = QCheckBox(checkbox_text, dialog)
        cb.setChecked(checkbox_value)
        dialog.setCheckBox(cb)
    return dialog


def info_dialog(title: str, text: str, informative_text: str|None = None, detailed_text: str|None = None, checkbox_text: str|None = None, checkbox_value: bool = False):
    _make_dialog(title, text, informative_text, detailed_text, checkbox_text, checkbox_value, QMessageBox.Icon.Information).exec()


def _format_log_entry(title: str, text: str):
    return f'{title}: {text}'


def warning_dialog(title: str, text: str, informative_text: str|None = None, detailed_text: str|None = None, checkbox_text: str|None = None, checkbox_value: bool = False):
    logging.warning(_format_log_entry(title, text))
    _make_dialog(title, text, informative_text, detailed_text, checkbox_text, checkbox_value, QMessageBox.Icon.Warning).exec()


def error_dialog(title: str, text: str, informative_text: str|None = None, detailed_text: str|None = None, checkbox_text: str|None = None, checkbox_value: bool = False):
    logging.error(_format_log_entry(title, text))
    _make_dialog(title, text, informative_text, detailed_text, checkbox_text, checkbox_value, QMessageBox.Icon.Critical).exec()

def exception_dialog(title: str, text: str, informative_text: str|None = None, detailed_text: str|None = None, checkbox_text: str|None = None, checkbox_value: bool = False):
    logging.critical(_format_log_entry(title, text))
    _make_dialog(title, text, informative_text, detailed_text, checkbox_text, checkbox_value, QMessageBox.Icon.Critical).exec()


def okcancel_dialog(title: str, text: str, informative_text: str|None = None, detailed_text: str|None = None, checkbox_text: str|None = None, checkbox_value: bool = False) -> bool:
    dlg = _make_dialog(title, text, informative_text, detailed_text, checkbox_text, checkbox_value, QMessageBox.Icon.Information)
    dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    result = dlg.exec()
    return result==QMessageBox.StandardButton.Ok


def yesno_dialog(title: str, text: str, informative_text: str|None = None, detailed_text: str|None = None, checkbox_text: str|None = None, checkbox_value: bool = False) -> bool:
    dlg = _make_dialog(title, text, informative_text, detailed_text, checkbox_text, checkbox_value, QMessageBox.Icon.Question)
    dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    result = dlg.exec()
    return result==QMessageBox.StandardButton.Yes


def custom_buttons_dialog(title: str, text: str, buttons: list[str], informative_text: str|None = None, detailed_text: str|None = None) -> int:
    assert 1<=len(buttons)<=3, f'Expected 1..3 buttons, got {buttons}'
    dlg = _make_dialog(title, text, informative_text, detailed_text, None, None, QMessageBox.Icon.Question)
    dialog_buttons = {}
    for i,text in enumerate(buttons):
        obj = dlg.addButton(text, QMessageBox.ButtonRole.NoRole)
        dialog_buttons[obj] = i
    dlg.exec()
    btn = dlg.clickedButton()
    if btn in dialog_buttons:
        return dialog_buttons[btn]
    else:
        return 0


def _format_filters(filetypes: list[tuple[str,str]]) -> list[str]:
    result = []
    for (name,filter) in filetypes:
        if filter=='*':
            type_str = '*'
        else:
            assert filter.startswith('.'), f'Expected filter to start with ".", got "{filter}"'
            type_str = f'*{filter}'
        result.append(f'{name} ({type_str})')
    return result


def _open_file_dialog(parent, *, title: str = 'Open File', filetypes: list[tuple[str,str]] = None, allow_multiple: bool = False, initial_dir: str = None, initial_filename = None):
    """ filetypes: e.g. [('Text Files','.txt'),('All Files','*')]"""

    dialog = QFileDialog(parent)
    QtHelper.set_dialog_icon(dialog)
    if allow_multiple:
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    else:
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setWindowTitle(title)
    dialog.setViewMode(QFileDialog.ViewMode.Detail)
    if initial_dir and pathlib.Path(initial_dir).exists():
        dialog.setDirectory(initial_dir)
    elif Settings.last_dir_filedialog and pathlib.Path(Settings.last_dir_filedialog).exists():
        dialog.setDirectory(Settings.last_dir_filedialog)
    elif AppPaths.get_default_file_dir() and pathlib.Path(AppPaths.get_default_file_dir()).exists():
        dialog.setDirectory(AppPaths.get_default_file_dir())
    if initial_filename and pathlib.Path(initial_filename).exists():
        dialog.selectFile(initial_filename)
        dialog.setDirectory(str(pathlib.Path(initial_filename).parent))
    if filetypes:
        dialog.setNameFilters(_format_filters(filetypes))
    
    if not dialog.exec():
        return None
    
    path1 = dialog.selectedFiles()[0]
    Settings.last_dir_filedialog = str(pathlib.Path(path1).parent)
    
    if allow_multiple:
        return dialog.selectedFiles()
    else:
        return dialog.selectedFiles()[0]


def open_file_dialog(parent, *, title: str = 'Open File', filetypes: list[tuple[str,str]] = None, initial_dir: str = None, initial_filename = None) -> str:
    """ filetypes: e.g. [('Text Files','.txt'),('All Files','*')]"""
    return _open_file_dialog(parent, title=title, filetypes=filetypes, allow_multiple=False, initial_dir=initial_dir, initial_filename=initial_filename)


def open_files_dialog(parent, *, title: str = 'Open File', filetypes: list[tuple[str,str]] = None, allow_multiple: bool = False, initial_dir: str = None, initial_filename = None) -> list[str]:
    return _open_file_dialog(parent, title=title, filetypes=filetypes, allow_multiple=True, initial_dir=initial_dir, initial_filename=initial_filename)


def save_file_dialog(parent, *, title: str = 'Save File', filetypes: list[tuple[str,str]] = None, initial_dir: str = None, initial_filename = None) -> Optional[str]:
    """ filetypes: e.g. [('Text Files','.txt'),('All Files','*')]"""

    dialog = QFileDialog(parent)
    QtHelper.set_dialog_icon(dialog)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setWindowTitle(title)
    dialog.setViewMode(QFileDialog.ViewMode.Detail)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    if Settings.last_dir_filedialog and pathlib.Path(Settings.last_dir_filedialog).exists():
        dialog.setDirectory(Settings.last_dir_filedialog)
    elif AppPaths.get_default_file_dir() and pathlib.Path(AppPaths.get_default_file_dir()).exists():
        dialog.setDirectory(AppPaths.get_default_file_dir())
    if initial_dir and pathlib.Path(initial_dir).exists():
        dialog.setDirectory(initial_dir)
    elif initial_filename and pathlib.Path(initial_filename).exists():
        dialog.selectFile(initial_filename)
        dialog.setDirectory(str(pathlib.Path(initial_filename).parent))
    if filetypes:
        dialog.setNameFilters(_format_filters(filetypes))
    
    if not dialog.exec():
        return None
    
    path = dialog.selectedFiles()[0]
    Settings.last_dir_filedialog = str(pathlib.Path(path).parent)
    
    return path


def open_directory_dialog(parent, *, title: str = 'Open Directory', initial_dir: str = None) -> Optional[str]:

    dialog = QFileDialog(parent)
    QtHelper.set_dialog_icon(dialog)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setWindowTitle(title)
    dialog.setViewMode(QFileDialog.ViewMode.Detail)
    if initial_dir and pathlib.Path(initial_dir).exists():
        dialog.setDirectory(initial_dir)
    elif Settings.last_dir_dirdialog and pathlib.Path(Settings.last_dir_dirdialog).exists():
        dialog.setDirectory(Settings.last_dir_dirdialog)
    elif AppPaths.get_default_file_dir() and pathlib.Path(AppPaths.get_default_file_dir()).exists():
        dialog.setDirectory(AppPaths.get_default_file_dir())
    
    if not dialog.exec():
        return None
    
    dir = dialog.selectedFiles()[0]
    Settings.last_dir_dirdialog = dir
    
    return dir
