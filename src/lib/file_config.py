from __future__ import annotations
from .path_ext import PathExt
from .settings import Settings
from typing import Callable



class FileConfigSingleton:
    
    
    class Attribute:


        def __init__(self, setting_name: str):
            self._setting_name = setting_name

        
        def get(self, path: PathExt, default: str|None = None) -> str|None:
            return getattr(Settings,self._setting_name).get(str(path), default)
        

        def clear(self):
            setattr(Settings, self._setting_name, dict())
        

        def __getitem__(self, key):
            if not isinstance(key, PathExt):
                raise ValueError()
            return getattr(Settings,self._setting_name).get(str(key), None)
        

        def __setitem__(self, key, value):
            if not isinstance(key, PathExt):
                raise ValueError()
            storage = getattr(Settings,self._setting_name)
            if value:
                storage[str(key)] = value
            else:
                del storage[str(key)]
            setattr(Settings, self._setting_name, storage)
        

        def __delitem__(self, key):
            if not isinstance(key, PathExt):
                raise ValueError()
            storage = getattr(Settings,self._setting_name)
            if str(key) in storage:
                del storage[str(key)]
                setattr(Settings, self._setting_name, storage)


    _instance = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    def __init__(self):
        self._labels = FileConfigSingleton.Attribute('custom_label_history')
        self._colors = FileConfigSingleton.Attribute('custom_color_history')
        self._styles = FileConfigSingleton.Attribute('custom_style_history')
    

    @property
    def labels(self) -> FileConfigSingleton.Attribute:
        return self._labels

    @property
    def colors(self) -> FileConfigSingleton.Attribute:
        return self._colors

    @property
    def styles(self) -> FileConfigSingleton.Attribute:
        return self._styles


FileConfig = FileConfigSingleton()
