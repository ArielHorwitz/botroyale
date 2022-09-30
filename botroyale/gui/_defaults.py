"""A module containing defaults for Kex widgets.

Used internally for resolving color schemes and other arguments for widgets.
"""
from typing import NamedTuple
from botroyale.util import settings
from botroyale.gui import kex as kx, ASSETS_DIR


# Fonts
FONT_NAME = settings.get("gui.font")
FONT_NAME_MONO = settings.get("gui.font_mono")
FONT_SIZE = settings.get("gui.font_size")
FONT = str(ASSETS_DIR / "fonts" / f"{FONT_NAME}.ttf")
FONT_MONO = str(ASSETS_DIR / "fonts" / f"{FONT_NAME_MONO}.ttf")


# Colors
class ColorScheme(NamedTuple):
    """A color scheme."""

    bg: kx.XColor
    fg: kx.XColor


USER_COLORS = settings.get("gui.colors")
BLACK = kx.get_color("black")
GREY = kx.get_color("grey")
WHITE = kx.get_color("white")
PALETTE = tuple(kx.XColor(*c) for c in settings.get("gui.palette"))
PALETTE_BG = tuple(kx.XColor(*c.rgba, v=0.3) for c in PALETTE)
FULL_PALETTE = tuple(list(PALETTE) + list(PALETTE_BG) + [WHITE, GREY, BLACK])


def _get_user_color(name):
    color = USER_COLORS[name]
    return ColorScheme(
        FULL_PALETTE[color[0]],
        FULL_PALETTE[color[1]],
    )


COLORS = {name: _get_user_color(name) for name in USER_COLORS}
TEXT_COLOR = COLORS["default"].fg


# Text
LINE_HEIGHT = settings.get("gui.line_height")
TEXT = {
    "font_size": FONT_SIZE,
    "font_name": FONT,
    "color": TEXT_COLOR.rgba,
}
TEXT_MONO = TEXT | {"font_name": FONT_MONO}


# Widgets
BUTTON = {
    **TEXT,
    "background_normal": str(ASSETS_DIR / "sprites" / "button_normal.png"),
    "background_down": str(ASSETS_DIR / "sprites" / "button_down.png"),
    "background_color": COLORS["button"].bg.rgba,
    "color": COLORS["button"].fg.rgba,
}
BUTTON_AUX = BUTTON | {
    "background_color": COLORS["button_aux"].bg.rgba,
    "color": COLORS["button_aux"].fg.rgba,
}
BUTTON_LIGHT = BUTTON | {
    "background_color": COLORS["button_light"].bg.rgba,
    "color": COLORS["button_light"].fg.rgba,
}
