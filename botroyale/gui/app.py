"""The GUI application itself.

Has two screens: main menu, and battle. Each is associated with an API object
(GameAPI, and BattleAPI respectively) provided by the game logic that instructs
the GUI. Each screen fills the entire window and manages its own
`botroyale.gui.kex.widgets.input_manager.XInputManager` and menu bar. The `App`
is mostly responsible for running the internal mainloop, and switching between
the screens (allowing them to de/activate).

See: `botroyale.gui.menu.MainMenuScreen` and `botroyale.gui.battle.BattleScreen`.
"""
from typing import Optional
from collections import deque
from functools import partial
from botroyale.util import PACKAGE_DIR, settings
from botroyale.util.file import popen_path, get_usr_dir
from botroyale.util.time import RateCounter
from botroyale.api.gui import GameAPI, BattleAPI, Control, Overlay
from botroyale.gui import (
    kex as kx,
    register_controls,
    logger,
    hotkey_logger,
)
from botroyale.gui.menu import MainMenuScreen
from botroyale.gui.battle import BattleScreen


ICON = str(PACKAGE_DIR / "icon.ico")
FPS = settings.get("gui.fps")
WINDOW_SIZE = settings.get("gui.window_size")
WINDOW_POS = settings.get("gui.window_pos")
START_MAXIMIZED = settings.get("gui.window_maximize")
TRANSITION_SPEED = settings.get("gui.transition_speed")


class App(kx.App):
    """See module documentation for details."""

    def __init__(self, game_api: GameAPI, **kwargs):
        """Initialize with a *game_api*."""
        logger("Starting app...")
        assert isinstance(game_api, GameAPI)
        # Kivy app configuration
        super().__init__(**kwargs)
        self.title = "Bot Royale"
        self.icon = ICON
        kx.Window.set_size(*WINDOW_SIZE)
        if any(c >= 0 for c in WINDOW_POS):
            kx.Window.set_position(*WINDOW_POS)
        if START_MAXIMIZED:
            # Schedule maximizing so that the resize happens first, otherwise
            # the resize has no effect.
            kx.schedule_once(kx.Window.maximize)
        # Setup
        self.queued_overlays = deque()
        self._overlay_cooldown = 0
        self.game_api = game_api
        self.fps_counter = RateCounter(sample_size=FPS, starting_elapsed=1000 / FPS)
        # Make widgets
        self.im = kx.InputManager(
            name="App",
            logger=hotkey_logger,
            log_callback=True,
            log_press=True,
            log_release=True,
        )
        register_controls(self.im, self.get_controls())
        self.sm = self.add(kx.ScreenManager(transition_speed=TRANSITION_SPEED))
        self.menu = MainMenuScreen(
            app_controls=self.get_controls(),
            api=self.game_api,
            start_new_battle=self._start_new_battle,
        )
        self.battle = BattleScreen(
            app_controls=self.get_controls(),
            return_to_menu=partial(self.switch_screen, "menu"),
        )
        self.sm.add_screen("menu", self.menu)
        self.sm.add_screen("battle", self.battle)
        self.screen_frames = {
            "menu": self.menu,
            "battle": self.battle,
        }
        self._activate_current_screen()
        # Start mainloop
        logger("GUI initialized, starting mainloop.")
        self.hook(self.update, FPS)

    def _start_new_battle(self, api: BattleAPI):
        self.battle.start_new_battle(api)
        self.switch_screen("battle", force=True)

    def update(self, dt):
        """Called every frame."""
        if self.queued_overlays:
            if self.overlay is not None:
                return
            overlay = self.queued_overlays.popleft()
            assert isinstance(overlay, Overlay)
            logger(f"Executing {overlay=}")
            self.with_overlay(overlay.func, text=overlay.text, after=overlay.after)
            return
        self.fps_counter.tick()
        if self.sm.current == "menu":
            self.menu.update()
        elif self.sm.current == "battle":
            self.battle.update()

    def switch_screen(
        self,
        screen: str,
        force: bool = False,
        _attempt: int = 0,
    ):
        """Switch and activate a screen, deactivating others."""
        interval = 0.05
        timeout = 2
        if (_attempt * interval) > timeout:
            logger(f"Attempted to switch to screen {screen} but timed out.")
            return
        switch_success = self.sm.switch_name(screen)
        if not switch_success:
            if force:
                logger(
                    f"Cannot switch screen {self.sm.mid_transition=}, "
                    f"trying again in 50ms (attempt: {_attempt})..."
                )
                kx.schedule_once(
                    lambda *args: self.switch_screen(
                        screen=screen,
                        force=force,
                        _attempt=_attempt + 1,
                    ),
                    interval,
                )
            return
        kx.schedule_once(self._activate_current_screen)
        logger(f"Switched to screen: {screen}")

    def _activate_current_screen(self, *args):
        current_screen = self.sm.current
        for screen_name, frame in self.screen_frames.items():
            if screen_name == current_screen:
                frame.activate()
            else:
                frame.deactivate()
        self._hotkey_debug()

    def get_controls(self):
        """Global app controls."""
        return [
            Control(
                "App",
                "Main Menu",
                partial(self.switch_screen, "menu"),
                ["f1", "escape"],
            ),
            Control("App", "Battle", partial(self.switch_screen, "battle"), "f2"),
            Control("App", "User folder", _show_usrdir, "^+ f"),
            Control("App", "Debug", self._debug, "!+ d"),
            Control("App", "Restart", kx.restart_script, "^+ w"),
            Control("App", "Quit", quit, "^+ q"),
        ]

    def _debug(self, *args):
        """GUI Debug."""
        logger("GUI DEBUG")
        print(f"{self.current_focus=}")
        self._hotkey_debug()

    def _hotkey_debug(self, *args):
        """Debug logs."""
        hotkey_logger(
            "\n".join(
                [
                    "=" * 50,
                    f"Current screen: {self.sm.current}",
                    "",
                    self.im._debug_str,
                    "",
                    self.menu.im._debug_str,
                    "",
                    self.battle.im._debug_str,
                    "=" * 50,
                ]
            )
        )

    def overlay_calls(self, overlays: Optional[list[Overlay]]):
        """Queue calling functions while displaying an overlay."""
        if overlays is None:
            return
        self.queued_overlays.extend(overlays)


def _show_usrdir(*args):
    """Open the user's directory."""
    usrdir = get_usr_dir("subfolder").parent
    popen_path(usrdir)
