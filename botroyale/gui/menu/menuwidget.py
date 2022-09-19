"""An interactive widget for the `MenuFrame`."""
from botroyale.gui import kex as kx
from botroyale.api.gui import InputWidget
from botroyale.api.gui import PALETTE_BG
from botroyale.util import settings


MENU_WIDGET_SIZE = settings.get("gui.menu.widget_size")


class MenuWidget(kx.Anchor):
    """See module documentation for details."""

    def __init__(self, iw: InputWidget, **kwargs):
        """See module documentation for details."""
        super().__init__(**kwargs)
        assert isinstance(iw, InputWidget)
        self.type = iw.type
        self.label = iw.label
        self.default = iw.default
        self.sendto = iw.sendto
        self.options = iw.options
        self.get_value = None
        self.set_size(*MENU_WIDGET_SIZE)
        self.container = self.add(kx.Box(orientation="vertical"))
        self.container.set_size(hx=0.95, hy=0.9)

    def double_height(self, multi=2):
        """Double the widget's height."""
        self.set_size(x=MENU_WIDGET_SIZE[0], y=MENU_WIDGET_SIZE[1] * multi)


class Spacer(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.remove_widget(self.container)
        self.anchor_y = "bottom"
        label = self.add(kx.Label(text=iw.label))
        label.make_bg(kx.XColor(*PALETTE_BG[4]))
        if self.type != "divider":
            self.double_height(multi=2)
            label.set_size(hy=0.75)
        else:
            self.double_height(multi=1.5)


class Toggle(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        btn = self.container.add(kx.ToggleButton(text=iw.label))
        btn.active = iw.default
        self.get_value = lambda: btn.active


class Text(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.double_height()
        label = kx.Label(text=iw.label)
        entry = kx.Entry(text=iw.default)
        self.container.add(label, entry)
        self.get_value = lambda: entry.text


class Select(MenuWidget):
    """See module documentation for details."""

    BTN_COLOR = kx.XColor(*PALETTE_BG[1])

    @classmethod
    def _get_spinner_btn(cls, **kwargs):
        btn = kx.Button(
            background_color=cls.BTN_COLOR.rgba,
            **kwargs,
        )
        btn.set_size(y=35)
        return btn

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.double_height()
        if iw.options is None:
            raise ValueError("Cannot make a select InputWidget without options")
        label = kx.Label(text=iw.label)
        spinner = kx.Spinner(
            text=iw.default,
            value=iw.default,
            values=iw.options,
            background_color=kx.XColor(*PALETTE_BG[1]).rgba,
            update_main_text=True,
            option_cls=self._get_spinner_btn,
        )
        self.container.add(label, spinner)
        self.get_value = lambda: spinner.value


# The class name "Slider" confuses kivy
class Slider_(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.double_height()
        label = kx.Label(text=iw.label)
        slider = kx.Slider(value=iw.default)
        self.container.add(label, slider)
        self.get_value = lambda: slider.value


def get_menu_widget(iw):
    """Return a `MenuWidget` for a given `InputWidget`."""
    if iw.type == "spacer" or iw.type == "divider":
        return Spacer(iw)
    elif iw.type == "toggle":
        return Toggle(iw)
    elif iw.type == "text":
        return Text(iw)
    elif iw.type == "select":
        return Select(iw)
    elif iw.type == "slider":
        return Slider_(iw)
    else:
        raise ValueError(f"Unknown InputWidget type: {iw.type}")
