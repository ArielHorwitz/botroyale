"""Manages user settings.

The settings file is located at `botroyale.util.PACKAGE_DIR` as *settings.json*.

To restore a setting to it's default value, simply delete the line from the
settings file. To restore all settings to defaults, simply delete the settings
file.

If the file *.deletesettings* is found at `botroyale.util.PACKAGE_DIR`, the
settings file will be deleted at the start of every execution.
"""
from typing import Any
import json
from botroyale.util import PACKAGE_DIR
from botroyale.util.file import file_load, file_dump


CLEAR_SETTINGS = (PACKAGE_DIR / ".deletesettings").is_file()
SETTINGS_FILE = PACKAGE_DIR / "settings.json"


class Settings:
    """Settings manager class.

    .. todo:: Remove `Settings` class and use functions and module-level variables.
    """

    _user_settings = {}
    if CLEAR_SETTINGS and SETTINGS_FILE.is_file():
        SETTINGS_FILE.unlink()
    if SETTINGS_FILE.is_file():
        _s = file_load(SETTINGS_FILE)
        _user_settings = json.loads(_s)
    _default_settings = {}

    @classmethod
    def get(cls, name: str, default: Any) -> Any:
        """Get the value of a setting (user configured or default value).

        Args:
            name: Name of setting (json key).
            default: The default value if not configured by the user.

        Return:
            The value of the setting (json value).
        """
        if default is not None:
            cls._default_settings[name] = default
        if name in cls._user_settings:
            return cls._user_settings[name]
        elif name in cls._default_settings:
            return cls._default_settings[name]
        raise KeyError(f'No such setting "{name}" found')

    @classmethod
    def write_to_file(cls):
        """Write the settings to file.

        Will remove entries without defaults (as registered with `Settings.get`).
        """
        all_settings = cls._default_settings | cls._user_settings
        for name in list(all_settings.keys()):
            if name not in cls._default_settings:
                del all_settings[name]
        sorted_settings = {k: all_settings[k] for k in sorted(all_settings.keys())}
        file_dump(SETTINGS_FILE, json.dumps(sorted_settings, indent=4))


get = Settings.get
save_settings = Settings.write_to_file
