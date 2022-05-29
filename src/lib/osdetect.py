import os

def is_windows():
    return True if os.name=='nt' else False
