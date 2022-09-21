"""Main Menu GUI.

Associated with a `botroyale.api.gui.GameAPI`, to display a menu of widgets with
the ability to create a new `botroyale.api.gui.BattleAPI` object for the
`Battle` class.
"""
from typing import Callable
from botroyale.api.gui import GameAPI, BattleAPI, Control, MENU_UPDATE_RESPONSES
from botroyale.gui import (
    kex as kx,
    widget_defaults as defaults,
    im_register_controls,
    logger,
    hotkey_logger,
)
from botroyale.gui.menubar import MenuBar
from botroyale.gui.menu.menuwidget import get_menu_widget, WIDGETS_FRAME_BG


NewBattleCall = Callable[[BattleAPI], None]


class MainMenu(kx.ZBox):
    """See module documentation for details."""

    def __init__(
        self,
        app_controls: list[Control],
        api: GameAPI,
        start_new_battle: NewBattleCall,
        **kwargs,
    ):
        """See module documentation for details."""
        super().__init__(orientation="vertical", **kwargs)
        assert isinstance(api, GameAPI)
        self.api = api
        self.menu = MenuFrame(api=api, start_new_battle=start_new_battle)
        controls = api.get_controls() + self.menu.get_controls()
        self.bar = MenuBar(app_controls + controls)
        self.im = kx.InputManager(
            name="Main menu",
            active=False,
            logger=hotkey_logger,
        )
        im_register_controls(self.im, controls)
        # Assemble widgets
        self.clear_widgets()
        self.add(self.bar, self.menu)

    def update(self, *args):
        """Update the menu frame."""
        self.menu.update()

    def activate(self, *args):
        """Set the widget as being visible."""
        self.im.activate()

    def deactivate(self, *args):
        """Set the widget as being invisible."""
        self.im.deactivate()


class MenuFrame(kx.Anchor):
    """Builds the widgets menu for the GameAPI."""

    def __init__(self, api: GameAPI, start_new_battle: NewBattleCall, **kwargs):
        """See module documentation for details."""
        super().__init__(**kwargs)
        self.api = api
        self.start_new_battle = start_new_battle
        self.menu_widgets = {}
        self.last_menu_values = {}
        self._make_widgets()

    def get_controls(self):
        """Controls for menu."""
        return [
            Control("Battle.New battle", self._try_new_battle, "spacebar"),
            Control("Battle.Refresh menu", lambda *a: self.update(force=True), "enter"),
        ]

    def _update_info_panel(self, *args):
        self.info_panel.text = self.api.get_info_panel_text()
        self.new_battle_btn.text = (
            f"{self.api.get_new_battle_text()}"
            f"\n([i]{kx.InputManager.humanize_keys('spacebar')}[/i])"
        )

    def _make_widgets(self):
        self.clear_widgets()
        # Info panel
        self.info_panel = kx.Label(
            valign="top",
            halign="left",
            **defaults.TEXT_MONO,
            text=self.api.get_info_panel_text(),
        )
        self.info_panel.set_size(hx=0.9, hy=0.9)
        info_panel_frame = kx.Anchor()
        info_panel_frame.add(self.info_panel)
        # New battle button
        self.new_battle_btn = kx.Button(
            on_release=self._try_new_battle,
            **defaults.BUTTON_LIGHT,
        )
        self._update_info_panel()
        self.new_battle_btn.set_size(hx=0.8, hy=0.75)
        new_battle_frame = kx.Anchor()
        new_battle_frame.set_size(y=100)
        new_battle_frame.add(self.new_battle_btn)
        # Left Panel
        left_panel = kx.Box(orientation="vertical")
        left_panel.set_size(hx=0.3)
        left_panel.make_bg(defaults.COLORS["aux"].bg)
        left_panel.add(info_panel_frame, new_battle_frame)
        # Menu frame
        self.menu_widgets_container = kx.Box()
        self.menu_widgets_container.set_size(hx=0.95, hy=0.95)
        menu_widgets_frame = kx.Anchor()
        menu_widgets_frame.make_bg(WIDGETS_FRAME_BG)
        menu_widgets_frame.add(self.menu_widgets_container)
        # Populate menu widgets frame
        self._remake_menu_widgets()
        # Main frame
        main_frame = self.add(kx.Box())
        main_frame.add(left_panel, menu_widgets_frame)

    def _remake_menu_widgets(self):
        logger("Creating menu widgets.")
        menu_widgets = self.api.get_menu_widgets()
        self.menu_widgets = {}
        self.menu_widgets_container.clear_widgets()

        def new_stack():
            stack = kx.DBox()
            scroller = kx.Scroll(view=stack)
            self.menu_widgets_container.add(scroller)
            return stack

        stack = new_stack()
        for idx, iw in enumerate(menu_widgets):
            logger(f"    Creating new widget: {iw}")
            menu_widget = get_menu_widget(iw)
            if menu_widget.type == "divider" and idx > 0:
                stack = new_stack()
            assert iw.sendto == menu_widget.sendto
            if menu_widget.get_value is not None:
                self.menu_widgets[iw.sendto] = menu_widget
            stack.add(menu_widget)
        self.last_menu_values = self._get_menu_values()

    def _get_menu_values(self):
        return {sendto: w.get_value() for sendto, w in self.menu_widgets.items()}

    def _try_new_battle(self, *args):
        """Try creating a new battle from current menu values."""
        menu_values = self._get_menu_values()
        new_api = self.api.get_new_battle(menu_values)
        self._update_info_panel()
        if new_api:
            self.start_new_battle(new_api)

    def _refresh_values(self):
        logger("Refreshing menu widget values.")
        for widget in self.api.get_menu_widgets():
            sendto = widget.sendto
            if sendto not in self.menu_widgets:
                continue
            old_value = self.menu_widgets[sendto].get_value()
            new_value = widget.default
            if old_value == new_value:
                continue
            logger(f"    Updating {sendto=} {old_value=} {new_value=}")
            self.menu_widgets[sendto].set_value(new_value)
        self.last_menu_values = self._get_menu_values()

    def update(self, force=False):
        """Handle changes of menu widget values and update info panel text."""
        changes = set()
        new_values = self._get_menu_values()
        for sendto, value in new_values.items():
            if (
                sendto in self.last_menu_values
                and value != self.last_menu_values[sendto]
            ):
                logger(f'    User set "{sendto}" in main menu to {value=}')
                changes.add(sendto)
        self.last_menu_values = new_values
        if not changes and not force:
            return
        menu_update = self.api.handle_menu_widget(list(changes), new_values)
        assert menu_update in MENU_UPDATE_RESPONSES
        if menu_update == "nothing":
            return
        if menu_update == "values":
            self._refresh_values()
        elif menu_update == "widgets":
            self._make_widgets()
        else:
            raise NotImplementedError(f"Unknown menu update response: {menu_update}")
        self._update_info_panel()
