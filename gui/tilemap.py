import math
import itertools
from pathlib import Path
from collections import namedtuple
import numpy as np
from gui import kex, center_sprite, FONT
import gui.kex.widgets as widgets
from api.logic import EventDeath
from util.settings import Settings
from util.hexagon import Hex, WIDTH_HEIGHT_RATIO


MAX_MAP_TILES = Settings.get('map_max_draw_tiles', 2500)
TILE_RADIUS = Settings.get('map_tile_radius', 50)
MAX_TILE_RADIUS = Settings.get('map_max_tile_radius', 1000)
TILE_PADDING = Settings.get('map_tile_padding', 15)
UNIT_SIZE = Settings.get('map_unit_size', 0.65)
FONT_SIZE = Settings.get('map_font_size', 12)
HEX_PNG = str(Path.cwd() / 'assets' / 'hex.png')
UNIT_PNG = str(Path.cwd() / 'assets' / 'unit.png')


TileInfo = namedtuple('TileInfo', ['bg_color', 'bg_text', 'fg_color', 'fg_text'])


class TileMap(widgets.RelativeLayout):
    def __init__(self, get_center, get_tile_info, **kwargs):
        super().__init__(**kwargs)
        self.__creating_grid = False
        self.__current_grid = 0, 0, 0  # tile_radius, canvas_width, canvas_height
        self.tile_radius = round(TILE_RADIUS)
        self.get_center = get_center
        self.get_tile_info = get_tile_info
        self.tiles = {}
        self.visible_tiles = set()
        self._create_grid()
        self.bind(size=self._resize)

    def _resize(self, w, size):
        widgets.kvClock.schedule_once(lambda *a: self._create_grid(), 0)

    def _create_grid(self):
        requested_tile_radius = self.tile_radius
        minimum_radius = self.__get_minimum_radius(self.size)
        tile_radius = max(requested_tile_radius, minimum_radius)

        # We can check if the tiles need to change at all
        new_grid = tile_radius, *self.size
        if new_grid == self.__current_grid:
            return
        self.__current_grid = new_grid

        tile_size = self.__get_tile_size(tile_radius)
        tile_radius *= 1+(TILE_PADDING/100)
        cols, rows = self.__get_axis_sizes(tile_radius)
        half_cols, half_rows = int(cols / 2), int(rows / 2)
        center_offset = np.asarray(self.size) / 2

        # Add / remove tile intruction groups
        visible_tiles_coords = itertools.product(range(-half_cols-1, half_cols+1), range(-half_rows, half_rows+1))
        currently_visible = {Hex(x,y) for x,y in visible_tiles_coords}
        newly_visible = currently_visible - self.visible_tiles
        newly_invisible = self.visible_tiles - currently_visible
        assert len(currently_visible) == (cols+1) * rows
        self.visible_tiles = currently_visible
        for hex in newly_invisible:
            self.canvas.remove(self.tiles[hex])
        for hex in newly_visible:
            if hex not in self.tiles:
                self.tiles[hex] = Tile(bg=HEX_PNG, fg=UNIT_PNG)
            self.canvas.add(self.tiles[hex])
        for hex in currently_visible:
            tile_pos = hex.pixels(tile_radius) + center_offset
            self.tiles[hex].reset(tile_pos, tile_size)
        print(f'Recreated tile map with {len(currently_visible)} tiles.')

    def __get_axis_sizes(self, tile_radius):
        w, h = self.__get_tile_size(tile_radius)
        cols = math.ceil(self.width / w)
        rows = math.ceil(self.height / (h * 3/4))
        # Ensure there is an odd number of cols and rows for center tile
        cols += cols % 2 == 0
        rows += rows % 2 == 0
        return cols, rows

    def __get_minimum_radius(self, pix_size, limit=MAX_MAP_TILES):
        canvas_ratio = pix_size[0] / pix_size[1]
        cols_count = math.sqrt(canvas_ratio * MAX_MAP_TILES)
        radius = pix_size[0] / cols_count / 2
        return radius

    @staticmethod
    def __get_total_tile_count(cols_radius, rows_radius):
        return (int(cols_radius) * 2 + 1) * (int(rows_radius) * 2 + 1)

    @staticmethod
    def __get_tile_size(radius):
        return radius * 2 * WIDTH_HEIGHT_RATIO, radius * 2

    def adjust_zoom(self, d=None):
        if d is None:
            new_radius = TILE_RADIUS
        else:
            new_radius = self.tile_radius * d
        minimum_radius = self.__get_minimum_radius(self.size)
        if minimum_radius > new_radius:
            print(f'Cannot zoom out any more.')
            new_radius = minimum_radius
        if new_radius > MAX_TILE_RADIUS:
            print(f'Cannot zoom in any more.')
            new_radius = MAX_TILE_RADIUS
        self.tile_radius = new_radius
        self._create_grid()

    def update(self):
        center = self.get_center()
        for hex in self.tiles:
            real_hex = hex - center
            self.tiles[hex].update(self.get_tile_info(real_hex))


