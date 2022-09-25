"""Kex utilities."""

from typing import Optional, Literal, Any, Callable, Union
from functools import partial, wraps
import time
import os
import sys
import random
import numpy as np
from . import kivy as kv


SimpleCallable = Callable[[], None]

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
        """Initialize the class.

        Args:
            r: Red component.
            g: Green component.
            b: Blue component.
            a: Alpha component.
            v: Value multiplier (multiplies `rgb` values).
        """
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
        """Return a color that is offset from self by *drift* amount."""
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
    """Window controls."""

    @classmethod
    def maximize(cls, *args):
        """Maixmize the window."""
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
    """A mixin for kivy widgets with useful methods."""

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

    def set_focus(self, *args):
        """Set the focus on this widget."""
        self.focus = True

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
        """Get the running app."""
        return kv.App.get_running_app()

    def logger(self, message: str):
        """Log a message in the XApp's logger."""
        kv.App.logger(message)


get_color = XColor.from_name
random_color = XColor.from_random


def queue_around_frame(
    func,
    before: Optional[SimpleCallable] = None,
    after: Optional[SimpleCallable] = None,
):
    """Decorator for queuing functions before and after drawing frames.

    Used for performing GUI operations before and after functions that will
    block code execution for a significant period of time. Functions that would
    otherwise freeze the GUI without feedback can be wrapped with this decorator
    to give user feedback.

    The following order of operations will be queued:

    1. Call *before*
    2. Draw GUI frame
    3. Call the wrapped function
    4. Call *after*

    ### Example usage:
    ```python
    @queue(
        before=lambda: print("Drawing GUI frame then executing function..."),
        after=lambda: print("Done executing..."),
    )
    def do_sleep():
        time.sleep(2)
    ```
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if before is not None:
            before()
        wrapped = partial(func, *args, **kwargs)
        kv.Clock.schedule_once(lambda dt: _call_with_after(wrapped, after), 0.05)

    return wrapper


def _call_with_after(func: SimpleCallable, after: Optional[SimpleCallable] = None):
    func()
    if after is not None:
        # In order to schedule properly, we must tick or else all the time spent
        # calling func will be counted as time waited on kivy's clock schedule.
        kv.Clock.tick()
        kv.Clock.schedule_once(lambda dt: after(), 0.05)


def center_sprite(
    pos: tuple[float, float],
    size: tuple[float, float],
) -> tuple[int, int]:
    """Given *size* and center position *pos*, return the bottom left corner."""
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
        print(
            f"Placeholder function {wrapper_args}{wrapper_kwargs} : "
            f"{args}{kwargs} -> {returns=}"
        )
        return returns

    return placeholder_inner


def _ping():
    return time.time() * 1000


def _pong(ping_):
    return time.time() * 1000 - ping_


schedule_once = kv.Clock.schedule_once
schedule_interval = kv.Clock.schedule_interval


__pdoc__ = {
    "schedule_once": False,
    "schedule_interval": False,
}
