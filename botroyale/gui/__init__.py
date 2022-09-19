"""GUI backend using the *kex* custom library, a [Kivy](https://kivy.org) Extention.

Due to a quirk of Kivy, importing submodules of this package will open up a
window on the desktop.
"""
from collections import defaultdict
from botroyale.api.logging import logger as glogger
from botroyale.util import PACKAGE_DIR
from botroyale.util import settings


GUI_DEBUG = settings.get("logging.gui")
HOTKEY_DEBUG = settings.get("logging.hotkeys")
ASSETS_DIR = PACKAGE_DIR / "assets"
DEFAULT_FONT_NAME = settings.get("gui.fonts.default")
FONT = str(ASSETS_DIR / "fonts" / f"{DEFAULT_FONT_NAME}.ttf")
FONT_SIZE = settings.get("gui.fonts.size")


def categorize_controls(controls, default_category="App", separator="."):
    """Organize a list of controls into a dictionary of categories of controls."""
    d = defaultdict(list)
    for control in controls:
        name, callback, key = control
        category = default_category
        if separator in name:
            category, name = name.split(separator, 1)
        d[category].append(control)
    return d


def im_register_controls(im, controls):
    """Register the hotkeys in a list of Controls to a kex.InputManager."""
    im.clear_all()
    for control, callback, key in controls:
        if key is None:
            continue
        im.register(control, key, callback=lambda *a, c=callback: c())


def logger(message: str):
    """Log *message* in the GUI logger."""
    if GUI_DEBUG:
        glogger(message)


def hotkey_logger(message: str):
    """Log *message* in the GUI hotkey logger."""
    if HOTKEY_DEBUG:
        glogger(message)
