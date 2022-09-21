# flake8: noqa

import sys
from pathlib import Path
from pkgutil import iter_modules
from importlib import import_module
from botroyale.util import PACKAGE_DIR
from setuptools import find_packages


def test_python_version():
    """Ensure that we are running the correct version of Python.

    For now, we test universally on the earliest supported version of Python.
    """
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 9


def test_imports():
    """Import every module found recusively in the botroyale package."""
    pkg_paths = []
    for pkg in find_packages(PACKAGE_DIR):
        path = PACKAGE_DIR
        for part in pkg.split("."):
            path /= part
        pkg_paths.append(path)

    for finder, name, ispkg in list(iter_modules(pkg_paths)):
        abs_path = Path(finder.path)
        rel_path = abs_path.relative_to(PACKAGE_DIR)
        path_parts = ["botroyale", *rel_path.parts]
        if not ispkg:
            path_parts.append(name)
        full_name = ".".join(path_parts)
        import_module(full_name)
