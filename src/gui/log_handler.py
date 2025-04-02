from .settings import Settings

import logging



class LogHandler(logging.StreamHandler):    
    
    _instance: "LogHandler|None" = None


    def __init__(self):
        assert LogHandler._instance is None
        self._records: list[logging.LogRecord] = []
        self._observers: list[callable] = []
        super().__init__(logging.DEBUG)
    

    @classmethod
    def inst(cls):
        if cls._instance is None:
            cls._instance = LogHandler()
            logging.getLogger().addHandler(cls._instance)
        return cls._instance


    def emit(self, record: logging.LogRecord):
        """ implementation of logging.Handler.emit()"""
        self._records.append(record)
        self._notify()


    def clear(self):
        self._records = []
        self._notify()
    

    def get_messages(self, level=logging.INFO) -> list[str]:
        return [f'{record.levelname}: {record.message} ({record.exc_text})' for record in self._records if record.levelno >= level]


    def _notify(self):
        for callback in self._observers:
            try:
                callback()
            except: pass


    def attach(self, callback: "callable[None,None]"):
        """ Attach a log listener """
        self._observers.append(callback)

    
    def detach(self, callback: "callable[None,None]"):
        """ Detach a log listener """
        try:
            self._observers.remove(callback)
        except:
            pass
