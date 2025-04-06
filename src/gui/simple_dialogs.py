from PyQt6.QtWidgets import QMessageBox, QFileDialog
import logging



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
    _make_dialog(title, text, extra_text, QMessageBox.Icon.Warning).exec()


def exception_dialog(title: str, text: str, extra_text: str = None):
    logging.critical(text)
    _make_dialog(title, text, extra_text, QMessageBox.Icon.Critical).exec()


def error_dialog(title: str, text: str, extra_text: str = None):
    logging.error(text)
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
