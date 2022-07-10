from util.settings import Settings
from gui import kex, logger
import gui.kex.widgets as widgets
from api.logic import BaseLogicAPI
from gui.panel import Panel
from gui.tilemap import TileMap


# User-configurable settings
FPS = Settings.get('gui._fps', 60)
WINDOW_SIZE = Settings.get('gui._window_size', [1280, 720])
START_MAXIMIZED = Settings.get('gui._window_maximize', True)
LOG_HOTKEYS = Settings.get('gui.log_hotkeys', False)


class App(widgets.App):
    def __init__(self, logic_cls, **kwargs):
        logger('Starting app...')
        super().__init__(**kwargs)
        self.title = 'Bot Royale'
        kex.resize_window(WINDOW_SIZE)
        if START_MAXIMIZED:
            widgets.kvWindow.maximize()
        assert issubclass(logic_cls, BaseLogicAPI)
        self.__logic_cls = logic_cls
        self.logic = self.__logic_cls()
        self.im = widgets.InputManager(
            logger=print if LOG_HOTKEYS else lambda *a: None)
        self.make_widgets()
        self.hook_mainloop(FPS)
        logger('GUI initialized.')

    def make_widgets(self):
        def get_control_button(control):
            control, callback, key = control
            if key:
                control = f'{control} ([i]{self.im.humanize_keys(key)}[/i])'
            return (control, lambda *a, c=callback: c())
        controls = [
            ('Quit', quit, '^+ q'),
            ('Restart', kex.restart_script, '^+ w'),
            ('GUI debug', self.debug, None),
            ('New battle', self.reset_logic, '^ n'),
            *self.logic.get_controls(),
        ]
        self.map = self.add(TileMap(app=self, api=self.logic))
        self.panel = self.add(Panel(
            control_buttons=[get_control_button(c) for c in controls]))
        self.panel.set_size(hx=0.5)
        for control, callback, key in controls:
            if key is None:
                continue
            self.im.register(control, key, callback=lambda *a, c=callback: c())
        self.update_widgets()

    def reset_logic(self):
        logger('Resetting logic...')
        self.root.clear_widgets()
        self.im.clear_all(app_control_defaults=True)
        self.logic = self.__logic_cls()
        self.make_widgets()

    def update_widgets(self):
        self.panel.set_text(self.logic.get_match_state())
        self.map.update()

    def mainloop_hook(self, dt):
        self.logic.update()
        self.update_widgets()

    def debug(self, *a):
        logger('GUI DEBUG')
        self.map.debug()
