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
        self.load()

    
    def load(self):
        try:
            with open(self._file, 'r') as fp:
                data = json.load(fp)
            for n in self._defaults.keys():
                self.__dict__[n] = data[n]
        except Exception as ex:
            logging.warning(f'Unable to load settings ({ex})')
            self.reset()
    

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
        for k,v in self._defaults.items():
            self.__dict__[k] = v
