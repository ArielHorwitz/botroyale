"""Manages user settings.

Settings are configured using TOML. A built-in default config exists in the
package, and a user-defined custom config exists in the usr dir. User-defined
values take priority.
"""
from typing import Any
import copy
import shutil
import warnings
from botroyale.util import PACKAGE_DIR
from botroyale.util.file import file_load, file_dump, toml_loads, get_usr_dir


def _create_missing_files():
    if not SETTINGS_FILE.is_file():
        file_dump(SETTINGS_FILE, "")
    if not DEFAULTS_FILE_USR.is_file():
        shutil.copy(DEFAULTS_FILE, DEFAULTS_FILE_USR)


DEFAULTS_FILE = PACKAGE_DIR / "default_settings.toml"
DEFAULTS = toml_loads(file_load(DEFAULTS_FILE))
SETTINGS_DIR = get_usr_dir("settings")
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = SETTINGS_DIR / "settings.toml"
DEFAULTS_FILE_USR = SETTINGS_DIR / "defaults.toml"
_create_missing_files()


def _import_settings():
    """Import settings from usr dir, fill missing entries from defaults.

    Ignores entries that don't exist in defaults.
    """
    # Gather settings from user and defaults
    settings = copy.deepcopy(DEFAULTS)
    usr_settings = {}
    if SETTINGS_FILE.is_file():
        usr_settings = toml_loads(file_load(SETTINGS_FILE))
    # Find all keys
    default_paths = set(_yield_setting_paths(settings))
    usr_paths = set(_yield_setting_paths(usr_settings))
    # Ignore paths that are not in defaults
    ignored_paths = usr_paths - default_paths
    for path in ignored_paths:
        warnings.warn(f'Unkown setting "{path}" (not in defaults)')
    shared_paths = default_paths & usr_paths
    for path in shared_paths:
        usr_value = _resolve_setting(usr_settings, path)
        _set_setting(settings, path, usr_value)
    return settings


def _resolve_setting(data, key_path):
    d = data
    for part in key_path.split("."):
        if part not in d:
            raise KeyError(f'Unkown setting "{key_path}" (not in defaults)')
        d = d[part]
    return d


def _set_setting(data, key_path, value):
    d = data
    path_parts = key_path.split(".")
    for part in path_parts[:-1]:
        if part not in d:
            raise KeyError(f'Unkown setting "{key_path}"')
        d = d[part]
    d[path_parts[-1]] = value


def _yield_setting_paths(d, path=None):
    path = [] if path is None else path
    for k, v in d.items():
        assert isinstance(k, str)
        new_path = [*path, k]
        if isinstance(v, dict):
            yield from _yield_setting_paths(v, path=new_path)
        else:
            yield ".".join(new_path)


class __Settings:
    data = _import_settings()


def get(setting_name: str) -> Any:
    """Get the value of *setting_name*."""
    v = _resolve_setting(__Settings.data, setting_name)
    return v


def clear():
    """Revert all settings data to defaults."""
    if SETTINGS_FILE.is_file():
        SETTINGS_FILE.unlink()
    if DEFAULTS_FILE_USR.is_file():
        DEFAULTS_FILE_USR.unlink()
    _create_missing_files()
