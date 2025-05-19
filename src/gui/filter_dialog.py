from .filter_dialog_ui import FilterDialogUi
from lib import Settings, PathExt
from typing import Optional
import re


class FilterDialog(FilterDialogUi):

    def __init__(self, parent):
        super().__init__(parent)
        self._files: list[str] = []
        self._matched_files: list[str] = []
    

    def show_modal_dialog(self, files: list[PathExt]) -> Optional[list[PathExt]]:
        self._files: list[PathExt] = files
        self._matched_files: list[PathExt] = []
        
        self._set_displayed_files([], self._files)
        self.ui_regex_mode = Settings.search_regex
        self.ui_search_text = Settings.last_search
        if super().ui_show_modal():
            if len(self._matched_files) > 0:
                return self._matched_files
        return None


    def _set_displayed_files(self, matched_files: list[PathExt], unmatched_files: list[PathExt]):
        self.ui_set_files([file.final_name for file in matched_files], [file.final_name for file in unmatched_files])
    

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
                    rex_str += re.escape(part)
            return rex_str

        if self.ui_search_text:
            try:
                if self.ui_regex_mode:
                    rex_str = self.ui_search_text
                else:
                    rex_str = wildcard_to_regex(self.ui_search_text)
                rex = re.compile(rex_str, re.IGNORECASE)
            except:
                self._set_displayed_files([], self._files)
                self.ui_indicate_search_error(True)
                return
            
            
            self._matched_files = [file for file in self._files if rex.search(file.final_name)]
            unmatched_files = [file for file in self._files if not rex.search(file.final_name)]
            self._set_displayed_files(self._matched_files, unmatched_files)
            self.ui_indicate_search_error(False)

        else:
            self.ui_indicate_search_error(False)
            self._set_displayed_files([], self._files)


    def on_search_change(self):
        Settings.last_search = self.ui_search_text
        self.do_filtering()
        

    def on_search_mode_change(self):
        Settings.search_regex = self.ui_regex_mode
        self.do_filtering()
    