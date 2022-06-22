from pathlib import Path
import numpy as np
from gui import kex
import gui.kex.widgets as widgets
from api.logic_api import EventDeath
from util.hexagon import Hex

COLORS = [
    (0.6, 0.1, 0.1),
    (0.2, 0.6, 0.1),
    (0.1, 0.3, 0.8),
    (0.5, 0.1, 0.8),
    (0.7, 0.5, 0.1),
    (0.1, 0.7, 0.7),
]


class Map(widgets.AnchorLayout):
    DEFAULT_CELL_BG = (0.25, 0.1, 0)
    DIST_COLORS = [
        (0, 0, 0),
        (1, 0, 0),
        (1, 0.5, 0),
        (0.5, 0.5, 0),
        (0.25, 0.75, 0),
        (0, 0.5, 0.5),
        (0, 0.5, 1),
        (0, 0, 1),
        (1, 0, 1),
        (1, 0, 0.5),
        (0, 0, 0),
    ]

    def __init__(self, api, app, **kwargs):
        self.api = api
        super().__init__(**kwargs)
        self.map_size = rows, cols = api.map_size
        assert isinstance(rows, int)
        assert isinstance(cols, int)
        self.selected_tile = Hex(0, 0)
        self.grid_cells = {}
        frame = self.add(widgets.BoxLayout(orientation='vertical'))
        self.status_bar = frame.add(widgets.Label())
        self.status_bar.set_size(y=30)
        self.map_grid = frame.add(widgets.BoxLayout(orientation='vertical'))
        self.debug_mode = False
        self.make_map()
        app.im.register('toggle_guimap_debug', key='^ m', callback=self.toggle_debug_mode)

    def toggle_debug_mode(self, *a):
        self.debug_mode = not self.debug_mode

    def select_cell(self, w, m, c, r):
        if not w.collide_point(*m.pos) or m.button != 'left':
            return
        self.selected_tile = Hex(c, r)

    def make_map(self):
        rows, cols = self.map_size
        self.map_grid.clear_widgets()
        self.grid_cells = {}
        for r in range(rows):
            row = self.map_grid.add(widgets.BoxLayout())
            if r % 2:
                offset = row.add(widgets.AnchorLayout())
                offset.set_size(hx=0.5)
            for c in range(cols):
                cell_anchor = widgets.AnchorLayout()
                cell_anchor.bind(on_touch_down=lambda w, m, c=c, r=r: self.select_cell(w, m, c, r))
                cell_anchor.padding = 10, 0
                cell = cell_anchor.add(widgets.Label())
                cell.make_bg((1, 1, 1))
                cell._bg.source = str(Path.cwd() / 'assets' / 'hex.png')
                row.add(cell_anchor)
                cell.make_bg(self.DEFAULT_CELL_BG)
                self.grid_cells[(c,r)] = cell
            if not r % 2:
                offset = row.add(widgets.AnchorLayout())
                offset.set_size(hx=0.5)

    def update(self):
        self.clear_cells()
        if not self.debug_mode:
            self.update_walls()
            self.update_pits()
            self.update_positions()
        self.handle_events()

    def clear_cells(self):
        self.status_bar.text = f'{self.selected_tile}'
        for coords, cell in self.grid_cells.items():
            c, r = coords
            tile = Hex(c, r)
            text = ''
            color = self.DEFAULT_CELL_BG
            if self.debug_mode:
                dist = tile.get_distance(self.selected_tile)
                color = self.DIST_COLORS[min(dist, len(self.DIST_COLORS)-1)]
                text = f'{tile.x}, {tile.y}\nD:{dist}'
            cell.text = text
            cell.make_bg(color)

    def handle_events(self):
        for event in self.api.flush_events():
            print(f'Handling event on turn #{self.api.turn_count}: {event}')
            if isinstance(event, EventDeath):
                c, r = self.api.positions[event.unit]
                color = self.get_unit_color(event.unit)
                self.flash_cell(c, r, color)

    def update_walls(self):
        for i, pos in enumerate(self.api.walls):
            x, y = pos
            if (x, y) not in self.grid_cells:
                continue
            self.grid_cells[(x,y)].make_bg((1,1,1))

    def update_pits(self):
        for i, pos in enumerate(self.api.pits):
            x, y = pos
            if (x, y) not in self.grid_cells:
                continue
            self.grid_cells[(x,y)].make_bg((0,0,0))

    def update_positions(self):
        for i, pos in enumerate(self.api.positions):
            if not self.api.alive_mask[i]:
                continue
            x, y = pos
            if (x, y) not in self.grid_cells:
                continue
            self.add_cell_label(x, y, f'<{i}>')
            self.grid_cells[(x,y)].make_bg(self.get_unit_color(i))

    def add_cell_label(self, x, y, label):
        ctext = self.grid_cells[(x,y)].text
        if ctext != '':
            label = f'{ctext}\n{label}'
        self.grid_cells[(x,y)].text = label

    def flash_cell(self, c, r, color, remaining=10, alternate=True):
        new_bg = color if alternate else (0,0,0)
        self.grid_cells[(c,r)].make_bg(new_bg)
        if remaining:
            p = lambda *a: self.flash_cell(c, r, color, remaining-1, not alternate)
            kex.Clock.schedule_once(p, 0.1)

    def get_unit_color(self, i):
        return COLORS[i%len(COLORS)]
