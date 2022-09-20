"""GUI App.

Has two modes: main menu, and battle. Each is associated with an API (GameAPI,
and BattleAPI respectively), and fills the entire window. The `App` is mostly
responsible for running the internal mainloop, and switching between the modes.

See: `MainMenu` and `BattleContainer`.
"""
from botroyale.util import PACKAGE_DIR
from botroyale.util import settings
from botroyale.util.time import RateCounter
from botroyale.api.gui import GameAPI, BattleAPI, Control
from botroyale.gui import kex as kx, logger, im_register_controls, hotkey_logger
from botroyale.gui.menu import MainMenu
from botroyale.gui.battle import BattleContainer


ICON = str(PACKAGE_DIR / "icon.ico")
FPS = settings.get("gui.fps")
WINDOW_SIZE = settings.get("gui.window_size")
START_MAXIMIZED = settings.get("gui.window_maximize")
TRANSITION_SPEED = settings.get("gui.transtion_speed")
LOG_HOTKEYS = settings.get("logging.hotkeys")


class App(kx.App):
    """See module documentation for details."""

    def __init__(self, game_api, **kwargs):
        """See module documentation for details.

        Args:
            game_api: Instance of `botroyale.api.gui.GameAPI`.
        """
        logger("Starting app...")
        assert isinstance(game_api, GameAPI)
        # Kivy app configuration
        super().__init__(**kwargs)
        self.title = "Bot Royale"
        self.icon = ICON
        kx.Window.set_size(*WINDOW_SIZE)
        if START_MAXIMIZED:
            # Schedule maximizing so that the resize happens first, otherwise
            # the resize has no effect.
            kx.schedule_once(kx.Window.maximize)
        # Setup
        self.game_api = game_api
        self.fps_counter = RateCounter(sample_size=FPS, starting_elapsed=1000 / FPS)
        # Make widgets
        self.sm = self.add(kx.ScreenManager(auto_transtion_speed=TRANSITION_SPEED))
        self.menu = MainMenu(
            app_controls=self.get_controls(),
            api=self.game_api,
            start_new_battle=self._start_new_battle,
        )
        self.battle = BattleContainer(
            app_controls=self.get_controls(),
            return_to_menu=self.show_menu,
        )
        self.sm.add_screen("menu", self.menu)
        self.sm.add_screen("battle", self.battle)
        self.im = kx.InputManager(name="App", logger=hotkey_logger)
        im_register_controls(self.im, self.get_controls())
        self.show_menu(force=True)
        # Start mainloop
        logger("GUI initialized, starting mainloop.")
        self.hook(self.update, FPS)

    def _start_new_battle(self, api: BattleAPI):
        if self.sm.mid_transition:
            logger("Cannot start new battle, trying again in 50ms...")
            kx.schedule_once(lambda *args, api=api: self._start_new_battle(api), 0.05)
            return
        self.battle.start_new_battle(api)
        self.show_battle()

    def update(self, dt):
        """Called every frame."""
        self.fps_counter.tick()
        if self.sm.current == "menu":
            self.menu.update()
        elif self.sm.current == "battle":
            self.battle.update()

    def show_menu(self, *args, force=False):
        """Switch to main menu."""
        if not self.sm.switch_name("menu") and not force:
            return
        logger("Switching to main menu.")
        self.battle.deactivate()
        self.menu.activate()

    def show_battle(self, *args):
        """Switch to battle."""
        if not self.sm.switch_name("battle"):
            return
        logger("Switching to battle.")
        self.menu.deactivate()
        self.battle.activate()

    def get_controls(self):
        """Global app controls."""
        return [
            Control("App.Main Menu", self.show_menu, "escape"),
            Control("App.Main Menu", self.show_menu, "f1"),
            Control("App.Battle", self.show_battle, "f2"),
            Control("App.Restart", kx.restart_script, "^+ w"),
            Control("App.Quit", quit, "^+ q"),
        ]
