from pathlib import Path
import numpy as np
from gui import kex
from gui.tilemap import TileMap, TileInfo
import gui.kex.widgets as widgets
from api.logic import EventDeath
from util.settings import Settings
from util.hexagon import Hex


DEFAULT_CELL_BG = Settings.get('map_default_cell_color', (0.25, 0.1, 0))
WALL_COLOR = Settings.get('map_wall_color', (1,1,1))
PIT_COLOR = Settings.get('map_pit_color', (0.1,0.1,0.1))
UNIT_COLORS = Settings.get('map_unit_colors', [
    (0.6, 0, 0.1),  # Red
    (0.9, 0.3, 0.4),  # Pink
    (0.8, 0.7, 0.1),  # Yellow
    (0.7, 0.4, 0),  # Orange
    (0.1, 0.4, 0),  # Green
    (0.4, 0.7, 0.1),  # Lime
    (0.1, 0.7, 0.7),  # Teal
    (0.1, 0.4, 0.9),  # Blue
    (0, 0.1, 0.5),  # Navy
    (0.7, 0.1, 0.9),  # Purple
    (0.4, 0, 0.7),  # Violet
    (0.7, 0, 0.5),  # Magenta
])
DIST_COLORS = Settings.get('map_distance_colors', [
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
])


class Map(widgets.AnchorLayout):
    def __init__(self, app, api, **kwargs):
        super().__init__(**kwargs)
        self.api = api
        self.unit_colors = [UNIT_COLORS[ci%len(UNIT_COLORS)] for ci in self.api.unit_colors]
        self.real_center = Hex(0, 0)
        self.tile_layer = self.add(TileMap(
            get_center=self.get_real_center,
            get_tile_info=self.get_tile_info,
            ))
        app.im.register('pan_up', key='w', callback=lambda *a: self.pan(y=2))
        app.im.register('pan_down', key='s', callback=lambda *a: self.pan(y=-2))
        app.im.register('pan_right', key='d', callback=lambda *a: self.pan(x=2))
        app.im.register('pan_left', key='a', callback=lambda *a: self.pan(x=-2))
        app.im.register('pan_up2', key='+ w', callback=lambda *a: self.pan(y=6))
        app.im.register('pan_down2', key='+ s', callback=lambda *a: self.pan(y=-6))
        app.im.register('pan_right2', key='+ d', callback=lambda *a: self.pan(x=6))
        app.im.register('pan_left2', key='+ a', callback=lambda *a: self.pan(x=-6))
        app.im.register('reset_map', key='home', callback=self.reset_view)
        app.im.register('map_zoom_in', key='pageup', callback=self.zoom_in)
        app.im.register('map_zoom_out', key='pagedown', callback=self.zoom_out)

    def get_real_center(self):
        return self.real_center

    def get_tile_info(self, hex):
        has_unit = hex in self.api.positions
        # BG color
        if hex in self.api.pits:
            bg_color = PIT_COLOR
        elif hex in self.api.walls:
            bg_color = WALL_COLOR
        else:
            bg_color = DEFAULT_CELL_BG
        # BG text
        if has_unit:
            bg_text = ''
        else:
            bg_text = ', '.join(str(_) for _ in hex.xy)
        bg_text = ''
        # FG color
        if has_unit:
            unit_id = self.api.positions.index(hex)
            fg_color = self.unit_colors[unit_id]
            fg_text = f'{unit_id}'
        else:
            fg_color = 0, 0, 0, 0
            fg_text = ''
        return TileInfo(
            bg_color=bg_color,
            bg_text=bg_text,
            fg_color=fg_color,
            fg_text=fg_text,
            )

    def pan(self, x=0, y=0):
        self.real_center -= Hex(x, y)

    def reset_view(self, *a):
        self.real_center = Hex(0, 0)
        self.tile_layer.adjust_zoom()

    def zoom_in(self, *a):
        self.tile_layer.adjust_zoom(1.25)

    def zoom_out(self, *a):
        self.tile_layer.adjust_zoom(0.8)

    def update(self):
        self.tile_layer.update()

    def clear_cells(self):
        self.status_bar.text = f'{self.selected_tile}'
        for coords, cell in self.grid_cells.items():
            c, r = coords
            tile = Hex(c, r)
            text = ''
            color = DEFAULT_CELL_BG
            if self.debug_mode:
                dist = tile.get_distance(self.selected_tile)
                color = DIST_COLORS[min(dist, len(DIST_COLORS)-1)]
                text = f'{tile.x}, {tile.y}\nD:{dist}'
            cell.text = text
            cell.make_bg(color)

    def flash_cell(self, c, r, color, remaining=10, alternate=True):
        new_bg = color if alternate else (0,0,0)
        self.grid_cells[(c,r)].make_bg(new_bg)
        if remaining:
            p = lambda *a: self.flash_cell(c, r, color, remaining-1, not alternate)
            kex.Clock.schedule_once(p, 0.1)
