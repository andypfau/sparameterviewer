from .filter_dialog_ui import FilterDialogUi
from lib import Settings, PathExt, natural_sort_key
from typing import Optional
import re
import dataclasses


class FilterDialog(FilterDialogUi):


    @dataclasses.dataclass
    class Result:
        action: FilterDialogUi.Action
        files: list[PathExt]


    def __init__(self, parent):
        super().__init__(parent)
        self._files: list[PathExt] = []
        self._matched_files: list[PathExt] = []
    

    def show_modal_dialog(self, files: list[PathExt]) -> Result:
        self._files = files
        self._matched_files = []
        
        self._set_displayed_files([], self._files)
        self.ui_regex_mode = Settings.search_regex
        self.ui_search_text = Settings.last_search
        
        return FilterDialog.Result(super().ui_show_modal(), self.ui_get_selected_files())


    def _set_displayed_files(self, matched_files: list[PathExt], unmatched_files: list[PathExt]):
        matched_files = sorted(matched_files, key=lambda item: natural_sort_key(item.final_name))
        unmatched_files = sorted(unmatched_files, key=lambda item: natural_sort_key(item.final_name))
        self.ui_set_files([file for file in matched_files], [file for file in unmatched_files])
    

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
    