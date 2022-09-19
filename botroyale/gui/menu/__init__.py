"""Main Menu GUI.

Associated with a `botroyale.api.gui.GameAPI`, to display a menu of widgets with
the ability to create a new `botroyale.api.gui.BattleAPI` object for the
`Battle` class.
"""
from typing import Callable
from botroyale.api.gui import GameAPI, BattleAPI, Control, PALETTE_BG
from botroyale.gui import im_register_controls, hotkey_logger, kex as kx
from botroyale.gui.menubar import MenuBar
from botroyale.gui.menu.menuwidget import get_menu_widget


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
        self.make_bg(kx.XColor(*PALETTE_BG[0]))
        self.api = api
        self.start_new_battle = start_new_battle
        self.menu_widgets = {}
        self.last_menu_values = {}
        self._make_widgets()

    def get_controls(self):
        """Controls for menu."""
        return [
            Control("Battle.New battle", self._try_new_battle, "spacebar"),
            Control("Battle.Refresh menu", self._handle_changes, "enter"),
            Control("Battle.Refresh menu", self._handle_changes, "numpadenter"),
        ]

    def _update_info_panel(self, *args):
        self.info_panel.text = self.api.get_info_panel_text()

    def _make_widgets(self):
        self.clear_widgets()
        # Info panel
        self.info_panel = kx.Label(valign="top", halign="left")
        self.info_panel.set_size(hx=0.9, hy=0.9)
        info_panel_frame = kx.Anchor()
        info_panel_frame.add(self.info_panel)
        # New battle button
        new_battle_btn = kx.Button(
            text="Start New Battle ([i]spacebar[/i])",
            on_release=self._try_new_battle,
        )
        new_battle_btn.set_size(hx=0.8, hy=0.5)
        new_battle_frame = kx.Anchor()
        new_battle_frame.set_size(y=100)
        new_battle_frame.add(new_battle_btn)
        # Lef Panel
        left_panel = kx.Box(orientation="vertical")
        left_panel.set_size(hx=0.3)
        left_panel.make_bg(kx.XColor(*PALETTE_BG[1]))
        left_panel.add(info_panel_frame, new_battle_frame)
        # Menu frame
        self.menu_widgets_container = kx.Box()
        self.menu_widgets_container.set_size(hx=0.95, hy=0.95)
        menu_widgets_frame = kx.Anchor()
        menu_widgets_frame.make_bg(kx.XColor(*PALETTE_BG[0]))
        menu_widgets_frame.add(self.menu_widgets_container)
        # Populate menu widgets frame
        self._remake_menu_widgets()
        # Main frame
        main_frame = self.add(kx.Box())
        main_frame.add(left_panel, menu_widgets_frame)

    def _remake_menu_widgets(self):
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
        if new_api:
            self.start_new_battle(new_api)

    def _handle_changes(self, *args, force=False):
        changes = set()
        new_values = self._get_menu_values()
        for sendto, value in new_values.items():
            if (
                sendto in self.last_menu_values
                and value != self.last_menu_values[sendto]
            ):
                changes.add(sendto)
        self.last_menu_values = new_values
        if not changes and not force:
            return
        do_update = self.api.handle_menu_widget(list(changes), new_values)
        if do_update:
            self._make_widgets()

    def update(self):
        """Handle changes of menu widget values and update info panel text."""
        self._handle_changes()
        self.info_panel.text = self.api.get_info_panel_text()
