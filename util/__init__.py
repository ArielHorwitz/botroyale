"""
Common independent functions and values.
"""
from os import PathLike
from pathlib import Path


VERSION: str = 'v1.0.0'
"""Version of the program (using semantic versioning)."""
TITLE: str = 'Bot Royale'
"""Title of the program."""
DESCRIPTION: str = 'A battle royale for bots.'
"""Short description of the program."""


PROJ_DIR = Path(__file__).parent.parent
"""The project directory root."""
assert PROJ_DIR.is_dir()
assert (PROJ_DIR / 'main.py').is_file()


def file_load(file: PathLike):
    """Use `util.file.file_load` instead.

    .. deprecated:: v1.0
        `util.file_load` will be removed in v2.0. Please use `util.file.file_load`.
    """
    with open(file, 'r') as f:
        d = f.read()
    return d


def file_dump(file: PathLike, d: str, clear: bool = True):
    """Use `util.file.file_dump` instead.

    .. deprecated:: v1.0
        `util.file_dump` will be removed in v2.0. Please use `util.file.file_dump`.
    """
    with open(file, 'w' if clear else 'a') as f:
        f.write(d)
