"""Layout widgets."""
from typing import Literal
from .. import kivy as kv
from ..util import XWidget


class XBox(XWidget, kv.BoxLayout):
    """BoyLayout."""

    pass


class XZBox(XWidget, kv.GridLayout):
    """Behaves like a Box where widgets are drawn in reverse order."""

    def __init__(
        self,
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        **kwargs,
    ):
        """Initialize the class."""
        if orientation == "horizontal":
            kwargs["orientation"] = "rl-tb"
            kwargs["rows"] = 1
        elif orientation == "vertical":
            kwargs["orientation"] = "lr-bt"
            kwargs["cols"] = 1
        else:
            raise ValueError(
                'FlipZIndex orientation must be "horizontal" or "vertical"'
            )
        super().__init__(**kwargs)

    def add(self, *children, **kwargs):
        """Overrides base method to insert correctly."""
        for child in children:
            super().add(child, insert_last=True, **kwargs)
        return child


class XDBox(XWidget, kv.GridLayout):
    """Behaves like a Box that will dynamically resize based on children's height."""

    def __init__(self, cols: int = 1, **kwargs):
        """Initialize the class."""
        super().__init__(cols=cols, **kwargs)

    def add(self, w: XWidget, *args, **kwargs):
        """Overrides XWidget `add` in order to bind to size changes."""
        w.bind(size=self._resize)
        r = super().add(w, *args, **kwargs)
        kv.Clock.schedule_once(self._resize, 0)
        return r

    def remove_widget(self, *a, **k):
        """Overrides base class `remove_widget` in order to resize."""
        super().remove_widget(*a, **k)
        self._resize()

    def _resize(self, *a):
        self.set_size(hx=1, y=sum([c.height for c in self.children]))


class XGrid(XWidget, kv.GridLayout):
    """GridLayout."""

    pass


class XStack(XWidget, kv.StackLayout):
    """StackLayout."""

    pass


class XRelative(XWidget, kv.RelativeLayout):
    """RelativeLayout."""

    pass


class XAnchor(XWidget, kv.AnchorLayout):
    """AnchorLayout."""


class XScroll(XWidget, kv.ScrollView):
    """ScorllView."""

    def __init__(
        self,
        view: XWidget,
        scroll_dir: Literal["vertical", "horizontal"] = "vertical",
        scroll_amount: float = 50,
        **kwargs,
    ):
        """Initialize the class.

        Args:
            view: A widget to put in the scroll view.
            scroll_dir: Direction of scroll: "horizontal" or "vertical"
            scroll_amount: Resolution of scroll in pixels.
        """
        super().__init__(**kwargs)
        self.scroll_dir = scroll_dir
        self.scroll_amount = scroll_amount
        self.bar_width = 15
        self.scroll_type = ["bars"]
        self.view = self.add(view)
        self.bind(size=self._on_size, on_touch_down=self._on_touch_down)
        self.view.bind(size=self._on_size)

    @property
    def scroll_dir(self):
        """Scrolling direction."""
        return self.__scroll_dir

    @scroll_dir.setter
    def scroll_dir(self, v):
        self.__scroll_dir = v
        self.do_scroll_x = v == "horizontal"
        self.do_scroll_y = v == "vertical"

    def _on_size(self, *a):
        self.do_scroll_x = (
            self.view.size[0] > self.size[0] and self.scroll_dir == "horizontal"
        )
        self.do_scroll_y = (
            self.view.size[1] > self.size[1] and self.scroll_dir == "vertical"
        )
        if self.size[0] >= self.view.size[0]:
            self.scroll_x = 1
        if self.size[1] >= self.view.size[1]:
            self.scroll_y = 1

    def _on_touch_down(self, w, m):
        if m.button not in {"scrollup", "scrolldown"}:
            return False
        if not any((self.do_scroll_x, self.do_scroll_y)):
            return False
        if not self.collide_point(*m.pos):
            return False

        dir = -1 if m.button == "scrollup" else 1
        pixels_x, pixels_y = self.convert_distance_to_scroll(
            self.scroll_amount,
            self.scroll_amount,
        )
        if self.scroll_dir == "horizontal":
            self.scroll_x = min(1, max(0, self.scroll_x + pixels_x * dir))
        elif self.scroll_dir == "vertical":
            self.scroll_y = min(1, max(0, self.scroll_y + pixels_y * dir))
        return True
