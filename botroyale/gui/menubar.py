"""Top menu bar widget."""
from botroyale.gui import (
    kex as kx,
    widget_defaults as defaults,
    categorize_controls,
)
from botroyale.api.gui import Control
from botroyale.util import settings


DEBUG_COLORS = settings.get("gui.debug_colors")


def _get_spinner_btn(**kwargs):
    btn = kx.Button(**defaults.BUTTON_AUX, **kwargs)
    btn.set_size(y=defaults.LINE_HEIGHT)
    return btn


class MenuBar(kx.Box):
    """See module documentation for details."""

    def __init__(self, controls: list[Control], **kwargs):
        """See module documentation for details."""
        super().__init__(**kwargs)
        self.set_size(y=40)
        self.make_bg(kx.get_color("black"))
        self.controls = {}
        self.set_controls(controls)

    def set_controls(self, controls: list[Control]):
        """Reset the controls."""
        self.controls = {c.label: c for c in controls}
        self.clear_widgets()
        self.add(*self._get_spinner_widgets(controls))
        if DEBUG_COLORS:
            self.add(self._get_palette_box())

    def _get_spinner_widgets(self, controls: list[Control]):
        spinners = []
        for category, controls in categorize_controls(controls).items():
            control_labels = []
            for c in controls:
                if "." not in c.label:
                    raise ValueError(
                        "Control label must be categorized like so: "
                        f'"Category name.Control name", got: {c.label}'
                    )
                label = c.label.split(".", 1)[-1]
                if c.hotkey:
                    hotkey_label = kx.InputManager.humanize_keys(c.hotkey)
                    label = f"{label} ([i]{hotkey_label}[/i])"
                control_labels.append(label)
            spinner = kx.Spinner(
                text=category,
                values=control_labels,
                **defaults.BUTTON,
                update_main_text=False,
                option_cls=_get_spinner_btn,
            )
            spinner.on_select = lambda l, c=category: self._invoke_control(c, l)
            spinners.append(spinner)
        return spinners

    def _get_palette_box(self):
        palette_box = kx.Box()
        total_width = 0
        for name, color in defaults.COLORS.items():
            w = kx.Label(text=name.capitalize(), color=color.fg.rgba)
            w.set_size(x=60)
            total_width += 60
            w.make_bg(color.bg)
            palette_box.add(w)
        for i in range(5):
            fg = kx.Label(text=str(i), color=kx.get_color("black").rgba)
            fg.make_bg(defaults.PALETTE[i])
            bg = kx.Label(text=str(5 + i), color=kx.get_color("white").rgba)
            bg.make_bg(defaults.PALETTE_BG[i])
            w = kx.Box(orientation="vertical")
            w.add(fg, bg)
            w.set_size(x=50)
            total_width += 50
            palette_box.add(w)
        palette_box.set_size(x=total_width)
        return palette_box

    def _invoke_control(self, category, label):
        label = label.split(" ([i]", 1)[0]
        original_label = f"{category}.{label}" if category else label
        control = self.controls[original_label]
        control.callback()
