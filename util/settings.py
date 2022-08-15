import json
from util import PROJ_DIR, file_load, file_dump


CLEAR_SETTINGS = (PROJ_DIR / '.deletesettings').is_file()
SETTINGS_FILE = PROJ_DIR / 'settings.json'


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
            cls.default_settings[name] = set_default
        if name in cls.user_settings:
            return cls.user_settings[name]
        elif name in cls.default_settings:
            return cls.default_settings[name]
        raise KeyError(f'No such setting "{name}" found')

    @classmethod
    def write_to_file(cls):
        all_settings = cls.default_settings | cls.user_settings
        for name in list(all_settings.keys()):
            if name not in cls.default_settings:
                del all_settings[name]
        sorted_settings = {k: all_settings[k] for k in sorted(all_settings.keys())}
        file_dump(SETTINGS_FILE, json.dumps(sorted_settings, indent=4))
