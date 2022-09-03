from logging import warning
import os, appdirs, json, logging



class AppSettings:

    
    def __init__(self, appname: str, author: str, version: str, settings_and_defaults: "dict(str,any)"):
        self._dir = appdirs.user_config_dir(appname, author, version)
        self._file = os.path.join(self._dir, 'app_settings.json')
        self._defaults = {}
        for n,s in settings_and_defaults.items():
            self.__dict__[n] = s
            self._defaults[n] = s
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
        for n,s in self._defaults.items():
            self.__dict__[n] = s



app_settings = AppSettings('apfau.de S-Parameter Viewer', 'apfau.de', '0.1', dict(
    plot_mode = 0,
    plot_unit = 0,
    show_legend = True,
    log_freq = False,
    always_show_names = False,
    expression = '',
    td_kaiser = 35.0,
    lock_xaxis = False,
    lock_yaxis = False,
))
