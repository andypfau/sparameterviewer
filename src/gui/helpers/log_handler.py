from __future__ import annotations

from typing import override, Callable

import dataclasses
import logging
import time



class LogHandler(logging.StreamHandler):


    @dataclasses.dataclass
    class Record:
        timestamp: float
        message: str
        file: str
        level: int
        level_name: str
    

    _instance: LogHandler|None = None


    def __init__(self):
        assert LogHandler._instance is None, f'Expected log handler instance to be unset, got {LogHandler._instance}'
        self._records: list[LogHandler.Record] = []
        self._observers: list[Callable[tuple[LogHandler.Record],None]] = []
        self._t_start = time.monotonic()
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
        entry = LogHandler.Record(time.monotonic()-self._t_start, record.msg, record.filename, record.levelno, record.levelname)
        self._records.append(entry)
        self._notify(entry)


    def clear(self):
        self._records = []
        self._notify()
    

    def get_records(self, level=logging.INFO) -> list[LogHandler.Record]:
        return [record for record in self._records if record.level >= level]
    

    def get_formatted_messages(self, level=logging.INFO) -> list[str]:
        return [f'{record.timestamp:09.3f}, {str(record.level_name).capitalize()}: {record.message}' for record in self.get_records(level)]


    def _notify(self, record: LogHandler.Record|None):
        for i in reversed(range(len(self._observers))):
            try:
                self._observers[i](record)
            except Exception as ex:
                del self._observers[i]


    def attach(self, callback: Callable[tuple[LogHandler.Record|None],None]):
        """ Attach a log listener """
        self._observers.append(callback)
