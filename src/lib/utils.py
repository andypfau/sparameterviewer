from .path_ext import PathExt
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
from typing import Callable



_rex_filetypes = re.compile(r'^\.((s[0-9]+p)|(ci?ti))$', re.IGNORECASE)
_rex_archtypes = re.compile(r'^\.zip$', re.IGNORECASE)


def is_ext_supported_file(ext: str) -> bool:
    return _rex_filetypes.match(ext)


def is_ext_supported_archive(ext: str) -> bool:
    return _rex_archtypes.match(ext)


def is_ext_supported(ext: str) -> bool:
    return _rex_filetypes.match(ext) or _rex_archtypes.match(ext)


def find_files_in_archive(path: str) -> list[PathExt]:
    result = []
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            for internal_name in zf.namelist():
                ext = os.path.splitext(internal_name)[1]
                if is_ext_supported_file(ext):
                    result.append(PathExt(path, arch_path=internal_name))
    except Exception as ex:
        logging.warning(f'Unable to open zip file <{path}>: {ex}')
    return result


def load_file_from_archive(archive_path: str, path_in_archive: str, target_path: str = None) -> str:
    """ Extracts a file from an archive, returns the path of the extracted file """
    with zipfile.ZipFile(archive_path, 'r') as zf:
        return zf.extract(path_in_archive, target_path)


