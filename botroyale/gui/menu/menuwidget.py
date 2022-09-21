"""An interactive widget for the `MenuFrame`."""
from botroyale.gui import (
    kex as kx,
    widget_defaults as defaults,
)
from botroyale.api.gui import InputWidget
from botroyale.util import settings


WIDGETS_FRAME_BG = defaults.COLORS["default"].bg
WIDGET_DARKER_BG = kx.XColor(*WIDGETS_FRAME_BG.rgba, v=0.75)
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
        self.set_size(*WIDGET_SIZE)
        self.container = self.add(kx.Box(orientation="vertical"))
        self.container.set_size(hx=0.95, hy=0.9)

    def get_value(self):
        """Get the widget value, using the subclass method."""
        return self._get_value()

    def set_value(self, new_value):
        """Set the widget value, using the subclass method."""
        try:
            self._set_value(new_value)
        except ValueError:
            raise ValueError(
                f"Cannot set {self} with {new_value=} of type {type(new_value)}"
            )

    def _set_value(self):
        raise NotImplementedError(f"{self} has not implemented set_value()")

    def double_height(self, multi=2, bg=False):
        """Double the widget's height and optionally draw a darker background."""
        self.set_size(x=WIDGET_SIZE[0], y=WIDGET_SIZE[1] * multi)
        if bg:
            self.make_bg(WIDGET_DARKER_BG)


class Spacer(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.remove_widget(self.container)
        self.anchor_y = "bottom"
        self.label = self.add(
            kx.Label(
                text=iw.label,
                **(defaults.TEXT | {"color": defaults.COLORS["alt"].fg.rgba}),
            )
        )
        self.label.make_bg(defaults.COLORS["alt"].bg)
        if self.type != "divider":
            self.double_height(multi=2)
            self.label.set_size(hy=0.75)
        else:
            self.double_height(multi=1.5)

    def _get_value(self):
        return self.label.text

    def _set_value(self, new_value):
        self.label.text = new_value


class Toggle(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.btn = self.container.add(
            kx.ToggleButton(
                text=iw.label,
                **defaults.BUTTON,
            )
        )
        self.btn.active = iw.default

    def _get_value(self):
        return self.btn.active

    def _set_value(self, new_value):
        self.btn.active = new_value


class Text(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.double_height(bg=True)
        label = kx.Label(text=iw.label, **defaults.TEXT_MONO)
        self.entry = kx.Entry(
            text=iw.default,
            halign="center",
            foreground_color=defaults.TEXT_COLOR,
            cursor_color=defaults.WHITE.rgba,
        )
        self.container.add(label, self.entry)

    def _get_value(self):
        return self.entry.text

    def _set_value(self, new_value):
        self.entry.text = new_value


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
        self.double_height(bg=True)
        if iw.options is None:
            raise ValueError("Cannot make a select InputWidget without options")
        label = kx.Label(text=iw.label, **defaults.TEXT_MONO)
        self.spinner = kx.Spinner(
            text=iw.default,
            value=iw.default,
            values=iw.options,
            **defaults.BUTTON_AUX,
            update_main_text=True,
            option_cls=self._get_spinner_btn,
        )
        self.container.add(label, self.spinner)

    def _get_value(self):
        return self.spinner.value

    def _set_value(self, new_value):
        self.spinner.text = new_value


# The class name "Slider" confuses kivy
class Slider_(MenuWidget):
    """See module documentation for details."""

    def __init__(self, iw, **kwargs):
        """See module documentation for details."""
        super().__init__(iw, **kwargs)
        self.double_height(bg=True)
        label = kx.Label(text=iw.label, **defaults.TEXT_MONO)
        self.slider = kx.SliderText(
            min=iw.slider_range[0],
            max=iw.slider_range[1],
            step=iw.slider_range[2],
            value=iw.default,
        )
        self.container.add(label, self.slider)

    def _get_value(self):
        return self.slider.slider.value

    def _set_value(self, new_value):
        self.slider.slider.value = new_value


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
