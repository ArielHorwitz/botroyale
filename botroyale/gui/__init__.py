"""GUI backend using the *kex* custom library, a [Kivy](https://kivy.org) Extention.

Due to a quirk of Kivy, importing submodules of this package will open up a
window on the desktop.
"""
from botroyale.api.logging import logger as glogger
from botroyale.util import PACKAGE_DIR, settings


ASSETS_DIR = PACKAGE_DIR / "assets"
GUI_DEBUG = settings.get("logging.gui")
HOTKEY_DEBUG = settings.get("logging.hotkeys")


def im_register_controls(im, controls):
    """Register the hotkeys in a list of Controls to a kex.InputManager."""
    im.clear_all()
    for c in controls:
        if c.hotkey is None:
            continue
        action = f"{c.category}.{c.label}"
        im.register(action, c.hotkey, c.callback)


def logger(message: str):
    """Log *message* in the GUI logger."""
    if GUI_DEBUG:
        glogger(message)


def hotkey_logger(message: str):
    """Log *message* in the GUI hotkey logger."""
    if HOTKEY_DEBUG:
        glogger(message)