class Tile(widgets.kvInstructionGroup):
    def __init__(self, bg, fg, size=(5, 5), **kwargs):
        super().__init__(**kwargs)
        self.__pos = 0, 0

        self._bg_color = widgets.kvColor(0,0,0,1)
        self._bg = widgets.kvRectangle(source=bg, size=size)
        self._bg_text_color = widgets.kvColor(0,0,0,0)
        self._bg_text = widgets.kvRectangle(size=size)

        fg_size = size[0] * UNIT_SIZE, size[1] * UNIT_SIZE
        self._fg_color = widgets.kvColor(0,0,0,1)
        self._fg = widgets.kvRectangle(source=fg, size=fg_size)
        self._fg_text_color = widgets.kvColor(0,0,0,0)
        self._fg_text = widgets.kvRectangle(size=fg_size)

        self.add(self._bg_color)
        self.add(self._bg)
        self.add(self._bg_text_color)
        self.add(self._bg_text)
        self.add(self._fg_color)
        self.add(self._fg)
        self.add(self._fg_text_color)
        self.add(self._fg_text)

    def update(self, tile_info):
        # Always set the bg color
        self._bg_color.rgba = (*tile_info.bg_color, 1)

        # Hide bg the text rect if no text is set
        if tile_info.bg_text is None:
            self._bg_text_color.rgba = 0,0,0,0
            bg_text = None
        else:
            self._bg_text_color.rgba = 1,1,1,1
            bg_text = tile_info.bg_text

        # Hide the fg rect if no color is set
        if tile_info.fg_color is None:
            self._fg_color.rgba = 0,0,0,0
        else:
            self._fg_color.rgba = (*tile_info.fg_color, 1)

        # Hide the fg text rect if no text is set
        if not tile_info.fg_text:
            self._fg_text_color.rgba = 0,0,0,0
            fg_text = None
        else:
            self._fg_text_color.rgba = 1,1,1,1
            fg_text = tile_info.fg_text

        # Apply text
        self.set_text(bg_text, fg_text)

    def reset(self, pos, size):
        self.__pos = pos
        self._bg.size = size
        self._bg.pos = center_sprite(pos, size)
        fg_size = size[0] * UNIT_SIZE, size[1] * UNIT_SIZE
        self._fg.size = fg_size
        self._fg.pos = center_sprite(pos, fg_size)
        # Hide the text as its size and position will be updated when set text
        self._bg_text.size = self._fg_text.size = 0, 0

    def set_text(self, bg, fg):
        if fg:
            self._fg_text.texture = t = widgets.text_texture(fg,
                font=FONT, font_size=FONT_SIZE)
            self._fg_text.size = t.size
            self._fg_text.pos = center_sprite(self.__pos, t.size)
            self._bg_text.size = 0, 0
        elif bg:
            self._bg_text.texture = t = widgets.text_texture(bg,
                font=FONT, font_size=FONT_SIZE)
            self._bg_text.size = t.size
            self._bg_text.pos = center_sprite(self.__pos, t.size)
            self._fg_text.size = 0, 0
        else:
            self._bg_text.size = 0, 0
            self._fg_text.size = 0, 0
