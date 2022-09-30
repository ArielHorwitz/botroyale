"""App and associated widgets.

Generally, to use the GUI, one would initialize and then run an `App`:
```python
app = XApp()
app.hook(func_to_call_every_frame, fps=20)
app.run()
```
"""
from typing import Callable, Optional
from functools import partial
from .. import kivy as kv
from ..util import (
    XColor,
    XWindow,
    XWidget,
    consume_args,
    SimpleCallable,
    queue_around_frame,
)
from .layouts import XAnchor
from .uix import XLabel


class XOverlay(kv.FocusBehavior, XAnchor):
    """Overlay to be displayed on top of other widgets."""

    def __init__(self, **kwargs):
        """Initialize like an XAnchor."""
        super().__init__()
        self.make_bg(XColor(a=0.5))
        self.label = self.add(XLabel(**kwargs))
        self.label.set_size(x=500, y=150)
        self.label.make_bg(XColor.from_name("red", 0.15))


class XRoot(kv.FocusBehavior, XAnchor):
    """Root widget for the app, with FocusBehavior."""

    pass


class XApp(XWidget, kv.App):
    """See module documentation for details."""

    block_input = kv.BooleanProperty(False)
    """If all user input should be blocked."""

    def __init__(
        self,
        logger: Optional[Callable[[str], None]] = None,
        escape_exits: bool = False,
        enable_multitouch: bool = False,
        **kwargs,
    ):
        """Initialize the class.

        Args:
            logger: Logging function for XWidgets. Used internally for debugging.
            escape_exits: Enable exiting when the escape key is pressed.
            enable_multitouch: Enable multitouch.
        """
        super().__init__(**kwargs)
        XWindow.enable_escape_exit(escape_exits)
        self.root = XRoot()
        self.keyboard = kv.Window.request_keyboard(consume_args, self.root)
        self.__last_focused = None
        self.__overlay = None
        self.__enable_multitouch = enable_multitouch
        if not enable_multitouch:
            XWindow.disable_multitouch()
        self.root.bind(
            on_touch_down=self._is_touch_blocked,
            on_touch_up=self._is_touch_blocked,
            on_touch_move=self._is_touch_blocked,
        )

    def logger(self, message: str):
        """Log a message in the app's logger."""
        if self.logger:
            self.logger(message)

    def hook(self, func: Callable[[float], None], fps: float):
        """Schedule *func* to be called *fps* times per seconds."""
        kv.Clock.schedule_once(
            lambda *a: kv.Clock.schedule_interval(func, 1 / fps),
            0,
        )

    def open_settings(self, *args) -> False:
        """Overrides base class method to disable the builtin settings widget."""
        return False

    @property
    def mouse_pos(self) -> tuple[float, float]:
        """The current position of the mouse."""
        return XWindow.mouse_pos

    def add(self, *args, **kwargs):
        """Add a widget to the root widget."""
        return self.root.add(*args, **kwargs)

    @property
    def current_focus(self) -> kv.Widget:
        """The widget currently in focus."""
        return self.keyboard.target

    @property
    def overlay(self) -> Optional[XOverlay]:
        """The current overlay."""
        return self.__overlay

    def _is_touch_blocked(self, w, m):
        if self.block_input:
            return True
        if not self.__enable_multitouch:
            if hasattr(m, "multitouch_sim") and m.multitouch_sim:
                return True
        return False

    def __create_overlay(self, **kwargs):
        self.__last_focused = self.current_focus
        self.__overlay = XOverlay(**kwargs)
        self.__overlay.focus = True
        self.block_input = True
        self.add(self.__overlay)

    def __destroy_overlay(self, after: Optional[SimpleCallable] = None):
        if self.__last_focused is not None:
            self.__last_focused.focus = True
        self.root.remove_widget(self.__overlay)
        self.__overlay = None
        self.block_input = False
        if after is not None:
            after()

    def with_overlay(
        self,
        func: SimpleCallable,
        after: Optional[SimpleCallable] = None,
        **kwargs,
    ):
        """Queue a function with a temporary `XOverlay` that blocks input.

        Uses the `botroyale.gui.kex.util.queue_around_frame` decorator to draw
        a frame before calling the function, otherwise the added overlay will
        not be seen until execution is yielded to kivy's clock.

        Example usage:
        ```python
        with_overlay(
            func=lambda: my_func(arg1=True),
            text="my_func is executing...",
            after=lambda: print("finished executing my_func."),
        )
        ```

        Args:
            func: Callback to queue after adding the overlay.
            after: Optionally call after removing the overlay.
            kwargs: Keyword arguments for the XOverlay object.
        """
        if self.__overlay is not None:
            raise RuntimeError("Cannot create an overlay when one already exists.")
        queue_around_frame(
            func,
            before=partial(self.__create_overlay, **kwargs),
            after=partial(self.__destroy_overlay, after),
        )()
