"""An interactive widget for the `MenuFrame`."""
from botroyale.gui import (
    kex as kx,
    widget_defaults as defaults,
)
from botroyale.api.gui import InputWidget
from botroyale.util import settings


WIDGET_SIZE = settings.get("gui.menu.widget_size")


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
        self.set_size(*WIDGET_SIZE)
        self.container = self.add(kx.Box())
        self.container.set_size(hx=0.95, hy=0.9)

    def double_height(self, multi=2):
        """Double the widget's height."""
        self.set_size(x=WIDGET_SIZE[0], y=WIDGET_SIZE[1] * multi)


class Spacer(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.remove_widget(self.container)
        self.anchor_y = "bottom"
        label = self.add(
            kx.Label(
                text=iw.label,
                **(defaults.TEXT | {"color": defaults.COLORS["alt"].fg.rgba}),
            )
        )
        label.make_bg(defaults.COLORS["alt"].bg)
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
        btn = self.container.add(
            kx.ToggleButton(
                text=iw.label,
                **defaults.BUTTON,
            )
        )
        btn.active = iw.default
        self.get_value = lambda: btn.active


class Text(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        label = kx.Label(text=iw.label, **defaults.TEXT_MONO)
        entry = kx.Entry(
            text=iw.default,
            foreground_color=defaults.TEXT_COLOR,
            cursor_color=defaults.WHITE.rgba,
        )
        self.container.add(label, entry)
        self.get_value = lambda: entry.text


class Select(MenuWidget):
    """See module documentation for details."""

    @classmethod
    def _get_spinner_btn(cls, **kwargs):
        btn = kx.Button(**(defaults.BUTTON_LIGHT | kwargs))
        btn.set_size(y=defaults.LINE_HEIGHT)
        return btn

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        if iw.options is None:
            raise ValueError("Cannot make a select InputWidget without options")
        label = kx.Label(text=iw.label, **defaults.TEXT_MONO)
        spinner = kx.Spinner(
            text=iw.default,
            value=iw.default,
            values=iw.options,
            **defaults.BUTTON_AUX,
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
        label = kx.Label(text=iw.label, **defaults.TEXT_MONO)
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
