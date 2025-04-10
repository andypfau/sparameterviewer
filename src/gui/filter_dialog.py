from .filter_dialog_ui import FilterDialogUi
from typing import Union
import re


class FilterDialog(FilterDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
        self._files: list[str] = []
        self._matched_files: list[str] = []
    

    def show_modal_dialog(self, files: list[str]) -> Union[list[str]|None]:
        self._files = files
        self._matched_files = []
        self.ui_set_files(files)
        if super().ui_show_modal():
            if len(self._matched_files) > 0:
                return self._matched_files
        return None


    def on_search_change(self):
        if self.ui_search_text:
            try:
                rex = re.compile(self.ui_search_text, re.IGNORECASE)
            except:
                self.ui_set_files(self._files)
                self.ui_indicate_search_error(True)
                return
            self._matched_files = [file for file in self._files if rex.search(file)]
            self.ui_set_files(self._matched_files)
            self.ui_indicate_search_error(False)
        else:
            self.ui_indicate_search_error(False)
            self.ui_set_files(self._files)
