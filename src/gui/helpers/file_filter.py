from lib import PathExt

import re


class FileFilter:
    
    def __init__(self, filter: str = None, regex: bool = False, full_match: bool = False, negate: bool = False):
        self._filter, self._regex, self._full_match, self._negate = filter, regex, full_match, negate
        
        if filter is None or filter == '':
            self._fn = lambda name: True
        else:
            if not regex:
                filter = self._wildcard_to_regex(filter)
            compiled_regex = re.compile(filter, re.IGNORECASE)
            if self._full_match:
                self._fn = lambda name: bool(compiled_regex.match(name)) != negate
            else:
                self._fn = lambda name: bool(compiled_regex.search(name)) != negate
    
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
        return self._fn is not None

    def matches(self, path: PathExt) -> bool:
        return self._fn(path.final_name)
