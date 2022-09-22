"""Kex utilities."""

from typing import Optional, Literal, Any, Callable, Union
import time
import os
import sys
import random
import numpy as np
from . import kivy as kv


COLORS = {
    "black": (0.0, 0.0, 0.0),
    "grey": (0.5, 0.5, 0.5),
    "white": (1.0, 1.0, 1.0),
    "red": (0.6, 0.0, 0.1),
    "pink": (0.9, 0.3, 0.4),
    "yellow": (0.8, 0.7, 0.1),
    "orange": (0.7, 0.4, 0.0),
    "lime": (0.1, 0.4, 0.0),
    "green": (0.4, 0.7, 0.1),
    "cyan": (0.1, 0.7, 0.7),
    "blue": (0.1, 0.4, 0.9),
    "navy": (0.0, 0.1, 0.5),
    "violet": (0.7, 0.1, 0.9),
    "purple": (0.4, 0.0, 0.7),
    "magenta": (0.7, 0.0, 0.5),
}
ColorName = Literal[
    "black",
    "grey",
    "white",
    "red",
    "pink",
    "yellow",
    "orange",
    "lime",
    "green",
    "cyan",
    "blue",
    "navy",
    "violet",
    "purple",
    "magenta",
]
ColorType = tuple[float, float, float, float]


class XColor:
    """A class to represent a color."""

    def __init__(
        self,
        r: float = 0,
        g: float = 0,
        b: float = 0,
        a: float = 1,
        v: float = 1,
    ):
        """Initialize the class."""
        r, g, b = r * v, g * v, b * v
        self.__rgba = r, g, b, a

    @classmethod
    def from_name(cls, name: ColorName, v: float = 1, a: float = 1) -> "XColor":
        """Return a `XColor` from color name."""
        color = [c * v for c in COLORS[name]]
        return cls(*color, a)

    @classmethod
    def from_random(cls, v: float = 1, a: float = 1) -> "XColor":
        """Get a new `XColor` with random values."""
        color = np.array([random.random() for _ in range(3)]) * v
        return cls(*color, a)

    def alternate_color(self, drift: float = 0.5) -> "XColor":
        """Return a color that is offset from us by *drift* amount."""
        alt_rgb = [(c + drift) % 1 for c in self.rgb]
        return self.__class__(*alt_rgb, self.a)

    @property
    def r(self):
        """The red component."""
        return self.__rgba[0]

    @property
    def g(self):
        """The green component."""
        return self.__rgba[1]

    @property
    def b(self):
        """The blue component."""
        return self.__rgba[2]

    @property
    def a(self):
        """The alpha component."""
        return self.__rgba[3]

    @property
    def rgb(self):
        """The red, green, and blue components."""
        return self.__rgba[:3]

    @property
    def rgba(self):
        """The red, green, blue, and alpha components."""
        return self.__rgba


class XWindow:
    @classmethod
    def maximize(cls, *args):
        kv.Window.maximize()

    @classmethod
    def set_size(cls, x: float, y: float):
        """Resize the window while maintaining it's center position."""
        oldx, oldy = kv.Window.size
        top, left = kv.Window.top, kv.Window.left
        bot, right = top + oldy, left + oldx
        center = np.asarray([(top + bot) / 2, (left + right) / 2])
        center_offset = np.asarray([y, x]) / 2
        new_top_left = tuple(int(_) for _ in (center - center_offset))
        kv.Window.size = x, y
        kv.Window.top, kv.Window.left = new_top_left

    @classmethod
    def toggle_fullscreen(cls, set_to: Optional[bool] = None):
        """Toggle window fullscreen."""
        set_to = not kv.Window.fullscreen if set_to is None else set_to
        kv.Window.fullscreen = set_to

    @classmethod
    def set_position(cls, x: float, y: float):
        """Reposition the window's top left position."""
        kv.Window.left, kv.Window.top = x, y

    @staticmethod
    def enable_escape_exit(set_to: bool = True):
        """Toggles using the escape key to exit the program."""
        kv.Config.set("kivy", "exit_on_escape", str(int(set_to)))

    @staticmethod
    def disable_multitouch():
        """Toggles multitouch."""
        kv.Config.set("input", "mouse", "mouse,disable_multitouch")

    @staticmethod
    def enable_resize(set_to: bool):
        """Toggles ability to resize the window."""
        kv.Config.set("graphics", "resizable", str(int(set_to)))


