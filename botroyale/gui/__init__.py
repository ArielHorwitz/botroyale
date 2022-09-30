"""GUI application for Bot Royale.

This package is documented mostly for posterity and is not directly used by bot
developers. For interfacing with the GUI, see: `botroyale.api.gui`.

For custom use cases:
```python
# Import this as late as possible since this opens up a window on desktop
from botroyale.gui.app import App

app = App(game_api=MyGameAPI())
app.run()
```

The GUI uses the `kex` custom library (a [Kivy](https://kivy.org) Extention).
Due to a quirk of Kivy, importing submodules of this package may open up a
window on the desktop (see [GitHub](https://github.com/kivy/kivy/issues/7742)
and [StackOverflow](
https://stackoverflow.com/questions/67345686/when-importing-a-kivymd-module-in-a-python-script-a-blank-window-appears
)).
"""
from botroyale.api.logging import logger as glogger
from botroyale.util import PACKAGE_DIR, settings


ASSETS_DIR = PACKAGE_DIR / "assets"
GUI_DEBUG = settings.get("logging.gui")
HOTKEY_DEBUG = settings.get("logging.hotkeys")


def register_controls(im, controls):
    """Register the hotkeys in a list of Controls to an InputManager.

    See: `botroyale.gui.kex.widgets.input_manager.XInputManager`
    """
    im.remove_all()
    for c in controls:
        if not c.hotkeys:
            continue
        action = f"{c.category}.{c.label}"
        im.register(action, c.callback, c.hotkeys)


def logger(message: str):
    """Log *message* in the GUI logger."""
    if GUI_DEBUG:
        glogger(message)


def hotkey_logger(message: str):
    """Log *message* in the GUI hotkey logger."""
    if HOTKEY_DEBUG:
        glogger(message)
