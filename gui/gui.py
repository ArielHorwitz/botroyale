from util.settings import Settings
from gui import kex
import gui.kex.widgets as widgets
from api.logic import BaseLogicAPI
from gui.panel import Panel
from gui.map import Map


# User-configurable settings
FPS = Settings.get('gui._fps', 60)
WINDOW_SIZE = Settings.get('gui._window_size', [1280, 720])
START_MAXIMIZED = Settings.get('gui._window_maximize', False)
STEP_CAP = Settings.get('gui.|step_cap', 1_000_000)
LOG_HOTKEYS = Settings.get('gui.log_hotkeys', False)


class App(widgets.App):
    def __init__(self, logic_api, **kwargs):
        print('Starting app...')
        super().__init__(**kwargs)
        self.title = 'Bot Royale'
        self.logger = print if LOG_HOTKEYS else lambda *a: None
        kex.resize_window(WINDOW_SIZE)
        if START_MAXIMIZED:
            widgets.kvWindow.maximize()
        assert isinstance(logic_api, BaseLogicAPI)
        self.logic = logic_api
        self.autoplay = False
        self.im = widgets.InputManager(app_control_defaults=True, logger=self.logger)
        self.make_widgets()
        self.im.register('toggle_autoplay', key='spacebar', callback=lambda *a: self.toggle_autoplay())
        self.im.register('next_step', key='n', callback=lambda *a: self.next_step())
        self.hook_mainloop(FPS)
        print('GUI initialized.')

    def make_widgets(self):
        self.map = self.add(Map(app=self, api=self.logic))
        self.panel = self.add(Panel(control_buttons=(
            ('Autoplay ([i]spacebar[/i])', self.toggle_autoplay),
            ('Next step ([i]n[/i])', self.next_step),
            ('Play all', self.play_all),
            ('Logic debug', self.logic_debug),
            ('Restart ([i]ctrl + w[/i])', kex.restart_script),
            ('Quit ([i]ctrl + q[/i])', quit),
        )))
        self.panel.set_size(hx=0.5)
        self.update_widgets()

    def toggle_autoplay(self, set_to=None):
        if set_to is None:
            set_to = not self.autoplay
        self.autoplay = set_to
        print(f'Auto playing...' if self.autoplay else f'Paused autoplay...')

    def next_step(self, *args):
        if not self.logic.game_over:
            self.logic.next_step()

    def update_widgets(self):
        self.panel.set_text(self.logic.get_match_state())
        self.map.update()

    def play_all(self, *args):
        print('Playing battle to completion...')
        count = 0
        while not self.logic.game_over and count < STEP_CAP:
            count += 1
            self.logic.next_step()

    def mainloop_hook(self, dt):
        if self.autoplay:
            self.next_step()
        self.update_widgets()

    def logic_debug(self, *a):
        self.logic.debug()
