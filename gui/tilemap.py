from collections import namedtuple
from pathlib import Path
import numpy as np
from gui import kex
import gui.kex.widgets as widgets
from api.logic import EventDeath
from util.settings import Settings
from util.hexagon import Hex, WIDTH_HEIGHT_RATIO


MAX_MAP_RADIUS = 20
MIN_TILE_RADIUS = 10
MAX_TILE_RADIUS = 200
TILE_RADIUS = Settings.get('map_tile_radius', 50)
assert MIN_TILE_RADIUS <= TILE_RADIUS <= MAX_TILE_RADIUS
TILE_PADDING = Settings.get('map_tile_padding', 5)
UNIT_SIZE = Settings.get('map_unit_size', 0.65)
HEX_PNG = str(Path.cwd() / 'assets' / 'hex.png')
UNIT_PNG = str(Path.cwd() / 'assets' / 'unit.png')


TileInfo = namedtuple('TileInfo', ['bg_color', 'bg_text', 'fg_color', 'fg_text'])


class TileMap(widgets.RelativeLayout):
    def __init__(self, get_center, get_tile_info, **kwargs):
        super().__init__(**kwargs)
        self.__mid_zoom = False
        self.tile_radius = round(TILE_RADIUS)
        self.get_center = get_center
        self.get_tile_info = get_tile_info
        self.tiles = {}
        self.recreate_grid()
        self.bind(size=self.recreate_grid, pos=self.recreate_grid)

    def recreate_grid(self, *a):
        if not self.__mid_zoom:
            print(f'Adjusting tile map...')
            self.__mid_zoom = True
            widgets.kvClock.schedule_once(self._do_create_grid, 0.5)

    def _do_create_grid(self, *a):
        print(f'Recreating tile map...')
        tile_radius = self.tile_radius
        half_rows = int(self.height / (tile_radius * 2) / 2) + 2
        half_rows = min(MAX_MAP_RADIUS, max(1, half_rows))
        half_cols = int(self.width / (tile_radius * 2) / 2) + 1
        half_cols = min(MAX_MAP_RADIUS, max(1, half_cols))
        tile_size = tile_radius * 2 * WIDTH_HEIGHT_RATIO, tile_radius * 2
        self.clear_widgets()
        self.tiles = {}
        for c in range(-half_cols, half_cols+1):
            for r in range(-half_rows, half_rows+1):
                tile = self.add(Tile(Hex(c, r)))
                self.tiles[tile.offset] = tile
                tile.set_size(*tile_size)
        widgets.kvClock.schedule_once(lambda *a, r=tile_radius: self._reposition_tiles(r), 0)

    def _reposition_tiles(self, tile_radius):
        tile_size = tile_radius * 2 * WIDTH_HEIGHT_RATIO, tile_radius * 2
        pix_center = np.asarray(self.center) - np.asarray(tile_size)/2
        padded_radius = tile_radius + TILE_PADDING
        for tile_offset, tile in self.tiles.items():
            pix_offset = tile_offset.pixels(padded_radius)
            new_pos = pix_center + pix_offset
            tile.pos = tuple(round(_) for _ in new_pos)
        self.update()
        self.__mid_zoom = False
        print(f'Recreated tile map.')

    def adjust_zoom(self, d=None):
        new_radius = TILE_RADIUS
        if d is not None:
            new_radius = max(MIN_TILE_RADIUS, min(MAX_TILE_RADIUS, self.tile_radius*d))
        self.tile_radius = round(new_radius)
        self.recreate_grid()

    def update(self):
        center = self.get_center()
        for hex_offset, tile in self.tiles.items():
            real_hex = hex_offset - center
            tile.update(self.get_tile_info(real_hex))


class Tile(widgets.AnchorLayout):
    def __init__(self, offset, **kwargs):
        self.offset = offset
        super().__init__(**kwargs)
        self.hexagon = self.add(widgets.Widget())
        self.hexagon.make_bg((0,0,0,0), source=HEX_PNG)
        self.hex_label = self.add(widgets.MLabel())
        self.unit = self.add(widgets.Widget())
        self.unit.set_size(hx=UNIT_SIZE, hy=UNIT_SIZE)
        self.unit.make_bg((0,0,0,0), source=UNIT_PNG)
        self.unit_label = self.add(widgets.MLabel())

    def update(self, info):
        self.hexagon.make_bg(info.bg_color)
        self.hex_label.text = info.bg_text
        self.unit.make_bg(info.fg_color)
        self.unit_label.text = info.fg_text
