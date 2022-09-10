"""Common independent functions and values."""
from pathlib import Path


PROJ_DIR: Path = Path(__file__).parent.parent.parent
"""The project directory root."""
PACKAGE_DIR: Path = PROJ_DIR / "botroyale"
"""The source code directory root."""
INSTALLED_FROM_SOURCE: bool = (PROJ_DIR / "pyproject.toml").is_file()
"""If the package is installed from source code (as opposed to packaged wheel)."""

# Sanity checks
assert PROJ_DIR.is_dir()
assert PACKAGE_DIR.is_dir()
assert (PACKAGE_DIR / "__init__.py").is_file()