class ArchiveFileLoader:
    """
    Usage:
        with ArchiveFileLoader('/path/arch.zip', 'file.ext') as extracted_path:
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


def p2db(p):
    return 10*np.log10(np.maximum(1e-30, np.abs(p)))


def v2db(v):
    return 20*np.log10(np.maximum(1e-15, np.abs(v)))


def db2v(db):
    return 10**(db/20)


def db2p(db):
    return 10**(db/20)


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



def get_next_1_2_5_10(x: int, nice_minutes: bool = False) -> int:
    """ Returns the next in the series (1, 2, 5, 10, 20, 50, 100, ...)"""
    
    def _get_next(x: int) -> int:
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
        
    if nice_minutes:
        x1 = _get_next(x)
        if x1 < 100:
            return x1
        elif x1 == 100:
            return 120
        else:
            return 60*_get_next(x//60)
    else:
        return _get_next(x)




def get_next_1_3_10(x: int, nice_minutes: bool = False) -> int:
    """ Returns the next in the series (1, 3, 10, 30, 100, ...)"""

    def _get_next(x: int) -> int:
        EPSILON = 0.99
        if x < 1:
            return 1
        f, i = math.modf(math.log10(x))
        if f < math.log10(3) * EPSILON:
            return 3*int(round(10**i))
        else:
            return int(round(10**(i+1)))

    if nice_minutes:
        x1 = _get_next(x)
        if x1 < 100:
            return x1
        elif x1 == 100:
            return 120
        else:
            return 60*_get_next(x//60)
    else:
        return _get_next(x)



def get_next_1_10_100(x: int, nice_minutes: bool = False) -> int:
    """ Returns the next in the series (1, 10, 100, 1000, ...)"""

    def _get_next(x: int) -> int:
        if x < 1:
            return 1
        return int(round(10**(math.floor(math.log10(x))+1)))
    
    if nice_minutes:
        x1 = _get_next(x)
        if x1 < 100:
            return x1
        elif x1 == 100:
            return 120
        else:
            return 60*_get_next(x//60)
    else:
        return _get_next(x)




__unique_id_counter__: int = 0

def get_unique_id() -> int:
    global __unique_id_counter__
    __unique_id_counter__ += 1
    return __unique_id_counter__


def window_has_argument(window: str) -> bool:
    if window in ['dpss', 'exponential', 'general_gaussian', 'taylor', 'dpss']:
        raise RuntimeError(f'The window function "{window}" more than one argument')
    if window in ['general_cosine', 'general_hamming', 'kaiser', 'kaiser_bessel_derived', 'tukey', 'gaussian', 'chebwin']:
        return True
    return False


def get_callstack_str(depth: int = 5) -> str:
    callstack = traceback.extract_stack()
    actual_depth = len(callstack) - 1  # remove the call to this function
    if actual_depth < 1:
        return 'Call: [empty callstack]'  # should never happen
    callstack_top = list(reversed(callstack[-depth-1:-1]))
    return 'Call: ' + ' < '.join([f'{s.name}()' for s in callstack_top]) + f' ({os.path.split(callstack_top[0].filename)[1]}#{callstack_top[0].lineno})'


def any_common_elements(a, b) -> bool:
    return len(set(a) & set(b)) > 0


def format_minute_seconds(secs: float) -> str:
    if isinstance(secs, float):
        if secs < 1:
            return f'{secs:.2f} s'
        if secs < 3:
            return f'{secs:.1f} s'

    if secs < 60:
        return f'{secs:.0f} s'

    int_secs = int(secs)
    return f'{int_secs//60}:{int_secs%60:02}'


def string_to_enum(s: str, lut: dict):
    for value, name in lut.items():
        if name == s:
            return value
    raise ValueError(f'String "{s}" not in LUT <{lut}>')


def enum_to_string(value, lut: dict):
    if value not in lut:
        raise ValueError(f'Value <{value}> not in LUT <{lut}>')
    return lut[value]


def choose_smart_db_scale(all_db_values: list[np.ndarray]) -> tuple[float,float]:

    QUANT_FOOT, QUANT_MIDDLE, QUANT_HEAD = 0.25, 0.5, 0.67
    LONG_TAIL_HEAD_POS_PERCENT = 80
    MAX_LONGTAIL_RANGE_DB = 80
    MIN_RANGE_DB = 15
    ZERO_EXTENSION_FACTOR = 2.0

    def nice_range(bottom, top):
        assert top >= bottom, f'Expected hi>lo, got {top} and {bottom}'
        range = top - bottom
        if range == 0:
            return bottom-1, top+1
        if range > 100:
            scale, margin = 10, 1
        elif range > 50:
            scale, margin = 5, 1
        elif range > 20:
            scale, margin = 2, 1
        elif range > 2:
            scale, margin = 1, 0.5
        elif range > 0.5:
            scale, margin = 0.2, 0.1
        elif range > 0.2:
            scale, margin = 0.1, 0.05
        else:
            scale, margin = 0.02, 0.01
        nice_bottom = math.floor(bottom / scale) * scale - margin
        nice_top = math.ceil(top / scale) * scale + margin
        return nice_bottom, nice_top

    # go over each trace, find out how to scale each one of them
    top, base, bottom = -1e99, +1e99, +1e99
    for db_values in all_db_values:
        this_top = np.max(db_values)
        (this_foot,this_middle,this_head) = np.quantile(db_values, [QUANT_FOOT, QUANT_MIDDLE, QUANT_HEAD])
        this_bottom = np.min(db_values)
        this_height = this_top - this_bottom
        head_pos = (this_head-this_bottom)/this_height
        
        top = max(top, this_top)
        bottom = min(bottom, this_bottom)
        has_long_tail = head_pos >= LONG_TAIL_HEAD_POS_PERCENT/100
        if has_long_tail:
            # baseline lies very high, which may look like having a "long tail" (like many return-loss traces do) -> scale to base to hide the tail
            if this_foot < this_top - MAX_LONGTAIL_RANGE_DB:
                this_base = this_top - MAX_LONGTAIL_RANGE_DB  # do not show excessively much
            else:
                this_base = this_foot
            base = min(base, this_base)
        else:
            # baseline is not particularly high, which may look like a "flat" trace -> use the bottom
            base = min(base, this_bottom)
    
    full_height = top - bottom
    if full_height < MIN_RANGE_DB:
        # range is small anyway, just show the whole thing
        return False, *nice_range(bottom, top)

    # attempt to apply a smarter range by using the estimated "base", not the actual minimum value
    bottom = base
    full_height = top - bottom

    if top < 0:
        height_with_zero = 0 - bottom
        if height_with_zero <= ZERO_EXTENSION_FACTOR*full_height:
            # increasing the top a little bit would show the zero-line -> include the zero-line
            top = 0
            full_height = top - bottom
    elif bottom > 0:
        height_with_zero = top - 0
        if height_with_zero <= ZERO_EXTENSION_FACTOR*full_height:
            # decreasing the bottom little bit would show the zero-line -> include the zero-line
            bottom = 0
            full_height = top - bottom

    return True, *nice_range(bottom, top)


def get_subset(arr, n: int):
    """
    Returns a subset of a list; examples:
        `get_subset([1,2,3,4,5], 1)` -> `[3]` (the middle item)
        `get_subset([1,2,3,4,5], 2)` -> `[0,4]` (1st and last item)
        `get_subset([1,2,3,4,5], 3)` -> `[0,2,4]` (three equidistant items)
        `get_subset([1,2,3,4,5], 99)` -> `[0,1,2,3,4]` (all items)
    """
    n_all = len(arr)
    if n <= 0:
        return []  # zero items
    elif n == 1:
        return [arr[round(n_all/2)]]  # the middle item
    elif n < n_all:
        return [arr[max(0,min(n_all-1,round((n_all-1)*i/(n-1))))] for i in range(n)]  # equidistant samples
    else:
        return arr  # all items


def strip_common(str_or_lines: str|list[str]) -> str|list[str]:
    if isinstance(str_or_lines, str):
        return '\n'.join(strip_common(str_or_lines.splitlines()))
    
    max_header = 999999
    for line in str_or_lines:
        m = re.match(r'^(\s+).*', line)
        if m:
            max_header = max(max_header, len(m.group(1)))
    
    return list([line[:max_header] for line in str_or_lines])


def factorize_int(number: int) -> list[int]:
    if number < 1:
        raise ValueError(f'Cannot factor a number less than one')
    if number == 1:
        return [1]

    factors: list[int] = []
    
    while number % 2 == 0:
        factors.append(2)
        number //= 2
        
    i = 3
    max_factor = int(math.sqrt(number)) + 1
    while i <= max_factor and number > 1:
        while number % i == 0:
            factors.append(i)
            number //= i
            max_factor = int(math.sqrt(number)) + 1
        i += 2
    
    if number > 1:
        factors.append(number)
        
    return factors


def find_optimum_grid(i: int) -> tuple[int,int]:
    """"
    Finds the optimum grid for a given number.
    The optimum grid is defined as having the minimum circumference,
      and as close to a square as possible.

    Examples:
        - 8 -> (3,3)  (could also be e.g. 2x4 or 1x8, but that would not be very square)
        - 9 -> (3,3)  (perfect square)
    """
    # TODO: for 5 it returns 3x3 instead of 2x3... I think I should also weight in the wasted cells somehow

    assert i >= 1
    root = int(math.ceil(math.sqrt(i)))
    solutions = []
    for x in range(root, 0, -1):
        if x*x == i:
            return x, x  # perfect square
        if x*x >= i:
            solutions.append((x, x))
        y = i // x
        if x*y >= i:
            solutions.append((x, y))
    assert len(solutions) >= 1
    
    def rectangle_circumference(solution):
        return 2*solution[0] + 2*solution[1]
    def aspect_ratio(solution):
        return solution[0]/solution[1]
    
    lowest_circumference = min([rectangle_circumference(s) for s in solutions])
    solutions = [s for s in solutions if rectangle_circumference(s)==lowest_circumference]

    return sorted(solutions, key=lambda s: abs(aspect_ratio(s)-1))[0]


def file_pattern_to_regex(pattern: str) -> str:
    sep = os.sep
    if sep == '\\':
       sep = '\\\\'
    tokens = re.split(r'([*?]+)', pattern)
    result = []
    for token in tokens:
        if '?' in token or '*' in token:
            if token == '?':
                result.append('.')
            elif token == '*':
                result.append(f'[^{sep}]*')
            elif token == '**':
                result.append(f'.*')
            else:
                raise ValueError(f'Invalid token "{token}" in pattern "{pattern}". Only "*", "**", and "?" are allowed as wildcard tokens.')
        else:
            result.append(re.escape(token))
    return ''.join(result) + '$'


def make_filename_matcher(pattern: str) -> Callable[tuple[PathExt],bool]:
    
    regex = file_pattern_to_regex(pattern)
    
    def match_full_path(path: PathExt) -> bool:
        match = re.match(regex, path.full_path, re.I)
        if match is None:
            return False
        if match.group(0).endswith(os.path.basename(path)):  # make sure we also matched the filename itself
            return True
        return False
    
    def match_name_only(path: PathExt) -> bool:
        return bool(re.match(regex, path.final_name, re.I) is not None)
    
    if os.sep in pattern:
        return match_full_path
    else:
        return match_name_only


def is_valid_binary(path: str) -> bool:
    if not path:
        return False
    if not os.path.exists(path):
        return False
    if not os.path.isfile(path):
        return False
    if not os.access(path, os.X_OK):
        return False
    return True


def find_default_editor() -> str|None:
    if is_windows():
        common_paths = [
            '%ProgramFiles%/Notepad++/notepad++.exe',
            '%ProgramFiles(x86)%/Notepad++/notepad++.exe',
            '%ProgramFiles%/Microsoft VS Code/bin/code.cmd',
            '%LocalAppData%/Programs/Microsoft VS Code/bin/code.cmd',
            '%SystemRoot%/System32/notepad.exe',
        ]
    else:
        common_paths = [
            '/usr/bin/code',
            '/snap/bin/code',
            '/usr/bin/geany',
            '/usr/bin/gedit',
            '/usr/bin/vim',
        ]

    for path in common_paths:
        if is_valid_binary(path):
            return path
    return None
