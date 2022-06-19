import numpy as np
from gui import kex
import gui.kex.widgets as widgets
from api.logic_api import EventDeath

COLORS = [
    (0.6, 0.1, 0.1),
    (0.2, 0.6, 0.1),
    (0.1, 0.3, 0.8),
    (0.5, 0.1, 0.8),
    (0.7, 0.5, 0.1),
    (0.1, 0.7, 0.7),
]
PIT_LABEL = '╔═╗\n╚═╝'
WALL_LABEL = '███\n███'


class Map(widgets.AnchorLayout):
    DEFAULT_CELL_BG = (0.2, 0.2, 0.2)
    def __init__(self, api, **kwargs):
        self.api = api
        super().__init__(**kwargs)
        self.map_size = rows, cols = api.map_size
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

    def update(self):
        self.clear_cells()
        self.update_walls()
        self.update_pits()
        self.update_positions()
        self.handle_events()

    def clear_cells(self):
        for row in self.grid_cells:
            for cell in row:
                cell.text = ''
                cell.make_bg(self.DEFAULT_CELL_BG)

    def handle_events(self):
        for event in self.api.flush_events():
            print(f'Handling event on turn #{self.api.turn_count}: {event}')
            if isinstance(event, EventDeath):
                x, y = self.api.positions[event.unit]
                color = self.get_unit_color(event.unit)
                self.flash_cell(x, y, color)

    def update_walls(self):
        for i, pos in enumerate(self.api.walls):
            x, y = pos
            self.grid_cells[y][x].text = WALL_LABEL
            self.grid_cells[y][x].make_bg((0,0,0))

    def update_pits(self):
        for i, pos in enumerate(self.api.pits):
            x, y = pos
            self.grid_cells[y][x].text = PIT_LABEL
            self.grid_cells[y][x].make_bg((0,0,0))

    def update_positions(self):
        for i, pos in enumerate(self.api.positions):
            if not self.api.alive_mask[i]:
                continue
            x, y = pos
            self.grid_cells[y][x].text = f'{i}'
            self.grid_cells[y][x].make_bg(self.get_unit_color(i))

    def flash_cell(self, x, y, color, remaining=10, alternate=True):
        new_bg = color if alternate else (0,0,0)
        self.grid_cells[y][x].make_bg(new_bg)
        if remaining:
            p = lambda *a: self.flash_cell(x, y, color, remaining-1, not alternate)
            kex.Clock.schedule_once(p, 0.1)

    def get_unit_color(self, i):
        return COLORS[i%len(COLORS)]
