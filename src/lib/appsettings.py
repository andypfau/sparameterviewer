from logging import warning
import os, appdirs, json, logging



class AppSettings:


    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._defaults = {k: cls.__dict__[k] for k in cls.__annotations__.keys()}
        return obj


    def __init__(self, appname, author, version):
        self._dir = appdirs.user_config_dir(appname, author, version)
        self._file = os.path.join(self._dir, 'app_settings.json')
        self._observers = []
        self._inhbit_listeners = False
        self.load()


    def attach(self, callback: "callable[None,None]"):
        self._observers.append(callback)
    

    def notify(self):
        if self._inhbit_listeners:
            return
        for callback in self._observers:
            try:
                callback()
            except: pass
    

    def __setattr__(self, __name: str, __value: any) -> None:
        if '_defaults' in self.__dict__:
            if __name in self.__dict__['_defaults']:
                self.save()
                self.notify()
        super().__setattr__(__name, __value)

    
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
