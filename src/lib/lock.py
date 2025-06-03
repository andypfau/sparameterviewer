class Lock:

    def __init__(self, initially_locked: bool = False):
        self._lock_count = 1 if initially_locked else 0


    def __enter__(self):
        self._lock_count += 1
    
    
    def __exit__(self, type, value, traceback):
        self._lock_count -= 1

    
    def __nonzero__(self):
        return self.locked

    
    def __bool__(self):
        return self.locked


    @property
    def locked(self) -> bool:
        return self._lock_count > 0


    def force_unlock(self):
        self._lock_count = 0
