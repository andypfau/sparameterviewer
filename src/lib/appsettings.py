from logging import warning
import os, json, logging
from typing import Callable



class AppSettings:


    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._defaults = {k: cls.__dict__[k] for k in cls.__annotations__.keys()}
        return obj


    def __init__(self, format_version_str: str):
        from lib import AppPaths
        self._file = AppPaths.get_settings_path(format_version_str)
        self._observers: list[Callable[None,None]] = []
        self._inhbit_listeners = False
        self.load()


    def attach(self, callback: Callable[None,None]):
        self._observers.append(callback)
    

    def notify(self):
        if self._inhbit_listeners:
            return
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i]()
            except Exception as ex:
                del self._observers[i]
    

    def __setattr__(self, __name: str, __value: any) -> None:
        super().__setattr__(__name, __value)
        if '_defaults' in self.__dict__:
            if __name in self.__dict__['_defaults']:
                self.save()
                self.notify()

    
    def load(self):
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
            self.reset()
        self._inhbit_listeners = False
        self.notify()
    

    def save(self):
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
    

    def reset(self):
        self._inhbit_listeners = True
        for k,v in self._defaults.items():
            self.__dict__[k] = v
        self.save()
        self._inhbit_listeners = False
        self.notify()