class XWidget:
    def add(
        self,
        *children: tuple[kv.Widget, ...],
        insert_last: bool = False,
        **kwargs,
    ) -> kv.Widget:
        """Replacement for kivy's `add_widget` method.

        Args:
            children: Children to be added to the widget.
            insert_last: If children should be added below all other children.
                Overwrites the "index" argument from kwargs.
            kwargs: Keyword arguments for kivy's `add_widget`.

        Returns:
            The *child* widget.
        """
        if not children:
            raise ValueError("Must supply children to add.")
        if insert_last:
            kwargs["index"] = len(self.children)
        for child in children:
            self.add_widget(child, **kwargs)
        return children[0]

    def set_size(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        hx: float = 1,
        hy: float = 1,
    ) -> kv.Widget:
        """Set the size of the widget and returns the widget itself.

        Designed to produce intuitive results when not all values are passed.
        """
        hx = hx if x is None else None
        hy = hy if y is None else None
        x = self.width if x is None else x
        y = self.height if y is None else y
        self.size_hint = hx, hy
        self.size = int(x), int(y)
        return self

    def set_position(self, x: float, y: float) -> kv.Widget:
        """Set the position of the widget and returns the widget itself."""
        self.pos = int(x), int(y)
        return self

    def set_focus(self, delay=0, debug=False):
        """Set to focus on this widget."""
        if delay:
            kv.Clock.schedule_once(lambda dt: self._do_set_focus(debug=debug), delay)
        else:
            self._do_set_focus(debug=debug)

    def _do_set_focus(self, *args, debug=False):
        self.focus = True
        if debug:
            kv.Clock.schedule_once(
                lambda dt: print(f"{self} got focus. {self.app.current_focus=}"),
                0.05,
            )

    def make_bg(self, color: Optional[XColor] = None, source: Optional[str] = None):
        """Add or update an image below the widget."""
        self._set_image("_bg", color, source)

    def make_fg(self, color: Optional[XColor] = None, source: Optional[str] = None):
        """Add or update an image on top of the widget."""
        self._set_image("_fg", color, source)

    def _get_image(
        self,
        attribute_name: Literal["_bg", "_fg"],
    ) -> Union[tuple[kv.Rectangle, kv.Color], tuple[None, None]]:
        """Get the background/foreground of the widget."""
        attribute_name_color = f"{attribute_name}_color"
        if not hasattr(self, attribute_name) or not hasattr(self, attribute_name_color):
            return None, None
        image = getattr(self, attribute_name)
        color = getattr(self, attribute_name_color)
        assert isinstance(image, kv.Rectangle)
        assert isinstance(color, kv.Color)
        return image, color

    def _set_image(
        self,
        attribute_name: Literal["_bg", "_fg"],
        color: Optional[XColor],
        source: Optional[str],
    ):
        """Set the background/foreground of the widget."""
        is_bg = attribute_name == "_bg"
        if color is None:
            color = XColor(0.1, 0.1, 0.1, 1) if is_bg else XColor(1, 1, 1, 1)
        image, color_instruction = self._get_image(attribute_name)
        if image:
            color_instruction.rgba = color.rgba
            image.source = source
        else:
            canvas = self.canvas.before if is_bg else self.canvas.after
            with canvas:
                color_instruction = kv.Color(*color.rgba)
                image = kv.Rectangle(size=self.size, pos=self.pos, source=source)
            setattr(self, f"{attribute_name}_color", color_instruction)
            setattr(self, attribute_name, image)
            update_func = self._update_bg if is_bg else self._update_fg
            self.bind(pos=update_func, size=update_func)

    def _update_bg(self, *args):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _update_fg(self, *args):
        self._fg.pos = self.pos
        self._fg.size = self.size

    @property
    def app(self):
        return kv.App.get_running_app()


get_color = XColor.from_name
random_color = XColor.from_random


def center_sprite(
    pos: tuple[float, float],
    size: tuple[float, float],
) -> tuple[int, int]:
    """Find the offset required to center something of *size* on *pos*.

    Given the center position *pos* and a size of *size*, return the position
    of the bottom left corner.

    Args:
        pos: Position to center on.
        size: Size of object.

    Returns:
        Position of bottom left corner.
    """
    assert len(pos) == 2 and len(size) == 2
    return int(pos[0] - (size[0] / 2)), int(pos[1] - (size[1] / 2))


def text_texture(text, **kwargs):
    """Create a label texture using kivy.core.Label."""
    label = kv.CoreLabel(text=text, **kwargs)
    label.refresh()
    return label.texture


def restart_script(*args, **kwargs):
    """Restart the Python script. Ignores all arguments."""
    os.execl(sys.executable, sys.executable, *sys.argv)


def consume_args(*args, **kwargs):
    """Empty function that will consume all arguments passed to it."""
    pass


def placeholder(
    *wrapper_args,
    verbose: bool = False,
    returns: Any = None,
    **wrapper_kwargs,
) -> Callable[[Any], Any]:
    """Create a placeholder function that can consume all arguments passed to it."""

    def placeholder_inner(*args, **kwargs):
        if verbose:
            print(
                "\n".join(
                    [
                        f"Placeholder function called: {wrapper_args}{wrapper_kwargs}",
                        f"  {args=}",
                        f"  {kwargs=}",
                    ]
                )
            )
        else:
            print("Placeholder function", end="")
            print(f": {wrapper_args}{wrapper_kwargs}" if args else " called.")
        return returns

    return placeholder_inner


def ping():
    return time.time() * 1000


def pong(ping_):
    return time.time() * 1000 - ping_


schedule_once = kv.Clock.schedule_once
schedule_interval = kv.Clock.schedule_interval


Window = XWindow
Widget = XWidget
__all__ = [
    "Window",
    "Widget",
    "XColor",
    "get_color",
    "random_color",
    "center_sprite",
    "text_texture",
    "restart_script",
    "consume_args",
    "placeholder",
    "schedule_once",
    "schedule_interval",
]
