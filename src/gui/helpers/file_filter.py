from lib import PathExt

import re


class FileFilter:
    
    def __init__(self, filter: str = None, regex: bool = False, full_match: bool = False, negate: bool = False):
        self._filter, self._regex, self._full_match, self._negate = filter, regex, full_match, negate
        
        self._compiled_regex: "re.Pattern|None"
        if filter is None or filter == '':
            self._regex_str = None
            self._compiled_regex = None
        else:
            if not regex:
                filter = self._wildcard_to_regex(filter)
            self._regex_str = filter
            self._compiled_regex = re.compile(filter, re.IGNORECASE)
    
    def __eq__(self, other):
        if not isinstance(other, FileFilter):
            return False
        if not self._filter == other._filter:
            return False
        if not self._regex == other._regex:
            return False
        if not self._full_match == other._full_match:
            return False
        if not self._negate == other._negate:
            return False
        return True
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    @staticmethod
    def _wildcard_to_regex(search):
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

    @property
    def filter(self) -> str|None:
        if not self.active:
            return None
        return self._filter
    
    @property
    def regex_str(self) -> str:
        return self._regex_str
    
    @property
    def regex(self) -> bool:
        return self._regex
    
    @property
    def full_match(self) -> bool:
        return self._full_match
    
    @property
    def negate(self) -> bool:
        return self._negate
    
    @property
    def active(self) -> bool:
        return self._compiled_regex is not None

    def _match(self, s: str) -> "re.Match|None":
        assert self._compiled_regex is not None
        if self._full_match:
            return self._compiled_regex.match(s)
        else:
            return self._compiled_regex.search(s)

    def matches(self, path: PathExt) -> bool:
        if self._compiled_regex is None:
            return True
        return bool(self._match(path.final_name)) != self._negate

    def get_match(self, path: PathExt) -> tuple[PathExt,bool,str|None]:
        if self._compiled_regex is None:
            return path, True, None
        m = self._match(path.final_name)
        if m:
            return path, not self._negate, m.group(0)
        else:
            return path, self._negate, None
