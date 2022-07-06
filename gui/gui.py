from util.settings import Settings
from gui import kex, GUI_DEBUG
import gui.kex.widgets as widgets
from api.logic import BaseLogicAPI
from gui.panel import Panel
from gui.tilemap import TileMap


# User-configurable settings
FPS = Settings.get('gui._fps', 60)
WINDOW_SIZE = Settings.get('gui._window_size', [1280, 720])
START_MAXIMIZED = Settings.get('gui._window_maximize', False)
LOG_HOTKEYS = Settings.get('gui.log_hotkeys', False)


class App(widgets.App):
    def __init__(self, logic_cls, **kwargs):
        print('Starting app...')
        super().__init__(**kwargs)
        self.title = 'Bot Royale'
        self.logger = print if LOG_HOTKEYS else lambda *a: None
        kex.resize_window(WINDOW_SIZE)
        if START_MAXIMIZED:
            widgets.kvWindow.maximize()
        assert issubclass(logic_cls, BaseLogicAPI)
        self.logic = logic_cls()
        self.im = widgets.InputManager(app_control_defaults=True, logger=self.logger)
        self.make_widgets()
        self.hook_mainloop(FPS)
        print('GUI initialized.')

    def make_widgets(self):
        self.map = self.add(TileMap(app=self, api=self.logic))
        self.panel = self.add(Panel(control_buttons=(
            ('Quit ([i]ctrl + q[/i])', quit),
            ('Restart ([i]ctrl + w[/i])', kex.restart_script),
            ('GUI debug', self.debug),
            *self.logic.get_control_buttons(),
        )))
        self.panel.set_size(hx=0.5)
        for hk_name, key, callback in self.logic.get_hotekys():
            self.im.register(hk_name, key=key, callback=lambda *a, c=callback: c())
        self.update_widgets()

    def update_widgets(self):
        self.panel.set_text(self.logic.get_match_state())
        self.map.update()

    def mainloop_hook(self, dt):
        self.logic.update()
        self.update_widgets()

    def debug(self, *a):
        if GUI_DEBUG:
            print('GUI DEBUG')
        self.map.debug()
