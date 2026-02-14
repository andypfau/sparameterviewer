from .helpers.file_filter import FileFilter
from .filter_dialog_ui import FilterDialogUi
from lib import Settings, PathExt, natural_sort_key
from typing import Optional
import re
import enum
import dataclasses


class FilterDialog(FilterDialogUi):

    
    class Mode(enum.StrEnum):
        Filter = 'filter'
        Check = 'check'
        Slice = 'slice'


    @dataclasses.dataclass
    class Result:
        action: FilterDialogUi.Action
        filter: FileFilter
        files: list[PathExt]


    def __init__(self, parent, mode: FilterDialog.Mode):
        super().__init__(parent, str(mode))
        self._mode = mode
        self._files: list[PathExt] = []
        self._matched_files: list[PathExt] = []
    

    def show_modal_dialog(self, files: list[PathExt]) -> Result:
        self._files = files
        self._matched_files = []
        
        self._set_displayed_files([], self._files)
        self.ui_regex_mode = Settings.search_regex
        if self._mode == FilterDialog.Mode.Check:
            self.ui_search_text = Settings.last_select_dialog_str
        elif self._mode == FilterDialog.Mode.Filter:
            self.ui_search_text = Settings.last_filter_dialog_str
        elif self._mode == FilterDialog.Mode.Slice:
            self.ui_search_text = Settings.last_slice_dialog_str

        result = super().ui_show_modal()
        match result:
            case FilterDialogUi.Action.Select:
                filter = self._get_filter(failsafe=True)
            case FilterDialogUi.Action.SelectInverted:
                filter = self._get_filter(failsafe=True, invert=True)
            case _:
                filter = FileFilter()
        files = self.ui_get_selected_files() if self._mode==FilterDialog.Mode.Check else []
        
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
            
            if self._mode == FilterDialog.Mode.Slice:
                matches = [filter.get_match(file) for file in self._files]
                self._matched_files = list(set([PathExt(match_str) for _,does_match,match_str in matches if does_match]))
                unmatched_files = [path for path,does_match,_ in matches if not does_match]
            else:
                self._matched_files = [file for file in self._files if filter.matches(file)]
                unmatched_files = [file for file in self._files if not filter.matches(file)]
            self._set_displayed_files(self._matched_files, unmatched_files)
            self.ui_indicate_search_error(False)

        else:
            self.ui_indicate_search_error(False)
            self._set_displayed_files([], self._files)


    def on_search_change(self):
        if self._mode == FilterDialog.Mode.Check:
            Settings.last_select_dialog_str = self.ui_search_text
        elif self._mode == FilterDialog.Mode.Filter:
            Settings.last_filter_dialog_str = self.ui_search_text
        elif self._mode == FilterDialog.Mode.Slice:
            Settings.last_slice_dialog_str = self.ui_search_text
        self.do_filtering()
        

    def on_search_mode_change(self):
        Settings.search_regex = self.ui_regex_mode
        self.do_filtering()
    