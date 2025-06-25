from __future__ import annotations

import os
import pathlib
import os
from functools import total_ordering



@total_ordering
class PathExt(pathlib.Path):
    """ An extension of Path with has the additional property arch_path, to represent a file inside an archive """

    def __init__(self, path, *, arch_path: str|None = None):
        super().__init__(path)
        self._arch_path = arch_path
    
    def __hash__(self) -> int:
        if self._arch_path:
            return hash(str(super()) + os.sep + self._arch_path)
        return super().__hash__()
    
    def __eq__(self, other) -> bool:
        if isinstance(other, PathExt):
            if self._arch_path != other._arch_path:
                return False
        return super().__eq__(other)

    def __lt__(self, other) -> bool:
        from .utils import natural_sort_key
        self_path = self.full_path
        if isinstance(other, PathExt):
            other_path = other.full_path
        else:
            other_path = str(super())
        return natural_sort_key(self_path) <= natural_sort_key(other_path)
    
    def is_in_arch(self) -> bool:
        return self._arch_path is not None
    
    @property
    def arch_path(self) -> str|None:
        return self._arch_path
    
    @property
    def arch_path_name(self) -> str|None:
        if not self._arch_path:
            return None
        return pathlib.Path(self._arch_path).name
    
    @property
    def arch_path_suffix(self) -> str|None:
        if not self._arch_path:
            return None
        return pathlib.Path(self._arch_path).suffix
    
    @property
    def full_name(self) -> str:
        if self._arch_path:
            return super().name + os.sep + pathlib.Path(self._arch_path).name
        return super().name
    
    @property
    def full_path(self) -> str:
        if self._arch_path:
            return str(super().absolute()) + os.sep + self._arch_path
        return str(super().absolute())
    
    @property
    def final_name(self) -> str:
        if self._arch_path:
            return pathlib.Path(self._arch_path).name
        return super().name
    
    def absolute(self) -> PathExt:
        return PathExt(super().absolute(), arch_path=self._arch_path)
