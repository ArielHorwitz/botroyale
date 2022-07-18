from util.settings import Settings
from gui import kex, logger
import gui.kex.widgets as widgets
from api.gui import GuiControlMenu, GuiControl, gui_control_menu_extend
from gui.panel import Panel, MenuBar
from gui.tilemap import TileMap


# User-configurable settings
FPS = Settings.get('gui._fps', 60)
WINDOW_SIZE = Settings.get('gui._window_size', [1280, 720])
START_MAXIMIZED = Settings.get('gui._window_maximize', True)
LOG_HOTKEYS = Settings.get('logging.hotkeys', False)


class App(widgets.App):
    def __init__(self, logic_cls, **kwargs):
        logger('Starting app...')
        super().__init__(**kwargs)
        self.title = 'Bot Royale'
        kex.resize_window(WINDOW_SIZE)
        if START_MAXIMIZED:
            widgets.kvWindow.maximize()
        self.__logic_cls = logic_cls
        self.logic = self.__logic_cls()
        self.im = widgets.InputManager(
            logger=print if LOG_HOTKEYS else lambda *a: None)
        self.make_widgets()
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
        self.im.clear_all(app_control_defaults=True)
        self.logic = self.__logic_cls()
        self.make_widgets()

    def update_widgets(self):
        self.panel.set_text(self.logic.get_summary_str())
        self.map.update()

    def mainloop_hook(self, dt):
        self.logic.update()
        self.update_widgets()

    def debug(self, *a):
        logger('GUI DEBUG')
        self.map.debug()
