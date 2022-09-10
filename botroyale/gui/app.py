from botroyale.util import PACKAGE_DIR
from botroyale.util import settings
from botroyale.util.time import RateCounter
from botroyale.api.logging import logger as glogger
from botroyale.api.gui import GameAPI, BattleAPI, Control, combine_control_menus
from botroyale.gui import kex, logger
from botroyale.gui.kex import widgets
from botroyale.gui.menubar import MenuBar
from botroyale.gui.game.game import GameScreen
from botroyale.gui.battle.battle import BattleScreen


ICON = str(PACKAGE_DIR / 'icon.ico')
# User-configurable settings
FPS = settings.get('gui.fps')
WINDOW_SIZE = settings.get('gui.window_size')
START_MAXIMIZED = settings.get('gui.window_maximize')
LOG_HOTKEYS = settings.get('logging.hotkeys')


class App(widgets.App):
    def __init__(self, game_api, **kwargs):
        logger('Starting app...')
        assert isinstance(game_api, GameAPI)
        # Kivy App widget configuration
        super().__init__(**kwargs)
        self.title = 'Bot Royale'
        self.icon = ICON
        kex.resize_window(WINDOW_SIZE)
        if START_MAXIMIZED:
            # Schedule maximizing so that the resize happens first, otherwise
            # the resize has no effect.
            widgets.kvClock.schedule_once(lambda *a: widgets.kvWindow.maximize())
        # Setup
        self.game_api = game_api
        self.fps_counter = RateCounter(sample_size=FPS, starting_elapsed=1000/FPS)
        self.im = widgets.InputManager(
            logger=glogger if LOG_HOTKEYS else lambda *a: None)
        # Make widgets
        self.main_frame = self.add(widgets.FlipZIndex(orientation='vertical'))
        self.game = GameScreen(self.game_api)
        self.battle = None
        self.set_menu_mode(force=True)
        # Start mainloop
        self.hook_mainloop(FPS)
        logger('GUI initialized.')

    def mainloop_hook(self, dt):
        """Called every frame."""
        # Count FPS
        self.fps_counter.tick()
        self.bar.set_text(f'{self.fps_counter.rate:.2f} FPS')

        # Update game or battle (depending on mode)
        if not self.battle:
            new_battle_api = self.game.update()
            # Game update may return a BattleAPI if a new battle is to start
            if new_battle_api:
                assert isinstance(new_battle_api, BattleAPI)
                self.set_battle_mode(new_battle_api)
        if self.battle:
            self.battle.update()

    def set_menu_mode(self, force=False):
        if not force and self.battle is None:
            return
        logger('GUI creating game menu...')
        self.battle = None
        # Recreate menu bar
        game_controls = self.game.get_controls()
        game_controls = combine_control_menus({'App': []}, game_controls)
        app_controls = self.get_controls(include_menu_return=False)
        controls = combine_control_menus(game_controls, app_controls)
        self.bar = MenuBar(controls)
        self.register_controls(controls)
        # Assemble widgets
        self.main_frame.clear_widgets()
        self.main_frame.add(self.bar)
        self.main_frame.add(self.game)

    def set_battle_mode(self, api):
        logger('GUI making new battle...')
        self.battle = BattleScreen(api)
        # Recreate menu bar
        battle_controls = self.battle.get_controls()
        battle_controls = combine_control_menus({'App': []}, battle_controls)
        app_controls = self.get_controls()
        controls = combine_control_menus(battle_controls, app_controls)
        self.bar = MenuBar(controls)
        self.register_controls(controls)
        # Assemble widgets
        self.main_frame.clear_widgets()
        self.main_frame.add(self.bar)
        self.main_frame.add(self.battle)

    def get_controls(self, include_menu_return=True):
        return_to_menu = []
        if include_menu_return:
            return_to_menu = [Control('Main menu', self.set_menu_mode, 'escape')]
        controls = {'App': [
            *return_to_menu,
            Control('Restart', kex.restart_script, '^+ w'),
            Control('Quit', quit, '^+ q'),
            ]}
        return controls

    def register_controls(self, control_menu):
        # Register hotkeys
        self.im.clear_all()
        for menu in control_menu.values():
            for control, callback, key in menu:
                if key is None:
                    continue
                self.im.register(control, key, callback=lambda *a, c=callback: c())
