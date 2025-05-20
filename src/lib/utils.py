import os
import sys
import string
import subprocess
import pathlib
import re
import io
import numpy as np
import math
import zipfile
import logging
import tempfile
import traceback



_rex_filetypes = re.compile(r'^\.(s[0-9]+p)|(ci?ti)$', re.IGNORECASE)
_rex_archtypes = re.compile(r'^\.zip$', re.IGNORECASE)


def is_ext_supported_file(ext: str) -> bool:
    return _rex_filetypes.match(ext)


def is_ext_supported_archive(ext: str) -> bool:
    return _rex_archtypes.match(ext)


def is_ext_supported(ext: str) -> bool:
    return _rex_filetypes.match(ext) or _rex_archtypes.match(ext)


def find_files_in_archive(path: str) -> list[str]:
    result = []
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            for internal_name in zf.namelist():
                ext = os.path.splitext(internal_name)[1]
                if is_ext_supported_file(ext):
                    result.append(internal_name)
    except Exception as ex:
        logging.warning(f'Unable to open zip file <{path}>: {ex}')
    return result


def load_file_from_archive(archive_path: str, path_in_archive: str, target_path: str = None) -> str:
    """ Extracts a file from an archive, returns the path of the extracted file """
    with zipfile.ZipFile(archive_path, 'r') as zf:
        return zf.extract(path_in_archive, target_path)


class AchiveFileLoader:
    """
    Usage:
        with AchiveFileLoader('/path/arch.zip', 'file.ext') as extracted_path:
            # The extracted file is at <extracted_path>, in a temporary directory.
            # The directory will be deleted when you exit the context manager.
            ...
    """

    def __init__(self, archive_path: str, path_in_archive: str):
        self._archive_path, self._path_in_archive = archive_path, path_in_archive
        self._tempdir: tempfile.TemporaryDirectory = None
        self._tempdir_path: str = None

    def __enter__(self) -> str:
        self._tempdir = tempfile.TemporaryDirectory()
        self._tempdir_path = self._tempdir.__enter__()
        with zipfile.ZipFile(self._archive_path, 'r') as zf:
            return zf.extract(self._path_in_archive, self._tempdir_path)

    def __exit__(self, exc, value, tb):
        self._tempdir.__exit__(exc, value, tb)
        


def get_unique_short_filename(name: str, all_names: "list[str]", min_length: int = 5) -> "str":
    def is_unique(item: str, all: "list[str]") -> bool:
        hits = 0
        for other in all:
            if item in other:
                hits += 1
                if hits > 1:
                    return False
        return True
    
    result = name
        
    # try to remove extension
    fn,_ = os.path.splitext(result)
    if is_unique(result, all_names):
        result = fn

    if len(result) <= min_length:
        # just use full name
        return result
    
    # crop off as much as possible at the end
    excess_end = 0
    for i in range(len(result)):
        short = result[:-1-i]
        if is_unique(short, all_names):
            excess_end = i
        else:
            break
    if excess_end > 3:
        excess_end = min(excess_end-3, len(result)-8)
        result = result[:-excess_end]

    # crop off as much as possible at the beginning
    excess_start = 0
    for i in range(len(result)):
        short = result[i:]
        if is_unique(short, all_names):
            excess_start = i
        else:
            break
    if excess_start > 3:
        excess_start = min(excess_start-3, len(result)-8)
        result = result[excess_start:]
    
    return result


def is_windows():
    return True if os.name=='nt' else False


def is_running_from_binary() -> bool:
    try:
        # see <https://pyinstaller.org/en/stable/runtime-information.html>
        if getattr(sys, 'frozen', False):
            return True
    except:
        pass # ignore
    return False


def sanitize_filename(filename: str) -> str:
    VALID_CHARS = '+-_' + string.ascii_letters + string.digits
    sanitized = [char for char in filename if char in VALID_CHARS]
    return ''.join(sanitized)


def open_file_in_default_viewer(filename: str):
    if is_windows():
        os.startfile(filename)
    else:
        start_process('xdg-open', filename)


def start_process(binary_path: str, *args):
    subprocess.Popen([binary_path, *args], start_new_session=True)


def v2db(v):
    return 20*np.log10(np.maximum(1e-15, np.abs(v)))


def group_delay(frequencies, sparams):
    d_phase = np.diff(np.unwrap(np.angle(sparams)))
    d_freq = np.diff(frequencies)
    return frequencies[1:], -d_phase/d_freq


def shorten_path(path: str, max_len: int) -> str:
    short_path = path
    parts_to_drop = 0
    while True:
        if len(short_path) <= max_len:
            break  # already short enough
        
        parts = list(pathlib.Path(path).parts)
        parts_to_drop += 1
        i0 = len(parts)//2 - parts_to_drop//2
        i1 = i0+parts_to_drop-1
        del parts[i0:i1+1]
        parts.insert(i0, '...')
        if len(parts) < 2:
            break  # cannot be shortened any more
        
        short_path_obj = pathlib.Path(parts[0])
        for part in parts[1:]:
            short_path_obj = short_path_obj / part
        short_path = str(short_path_obj)
    return short_path


def natural_sort_key(s):
    def prepare_token(s: str):
        if s.isdigit():
            try:
                return int(s)
            except:
                s
        else:
            return s.casefold()
    return [prepare_token(part) for part in re.split('([0-9]+)', s)]



def get_next_1_2_5_10(x: int) -> int:
    """ Returns the next in the series (1, 2, 5, 10, 20, 50, 100, ...)"""
    EPSILON = 0.99
    if x < 1:
        return 1
    f, i = math.modf(math.log10(x))
    if f < math.log10(2) * EPSILON:
        return 2*int(round(10**i))
    elif f < math.log10(5) * EPSILON:
        return 5*int(round(10**i))
    else:
        return int(round(10**(i+1)))



def get_next_1_3_10(x: int) -> int:
    """ Returns the next in the series (1, 3, 10, 30, 100, ...)"""
    EPSILON = 0.99
    if x < 1:
        return 1
    f, i = math.modf(math.log10(x))
    if f < math.log10(3) * EPSILON:
        return 3*int(round(10**i))
    else:
        return int(round(10**(i+1)))



def get_next_1_10_100(x: int) -> int:
    """ Returns the next in the series (1, 10, 100, 1000, ...)"""
    if x < 1:
        return 1
    return int(round(10**(math.floor(math.log10(x))+1)))



__unique_id_counter__: int = 0

def get_unique_id() -> int:
    global __unique_id_counter__
    __unique_id_counter__ += 1
    return __unique_id_counter__


def window_has_argument(window: str) -> bool:
    if window in ['dpss', 'exponential', 'general_gaussian', 'taylor']:
        raise RuntimeError(f'The window function "{window}" more than one argumentsy')
    if window in ['general_cosine', 'general_hamming', 'kaiser', 'kaiser_bessel_derived', 'tukey']:
        return True
    return False


def get_callstack_str(depth: int = 5) -> str:
    callstack = traceback.extract_stack()
    actual_depth = len(callstack) - 1  # remove the call to this function
    if actual_depth < 1:
        return 'Call: [empty callstack]'  # should never happen
    callstack_top = list(reversed(callstack[-depth-1:-1]))
    return 'Call: ' + ' < '.join([f'{s.name}()' for s in callstack_top]) + f' ({os.path.split(callstack_top[0].filename)[1]}#{callstack_top[0].lineno})'
