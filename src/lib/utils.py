import os
import string
import subprocess
import numpy as np


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
        #print(f'{name}: cropping off {excess_end} at end')
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
        #print(f'{name}: cropping off {excess_start} at start')
        result = result[excess_start:]
    
    return result


def is_windows():
    return True if os.name=='nt' else False


def sanitize_filename(filename: str) -> str:
    VALID_CHARS = '+-_' + string.ascii_letters + string.digits
    sanitized = [char for char in filename if char in VALID_CHARS]
    return ''.join(sanitized)


def open_file_in_default_viewer(filename: str):
    if is_windows():
        os.startfile(filename)
    else:
        subprocess.run(['xdg-open', filename], check=True)


def start_process(binary_path: str, *args):
    subprocess.run([binary_path, *args])


def v2db(v):
    return 20*np.log10(np.maximum(1e-15, np.abs(v)))


def group_delay(frequencies, sparams):
    d_phase = np.diff(np.unwrap(np.angle(sparams)))
    d_freq = np.diff(frequencies)
    return frequencies[1:], -d_phase/d_freq
