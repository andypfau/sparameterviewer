import os, appdirs, json, warnings


class AppSettings:
    
    def __init__(self, appname: str, author: str, version: str, settings_and_defaults: "dict(str,any)", error_callback: "callable[[str],None]|None" = None):
        self._dir = appdirs.user_config_dir(appname, author, version)
        self._file = os.path.join(self._dir, 'app_settings.json')
        self._defaults = {}
        for n,s in settings_and_defaults.items():
            self.__dict__[n] = s
            self._defaults[n] = s
        if error_callback is not None:
            self._error_callback = error_callback
        else:
            self._error_callback = lambda msg: warnings.warn(msg)
        self.load()
    
    def load(self):
        try:
            with open(self._file, 'r') as fp:
                data = json.load(fp)
            for n in self._defaults.keys():
                self.__dict__[n] = data[n]
        except Exception as ex:
            self._error_callback(f'Unable to load settings ({ex})')
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
            self._error_callback(f'Unable to save settings ({ex})')
    
    def reset(self):
        for n,s in self._defaults.items():
            self.__dict__[n] = s
