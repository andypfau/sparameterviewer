from PyQt6.QtWidgets import QMessageBox, QFileDialog
import logging
from typing import Union



def _make_dialog(title: str, text: str, extra_text: str, icon: QMessageBox.Icon) -> QMessageBox:
    dlg = QMessageBox()
    dlg.setIcon(icon)
    dlg.setWindowTitle(title)
    dlg.setText(text)
    if extra_text:
        dlg.setInformativeText(extra_text)
    return dlg


def info_dialog(title: str, text: str, extra_text: str = None):
    _make_dialog(title, text, extra_text, QMessageBox.Icon.Information).exec()


def warning_dialog(title: str, text: str, extra_text: str = None):
    logging.warning(text)
    if extra_text:
        logging.warning(extra_text)
    _make_dialog(title, text, extra_text, QMessageBox.Icon.Warning).exec()


def exception_dialog(title: str, text: str, extra_text: str = None):
    logging.critical(text)
    if extra_text:
        logging.critical(extra_text)
    _make_dialog(title, text, extra_text, QMessageBox.Icon.Critical).exec()


def error_dialog(title: str, text: str, extra_text: str = None):
    logging.error(text)
    if extra_text:
        logging.error(extra_text)
    _make_dialog(title, text, extra_text, QMessageBox.Icon.Critical).exec()


def okcancel_dialog(title: str, text: str, extra_text: str = None) -> bool:
    dlg = _make_dialog(title, text, extra_text, QMessageBox.Icon.Question)
    dlg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
    result = dlg.exec()
    return result==QMessageBox.StandardButton.Ok


def yesno_dialog(title: str, text: str, extra_text: str = None) -> bool:
    dlg = _make_dialog(title, text, extra_text, QMessageBox.Icon.Question)
    dlg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    result = dlg.exec()
    return result==QMessageBox.StandardButton.Yes


def _get_filter_str(filetypes):
    result = ''
    for (name,filter) in filetypes:
        if filter=='*':
            type_str = '*.*'
        else:
            type_str = f'*{filter}'
        if result != '':
            result += ';;'
        result += f'{name} ({type_str})'
    return result


def open_file_dialog(parent, *, title: str = 'Open File', filetypes: list[tuple[str,str]] = None, allow_multiple: bool = False, initial_dir: str = None) -> Union[str,list[str],None]:
    """ filetypes: e.g. [('Text Files','.txt'),('All Files','*')]"""

    kwargs = dict(parent=parent, caption=title)
    if initial_dir:
        kwargs['directory'] = initial_dir
    if filetypes:
        kwargs['filter'] = _get_filter_str(filetypes)
        kwargs['initialFilter'] = _get_filter_str(filetypes[0:1])

    if allow_multiple:
        (filenames, _) = QFileDialog.getOpenFileNames(**kwargs)
        if len(filenames)==0:
            return None
        return filenames
    else:
        (filename, _) = QFileDialog.getOpenFileName(**kwargs)
        if filename=='':
            return None
        return filename


def save_file_dialog(parent, *, title: str = 'Save File', filetypes: list[tuple[str,str]] = None, initial_dir: str = None) -> bool:
    """ filetypes: e.g. [('Text Files','.txt'),('All Files','*')]"""

    kwargs = dict(parent=parent, caption=title)
    if initial_dir:
        kwargs['directory'] = initial_dir
    if filetypes:
        kwargs['filter'] = _get_filter_str(filetypes)
        kwargs['initialFilter'] = _get_filter_str(filetypes[0:1])

    (filename, _) = QFileDialog.getSaveFileName(**kwargs)
    if filename=='':
        return None
    return filename


def open_directory_dialog(parent, *, title: str = 'Open Directory', initial_dir: str = None) -> Union[str,None]:
    kwargs = dict(parent=parent, caption=title)
    if initial_dir:
        kwargs['directory'] = initial_dir

    dir = QFileDialog.getExistingDirectory(**kwargs)
    if dir=='':
        return None
    return dir
