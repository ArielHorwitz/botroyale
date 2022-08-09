from pathlib import Path
from util.settings import Settings
from util.time import RateCounter
from gui import kex, logger
import gui.kex.widgets as widgets
from api.logging import logger as glogger
from api.gui import GuiControlMenu, GuiControl, gui_control_menu_extend
from gui.panel import Panel, MenuBar
from gui.tilemap import TileMap
from logic.battle_manager import BattleManager


ICON = str(Path.cwd() / 'icon.ico')
# User-configurable settings
FPS = Settings.get('gui._fps', 60)
WINDOW_SIZE = Settings.get('gui._window_size', [1280, 720])
START_MAXIMIZED = Settings.get('gui._window_maximize', True)
LOG_HOTKEYS = Settings.get('logging.hotkeys', False)


class App(widgets.App):
    def __init__(self, **kwargs):
        logger('Starting app...')
        super().__init__(**kwargs)
        self.title = 'Bot Royale'
        self.icon = ICON
        kex.resize_window(WINDOW_SIZE)
        if START_MAXIMIZED:
            widgets.kvWindow.maximize()
        self.fps_counter = RateCounter(sample_size=FPS, starting_elapsed=1000/FPS)
        self.im = widgets.InputManager(
            logger=glogger if LOG_HOTKEYS else lambda *a: None)
        self.reset_logic()
        self.hook_mainloop(FPS)
        logger('GUI initialized.')

    def make_widgets(self):
        self.panel = Panel()
        self.map = TileMap(app=self, api=self.logic)
        # Collect menu bar items
        controls = [
            GuiControlMenu('App', [
                GuiControl('New battle', self.reset_logic, '^ n'),
                GuiControl('Restart', kex.restart_script, '^+ w'),
                GuiControl('Quit', quit, '^+ q'),
            ]),
            GuiControlMenu('Debug', [
                GuiControl('GUI debug', self.debug, '^+ g'),
            ]),
        ]
        gui_control_menu_extend(controls, self.logic.get_controls())
        gui_control_menu_extend(controls, self.map.get_controls())
        # Widgets
        vertical_splitter = self.add(widgets.FlipZIndex(orientation='vertical'))
        self.bar = vertical_splitter.add(MenuBar(controls))
        horizontal_splitter = vertical_splitter.add(widgets.FlipZIndex(orientation='horizontal'))
        horizontal_splitter.add(self.panel)
        self.panel.set_size(hx=0.5)
        horizontal_splitter.add(self.map)
        # Hotkeys
        for submenu, subcontrols in controls:
            for control, callback, key in subcontrols:
                if key is None:
                    continue
                self.im.register(control, key, callback=lambda *a, c=callback: c())
        # Update
        self.update_widgets()

    def reset_logic(self):
        logger('Resetting logic...')
        self.root.clear_widgets()
        self.im.clear_all()
        self.logic = BattleManager(gui_mode=True)
        self.make_widgets()

    def update_widgets(self):
        self.panel.set_text(self.logic.get_info_panel_text())
        self.panel.make_bg(self.logic.get_info_panel_color())
        self.map.update()
        self.bar.set_text(f'{self.fps_counter.rate:.2f} FPS')

    def mainloop_hook(self, dt):
        self.fps_counter.tick()
        self.logic.update()
        self.update_widgets()

    def debug(self, *a):
        logger('GUI DEBUG')
        self.map.debug()
