"""Common independent functions and values."""
from os import PathLike
import argparse
from pathlib import Path
from botroyale.util.file import file_load


PROJ_DIR: PathLike = Path(__file__).parent.parent.parent
"""The project directory root."""
PACKAGE_DIR: PathLike = PROJ_DIR / "botroyale"
"""The source code directory root."""
assert PROJ_DIR.is_dir()
assert PACKAGE_DIR.is_dir()


VERSION: str = file_load(PROJ_DIR / "VERSION").strip()
"""Version of the program (using semantic versioning: https://semver.org/)."""
TITLE: str = "Bot Royale"
"""Title of the program."""
DESCRIPTION: str = "A battle royale for bots."
"""Short description of the program."""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument(
        "module",
        metavar="MODULE",
        nargs="?",
        default="gui",
        help="name of module to run (default: gui)",
    )
    parser.add_argument(
        "opargs", metavar="OPARGS", nargs="*", help="optional arguments for script"
    )
    parser.add_argument(
        "--list", action="store_true", help="print available modules to run and exit"
    )
    args = parser.parse_args()
    return args


MAIN_ARGS = args = _parse_args()
"""Arguments passed to the program when executed."""
