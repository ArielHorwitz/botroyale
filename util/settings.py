from pathlib import Path
import json
from util import file_load, file_dump


CLEAR_SETTINGS = (Path.cwd() / '.deletesettings').is_file()
SETTINGS_FILE = Path.cwd() / 'settings.json'


class Settings:
    if CLEAR_SETTINGS and SETTINGS_FILE.is_file():
        SETTINGS_FILE.unlink()
    if SETTINGS_FILE.is_file():
        s = file_load(SETTINGS_FILE)
        user_settings = json.loads(s)
    else:
        user_settings = {}
    default_settings = {}

    @classmethod
    def get(cls, name, set_default=None):
        if set_default is not None:
            if name in cls.default_settings:
                raise KeyError(f'Setting "{name}" default already set to: {cls.default_settings[name]}')
            cls.default_settings[name] = set_default
        if name in cls.user_settings:
            return cls.user_settings[name]
        return cls.default_settings[name]

    @classmethod
    def write_to_file(cls):
        all_settings = cls.default_settings | cls.user_settings
        for name in list(all_settings.keys()):
            if name not in cls.default_settings:
                del all_settings[name]
        file_dump(SETTINGS_FILE, json.dumps(all_settings, indent=4))
