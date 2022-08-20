"""
Common independent functions and values.
"""
from os import PathLike
import argparse
from pathlib import Path
from util.file import file_load


PROJ_DIR = Path(__file__).parent.parent
"""The project directory root."""
assert PROJ_DIR.is_dir()
assert (PROJ_DIR / 'main.py').is_file()


VERSION = '1.0.0'
"""Version of the program (using semantic versioning)."""
TITLE: str = 'Bot Royale'
"""Title of the program."""
DESCRIPTION: str = 'A battle royale for bots.'
"""Short description of the program."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('module', metavar='MODULE',
        nargs='?', default='gui',
        help='name of module to run (default: gui)')
    parser.add_argument('opargs', metavar='OPARGS',
        nargs='*',
        help='optional arguments for script')
    parser.add_argument('--list',
        action='store_true',
        help='print available modules to run and exit')
    args = parser.parse_args()
    return args


MAIN_ARGS = args = _parse_args()
"""Arguments passed to the program when executed."""


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
