"""
Writing, loading, and opening files.
"""
import os
import subprocess
import platform


def file_load(file: os.PathLike):
    """Loads *file* and returns the contents as a string."""
    with open(file, 'r') as f:
        d = f.read()
    return d


def file_dump(file: os.PathLike, d: str, clear: bool = True):
    """Saves the string *d* to *file*. If *clear* is True, will overwrite the file, otherwise will append to it."""
    with open(file, 'w' if clear else 'a') as f:
        f.write(d)


def popen_path(path: os.PathLike):
    """Opens the given path using `subprocess.Popen`."""
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])
