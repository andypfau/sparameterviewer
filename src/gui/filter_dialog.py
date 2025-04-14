from .filter_dialog_ui import FilterDialogUi
from .helpers.settings import Settings
from typing import Optional
import re


class FilterDialog(FilterDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
        self._files: list[str] = []
        self._matched_files: list[str] = []
    

    def show_modal_dialog(self, files: list[str]) -> Optional[list[str]]:
        self._files = files
        self._matched_files = []
        self.ui_set_files(files)
        self.ui_regex_mode = Settings.search_regex
        if Settings.search_regex:
            self.ui_search_text = '.*'
        else:
            self.ui_search_text = '*'
        if super().ui_show_modal():
            if len(self._matched_files) > 0:
                return self._matched_files
        return None
    

    def do_filtering(self):

        def wildcard_to_regex(search):
            rex_str = ''
            parts = re.split(r'([*?])', search)
            for part in parts:
                if part=='*':
                    rex_str += '.*'
                elif part=='?':
                    rex_str += '.'
                else:
                    rex_str +=re.escape(part)
            return rex_str

        if self.ui_search_text:
            try:
                if self.ui_regex_mode:
                    rex_str = self.ui_search_text
                else:
                    rex_str = wildcard_to_regex(self.ui_search_text)
                rex = re.compile(rex_str, re.IGNORECASE)
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


    def on_search_change(self):
        self.do_filtering()
        

    def on_search_mode_change(self):
        self.do_filtering()
    