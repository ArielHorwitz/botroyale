"""Common independent functions and values."""
from os import PathLike
import argparse
from pathlib import Path


PROJ_DIR: PathLike = Path(__file__).parent.parent.parent
"""The project directory root."""
PACKAGE_DIR: PathLike = PROJ_DIR / "botroyale"
"""The source code directory root."""
INSTALLED_FROM_SOURCE: bool = (PROJ_DIR / "pyproject.toml").is_file()
"""If the package is installed from source code (as opposed to packaged wheel)."""

# Sanity checks
assert PROJ_DIR.is_dir()
assert PACKAGE_DIR.is_dir()
assert (PACKAGE_DIR / "__init__.py").is_file()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
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
