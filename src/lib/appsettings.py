from .apppaths import AppPaths
from logging import warning
import os, json, logging
from typing import Callable



class AppSettings:


    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._defaults = {k: cls.__dict__[k] for k in cls.__annotations__.keys()}
        return obj


    def __init__(self, format_version_str: str):
        self._file = AppPaths.get_settings_path(format_version_str)
        self._observers: list[Callable[None,None]] = []
        self._inhbit_listeners = False
        self._load()
    

    @property
    def settings_file_path(self) -> str:
        return os.path.abspath(self._file)


    def attach(self, callback: Callable[tuple[list[str]],None]):
        self._observers.append(callback)
    

    def _notify(self, attributes: list[str]):
        if self._inhbit_listeners:
            return
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](attributes)
            except Exception as ex:
                del self._observers[i]
    

    def __setattr__(self, __name: str, __value: any) -> None:
        is_setting = ('_defaults' in self.__dict__) and (__name in self.__dict__['_defaults'])
        if is_setting:
            current_value = self.__getattribute__(__name)
            if __value == current_value:
                return
        super().__setattr__(__name, __value)
        if is_setting:
            self._save()
            self._notify([__name])

    
    def _load(self):
        self._inhbit_listeners = True
        try:
            with open(self._file, 'r') as fp:
                data = json.load(fp)
            for setting_name in self._defaults.keys():
                
                initial_value = self._defaults[setting_name]
                try:
                    loaded_value = data[setting_name]
                    expected_type = type(self._defaults[setting_name])
                    try:
                        initial_value = expected_type(loaded_value)
                    except (ValueError, TypeError) as ex:
                        logging.warning(f'Casting <{loaded_value}> to {expected_type} failed, using default <{initial_value}> ({ex})')
                except Exception as ex:
                    logging.warning(f'Unable to load setting <{setting_name}>, using default <{initial_value}> ({ex})')
                
                self.__dict__[setting_name] = initial_value
                
        except Exception as ex:
            logging.warning(f'Unable to load settings ({ex})')
            self._reset()
        self._inhbit_listeners = False
        self._notify([*self._defaults.keys()])
    

    def _save(self):
        try:
            data = {}
            for n in self._defaults.keys():
                data[n] = self.__dict__[n]
            
            dir = os.path.dirname(self._file)
            os.makedirs(dir, exist_ok=True) 

            with open(self._file, 'w') as fp:
                json.dump(data, fp, indent=4)
        except Exception as ex:
            logging.warning(f'Unable to save settings ({ex})')
    

    def _reset(self):
        self._inhbit_listeners = True
        for k,v in self._defaults.items():
            self.__dict__[k] = v
        self._save()
        self._inhbit_listeners = False
        self._notify([*self._defaults.keys()])
