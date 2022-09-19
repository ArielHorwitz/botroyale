"""Top menu bar widget."""
from botroyale.gui import ASSETS_DIR, FONT, FONT_SIZE, categorize_controls, kex as kx
from botroyale.util import settings
from botroyale.api.gui import Control, PALETTE_BG


font = settings.get("gui.fonts.menubar")
FONT_MENU = str(ASSETS_DIR / "fonts" / f"{font}.ttf")
BTN_COLOR = kx.XColor(*PALETTE_BG[1])


def _get_spinner_btn(**kwargs):
    btn = kx.Button(
        font_size=FONT_SIZE,
        font_name=FONT,
        background_color=BTN_COLOR.rgba,
        **kwargs,
    )
    btn.set_size(y=35)
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
                background_color=BTN_COLOR.rgba,
                update_main_text=False,
                option_cls=_get_spinner_btn,
            )
            spinner.on_select = lambda l, c=category: self._invoke_control(c, l)
            spinners.append(spinner)
        return spinners

    def _invoke_control(self, category, label):
        label = label.split(" ([i]", 1)[0]
        original_label = f"{category}.{label}" if category else label
        control = self.controls[original_label]
        control.callback()
