from .helpers.file_filter import FileFilter
from .filter_dialog_ui import FilterDialogUi
from lib import Settings, PathExt, natural_sort_key
from typing import Optional
import re
import dataclasses


class FilterDialog(FilterDialogUi):


    @dataclasses.dataclass
    class Result:
        action: FilterDialogUi.Action
        filter: FileFilter
        files: list[PathExt]


    def __init__(self, parent, select_mode: bool):
        super().__init__(parent, select_mode)
        self._files: list[PathExt] = []
        self._matched_files: list[PathExt] = []
    

    def show_modal_dialog(self, files: list[PathExt]) -> Result:
        self._files = files
        self._matched_files = []
        
        self._set_displayed_files([], self._files)
        self.ui_regex_mode = Settings.search_regex
        self.ui_search_text = Settings.last_search

        result = super().ui_show_modal()
        filter = self._get_filter(failsafe=True, invert=result==FilterDialogUi.Action.Remove)
        files = self.ui_get_selected_files() if self._select_mode else []
        
        return FilterDialog.Result(result, filter, files)


    def _set_displayed_files(self, matched_files: list[PathExt], unmatched_files: list[PathExt]):
        matched_files = sorted(matched_files, key=lambda item: natural_sort_key(item.final_name))
        unmatched_files = sorted(unmatched_files, key=lambda item: natural_sort_key(item.final_name))
        self.ui_set_files_and_selection([file for file in matched_files], [file for file in unmatched_files])
    

    def _get_filter(self, failsafe: bool = False, invert: bool = False) -> FileFilter:
        def get():
            return FileFilter(self.ui_search_text, self.ui_regex_mode, negate=invert)
        try:
            return get()
        except:
            if failsafe:
                return FileFilter()
            raise
    

    def do_filtering(self):


        if self.ui_search_text:
            try:
                filter = self._get_filter()
            except:
                self._set_displayed_files([], self._files)
                self.ui_indicate_search_error(True)
                return
            
            self._matched_files = [file for file in self._files if filter.apply(file)]
            unmatched_files = [file for file in self._files if not filter.apply(file)]
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
    