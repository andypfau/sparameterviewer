from __future__ import annotations

from typing import override, Callable
from lib import Settings

import logging



class LogHandler(logging.StreamHandler):    
    

    _instance: LogHandler|None = None


    def __init__(self):
        assert LogHandler._instance is None
        self._records: list[logging.LogRecord] = []
        self._observers: list[Callable[tuple[logging.LogRecord],None]] = []
        super().__init__(logging.DEBUG)
    

    @classmethod
    def inst(cls):
        if cls._instance is None:
            cls._instance = LogHandler()
            logging.getLogger().addHandler(cls._instance)
        return cls._instance


    @override
    def emit(self, record: logging.LogRecord):
        """ implementation of logging.Handler.emit()"""
        self._records.append(record)
        self._notify(record)


    def clear(self):
        self._records = []
        self._notify()
    

    def get_records(self, level=logging.INFO) -> list[logging.LogRecord]:
        return [record for record in self._records if record.levelno >= level]
    

    def get_messages(self, level=logging.INFO) -> list[str]:
        return [f'{record.levelname}: {record.message} ({record.exc_text})' for record in self.get_records(level)]


    def _notify(self, record: logging.LogRecord|None):
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](record)
            except Exception as ex:
                del self._observers[i]


    def attach(self, callback: Callable[tuple[logging.LogRecord],None]):
        """ Attach a log listener """
        self._observers.append(callback)
