from logging import warning
import os, json, logging



class AppSettings:


    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._defaults = {k: cls.__dict__[k] for k in cls.__annotations__.keys()}
        return obj


    def __init__(self, format_version_str: str):
        from lib import AppPaths
        self._dir = AppPaths.get_settings_dir(format_version_str)
        self._file = AppPaths.get_settings_path(format_version_str)
        self._observers = []
        self._inhbit_listeners = False
        self.load()


    def attach(self, callback: "callable[None,None]"):
        self._observers.append(callback)
    

    def notify(self):
        if self._inhbit_listeners:
            return
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i]()
            except Exception as ex:
                logging.debug(f'Remove setting observer {i} ({ex})')
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
            for n in self._defaults.keys():
                try:
                    self.__dict__[n] = data[n]
                except Exception as ex:
                    logging.warning(f'Unable to load setting <{n}>, using default ({ex})')
                    self.__dict__[n] = self._defaults[n]
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
            os.makedirs(self._dir, exist_ok=True) 
            with open(self._file, 'w') as fp:
                json.dump(data, fp)
        except Exception as ex:
            logging.warning(f'Unable to save settings ({ex})')
    

    def reset(self):
        self._inhbit_listeners = True
        for k,v in self._defaults.items():
            self.__dict__[k] = v
        self.save()
        self._inhbit_listeners = False
        self.notify()
