import random
from gui import kex
import gui.kex.widgets as widgets


FPS = 20
TURN_CAP = 1_000_000
COLORS = [
    (0.6, 0.1, 0.1),
    (0.1, 0.6, 0.1),
    (0.1, 0.3, 0.8),
    (0.5, 0.1, 0.8),
    (0.1, 0.6, 0.8),
    (0.7, 0.5, 0.1),
]
random.shuffle(COLORS)


class App(widgets.App):
    def __init__(self, logic_api, **kwargs):
        super().__init__(**kwargs)
        assert hasattr(logic_api, 'map_size')
        assert hasattr(logic_api, 'next_turn')
        assert hasattr(logic_api, 'game_over')
        assert hasattr(logic_api, 'positions')
        assert hasattr(logic_api, 'get_map_state')
        self.logic = logic_api
        self.autoplay = False
        self.make_widgets()
        self.im = widgets.InputManager(app_control_defaults=True, logger=print)
        self.im.register('toggle_autoplay', key='spacebar', callback=lambda *a: self.toggle_autoplay())
        self.hook_mainloop(FPS)

    def make_widgets(self):
        self.root.orientation = 'vertical'
        controls = self.add(widgets.BoxLayout())
        controls.set_size(y=30)
        controls.add(widgets.Button(text='Next turn', on_release=self.next_turn))
        self.autoplay_widget = controls.add(widgets.ToggleButton(text='Autoplay'))
        self.autoplay_widget.bind(state=lambda w, *a: self._set_autoplay(w.active))
        controls.add(widgets.Button(text='Play all', on_release=self.play_all))
        controls.add(widgets.Button(text='Restart', on_release=lambda *a: kex.restart_script()))
        controls.add(widgets.Button(text='Quit', on_release=lambda *a: quit()))

        window = self.add(widgets.BoxLayout())
        self.main_text = window.add(widgets.Label(valign='top', halign='left'))
        self.main_text.set_size(hx=0.5)
        self.map = window.add(Map(map_size=self.logic.map_size))

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
        while not self.logic.game_over and count < TURN_CAP:
            count += 1
            self.logic.next_turn()

    def mainloop_hook(self, dt):
        if self.autoplay:
            self.next_turn()
        self.main_text.text = self.logic.get_map_state()
        self.map.update(self.logic.positions)


class Map(widgets.AnchorLayout):
    DEFAULT_CELL_BG = (0.2, 0.2, 0.2)
    def __init__(self, map_size, **kwargs):
        super().__init__(**kwargs)
        self.map_size = rows, cols = map_size
        assert isinstance(rows, int)
        assert isinstance(cols, int)
        self.grid_cells = []
        map_grid = self.add(widgets.GridLayout(cols=cols))
        for y in range(rows):
            self.grid_cells.append([])
            for x in range(cols):
                cell_anchor = widgets.AnchorLayout()
                cell_anchor.padding = 2, 2
                cell = cell_anchor.add(widgets.Label())
                map_grid.add(cell_anchor)
                cell.make_bg(self.DEFAULT_CELL_BG)
                self.grid_cells[-1].append(cell)

    def clear_cells(self):
        for row in self.grid_cells:
            for cell in row:
                cell.text = ''
                cell.make_bg(self.DEFAULT_CELL_BG)

    def update(self, positions):
        self.clear_cells()
        for i, pos in enumerate(positions):
            x, y = pos
            self.grid_cells[y][x].text = f'{i}'
            self.grid_cells[y][x].make_bg(COLORS[i%len(COLORS)])