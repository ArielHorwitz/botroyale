"""Container for the Battle GUI.

The `BattleContainer` may be associated with a `botroyale.api.gui.BattleAPI`.
If so, will display the `BattleFrame`. Otherwise will display a placeholder with
the option to return to the main menu.
"""
from typing import Callable
from botroyale.api.gui import Control, BattleAPI
from botroyale.gui import (
    kex as kx,
    widget_defaults as defaults,
    im_register_controls,
    hotkey_logger,
    logger,
)
from botroyale.gui.battle.tilemap import TileMap
from botroyale.gui.menubar import MenuBar


def _get_placeholder(return_to_menu):
    anchor = kx.Anchor()
    anchor.make_bg(defaults.COLORS["default"].bg)
    box = anchor.add(kx.Box(orientation="vertical"))
    box.set_size(x=300, y=300)
    label = kx.Label(
        text="No battle in progress.\nStart a new battle in the menu.",
        **(defaults.TEXT | {"color": defaults.COLORS["default"].fg.rgba}),
    )
    label.set_size(hy=4)
    button = kx.Button(
        text="Return to menu",
        on_release=lambda *a: return_to_menu(),
        **defaults.BUTTON,
    )
    box.add(label, button)
    return anchor


class BattleContainer(kx.ZBox):
    """See module documentation for details."""

    def __init__(
        self, app_controls: list[Control], return_to_menu: Callable[[], None], **kwargs
    ):
        """See module documentation for details."""
        super().__init__(orientation="vertical", **kwargs)
        self.app_controls = app_controls
        self.return_to_menu = return_to_menu
        self.placeholder = _get_placeholder(return_to_menu)
        self.bar = self.add(MenuBar(app_controls))
        self.battle_frame = self.add(kx.Anchor())
        self.battle_frame.add(self.placeholder)
        self.battle_in_progress = None
        self.im = kx.InputManager(
            name="Battle",
            active=False,
            logger=hotkey_logger,
        )

    def update(self, *args):
        """Update battle GUI if in progress."""
        if self.battle_in_progress:
            self.battle_in_progress.update()

    def activate(self, *args):
        """Activate the Battle GUI."""
        self.im.activate()

    def deactivate(self, *args):
        """Deactivate the Battle GUI."""
        self.im.deactivate()

    def start_new_battle(self, api: BattleAPI):
        """Start a new battle."""
        logger(f"Starting new battle: {api=}")
        assert isinstance(api, BattleAPI)
        self.battle_in_progress = BattleFrame(api=api)
        self.battle_frame.clear_widgets()
        self.battle_frame.add(self.battle_in_progress)
        controls = self.battle_in_progress.get_controls()
        self.bar.set_controls(self.app_controls + controls)
        im_register_controls(self.im, controls)


class BattleFrame(kx.Anchor):
    """See module documentation for details."""

    def __init__(self, api, **kwargs):
        """See module documentation for details."""
        super().__init__(**kwargs)
        self.api = api
        self.panel = Panel(api)
        self.map = TileMap(api)
        main_frame = self.add(kx.ZBox(orientation="horizontal"))
        main_frame.add(self.panel.set_size(hx=0.5))
        main_frame.add(self.map)

    def get_controls(self):
        """Get the Controls from the different components of the battle API and GUI."""
        map_controls = self.map.get_controls()
        api_controls = self.api.get_controls()
        return map_controls + api_controls

    def update(self):
        """Refresh all things battle-related."""
        self.api.update()
        self.panel.update()
        self.map.update()


class Panel(kx.Box):
    """See module documentation for details."""

    def __init__(self, api, **kwargs):
        """See module documentation for details."""
        super().__init__(orientation="vertical")
        self.make_bg(defaults.COLORS["dark"].bg)
        self.api = api
        text_frame = self.add(
            kx.Anchor(anchor_x="left", anchor_y="top", padding=(15, 15))
        )
        self.main_text = text_frame.add(
            kx.Label(
                valign="top",
                halign="left",
                **defaults.TEXT_MONO,
            ),
        )

    def update(self):
        """Update the panel text."""
        text = self.api.get_info_panel_text()
        self.main_text.text = text
        color_name = self.api.get_info_panel_color()
        color = defaults.COLORS[color_name]
        self.main_text.color = color.fg.rgba
        self.make_bg(color.bg)
