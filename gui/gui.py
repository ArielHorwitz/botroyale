from util.settings import Settings
from gui import kex
import gui.kex.widgets as widgets
from api.logic import BaseLogicAPI
from gui.map import Map


# User-configurable settings
FPS = Settings.get('fps', 5)
WINDOW_SIZE = Settings.get('window_size', [1280, 720])
START_MAXIMIZED = Settings.get('window_maximize', False)
STEP_CAP = Settings.get('gui_step_cap', 1_000_000)
LOG_HOTKEYS = Settings.get('gui_log_hotkeys', False)


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
        self.im.register('next_turn', key='t', callback=lambda *a: self.next_turn())
        self.hook_mainloop(FPS)
        print('GUI initialized.')

    def make_widgets(self):
        self.root.orientation = 'vertical'
        controls = self.add(widgets.BoxLayout())
        controls.set_size(y=45)
        controls.add(widgets.Button(
            text='Next turn ([i]t[/i])', markup=True,
            on_release=self.next_turn,
        ))
        self.autoplay_widget = controls.add(widgets.ToggleButton(
            text='Autoplay ([i]spacebar[/i])', markup=True))
        self.autoplay_widget.bind(state=lambda w, *a: self._set_autoplay(w.active))
        controls.add(widgets.Button(text='Play all', on_release=self.play_all))
        controls.add(widgets.Button(text='Logic debug', on_release=self.logic_debug))
        controls.add(widgets.Button(
            text='Restart ([i]ctrl + w[/i])', markup=True,
            on_release=lambda *a: kex.restart_script(),
        ))
        controls.add(widgets.Button(
            text='Quit ([i]ctrl + q[/i])', markup=True,
            on_release=lambda *a: quit(),
        ))

        window = self.add(widgets.BoxLayout())
        self.map = window.add(Map(api=self.logic, app=self))
        main_text_frame = window.add(widgets.AnchorLayout(
            anchor_x='left', anchor_y='top', padding=(15, 15)))
        main_text_frame.set_size(hx=0.5)
        main_text_frame.make_bg((0.05, 0.2, 0.35))
        self.main_text = main_text_frame.add(
            widgets.Label(valign='top', halign='left'))

    def toggle_autoplay(self, set_to=None):
        if set_to is None:
            set_to = not self.autoplay_widget.active
        self.autoplay_widget.active = set_to

    def _set_autoplay(self, set_to):
        self.autoplay = set_to
        print(f'Auto playing...' if self.autoplay else f'Pausing auto play...')

    def next_turn(self, *args):
        if not self.logic.game_over:
            self.logic.next_turn()

    def play_all(self, *args):
        print('Playing battle to completion...')
        count = 0
        while not self.logic.game_over and count < STEP_CAP:
            count += 1
            self.logic.next_turn()

    def mainloop_hook(self, dt):
        if self.autoplay:
            self.next_turn()
        self.main_text.text = self.logic.get_match_state()
        self.map.update()

    def logic_debug(self, *a):
        self.logic.debug()
