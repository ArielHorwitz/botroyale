"""
Common independent functions and values.
"""
from os import PathLike
from pathlib import Path


TITLE: str = 'Bot Royale'
"""Title of the program."""
VERSION: float = 1.000
"""Version number of the program."""
FULL_TITLE: str = f'{TITLE} v{VERSION:.3f}'
"""Title of the program with version."""
DESCRIPTION: str = 'A battle royale for bots.'
"""Short description of the program."""


PROJ_DIR = Path(__file__).parent.parent
"""The project directory root."""
assert PROJ_DIR.is_dir()
assert (PROJ_DIR / 'main.py').is_file()


def file_load(file: PathLike):
    """Use `util.file.file_load` instead.

    .. deprecated:: 1.000
    """
    with open(file, 'r') as f:
        d = f.read()
    return d


def file_dump(file: PathLike, d: str, clear: bool = True):
    """Use `util.file.file_dump` instead.

    .. deprecated:: 1.000
    """
    with open(file, 'w' if clear else 'a') as f:
        f.write(d)
