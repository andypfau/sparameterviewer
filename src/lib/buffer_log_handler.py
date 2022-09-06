import logging


class BufferLogHandler(logging.Handler):
   
    def __init__(self, level):
        self.count = 0
        self.entries = []
        super().__init__(level)

    def emit(self, record):
        self.count += 1
        self.entries.append(f'{record.levelname}: {record.message} ({record.exc_text})')
