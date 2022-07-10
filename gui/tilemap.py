import math
import random
import itertools
from pathlib import Path
import numpy as np
from gui import kex, center_sprite, FONT, logger
import gui.kex.widgets as widgets
from util.settings import Settings
from util.hexagon import Hex, WIDTH_HEIGHT_RATIO


MAX_MAP_TILES = Settings.get('tilemap.max_draw_tiles', 2500)
TILE_RADIUS = Settings.get('tilemap._tile_radius', 20)
TILE_PADDING = Settings.get('tilemap._tile_padding', 10)
MAX_TILE_RADIUS = Settings.get('tilemap.max_tile_radius', 200)
UNIT_SIZE = Settings.get('tilemap.unit_size', 0.55)
FONT_SIZE = Settings.get('tilemap.font_size', 12)
HEX_PNG = str(Path.cwd() / 'assets' / 'hex.png')
UNIT_PNG = str(Path.cwd() / 'assets' / 'unit.png')
VFX_DIR = Path.cwd() / 'assets' / 'vfx'


class TileMap(widgets.RelativeLayout):
    def __init__(self, app, api, **kwargs):
        super().__init__(**kwargs)
        self.__current_grid = 0, 0, 0  # tile_radius, canvas_width, canvas_height
        self.__tile_radius = TILE_RADIUS  # in pixels, to hexagon corner
        self.__tile_padding = TILE_PADDING  # in percent of tile radius
        self.real_center = Hex(0, 0)
        self.get_tile_info = api.get_gui_tile_info
        self.get_vfx = api.flush_vfx
        self.get_logic_time = api.get_time
        self.tiles = {}
        self.visible_tiles = set()
        self.__vfx = set()
        self._create_grid()
        self.bind(size=self._resize)
        self.bind(on_touch_down=self.scroll_wheel)
        app.im.register('pan_up', key='w', callback=lambda *a: self.pan(y=1))
        app.im.register('pan_down', key='s', callback=lambda *a: self.pan(y=-1))
        app.im.register('pan_right', key='d', callback=lambda *a: self.pan(x=1))
        app.im.register('pan_left', key='a', callback=lambda *a: self.pan(x=-1))
        app.im.register('pan_up2', key='+ w', callback=lambda *a: self.pan(y=1, zoom_scale=True))
        app.im.register('pan_down2', key='+ s', callback=lambda *a: self.pan(y=-1, zoom_scale=True))
        app.im.register('pan_right2', key='+ d', callback=lambda *a: self.pan(x=1, zoom_scale=True))
        app.im.register('pan_left2', key='+ a', callback=lambda *a: self.pan(x=-1, zoom_scale=True))
        app.im.register('reset_map', key='home', callback=self.reset_view)
        app.im.register('map_zoom_in', key='pageup', callback=self.zoom_in)
        app.im.register('map_zoom_out', key='pagedown', callback=self.zoom_out)
        app.im.register('clear_vfx', key='^+ c', callback=self.clear_vfx)

    def scroll_wheel(self, w, m):
        if not self.collide_point(*m.pos):
            return False
        if m.button == 'scrollup':
            self.zoom_out()
            return True
        elif m.button == 'scrolldown':
            self.zoom_in()
            return True
        return False

    def pan(self, x=0, y=0, zoom_scale=False):
        if zoom_scale:
            cols, rows = self.axis_sizes
            x = int(x * cols / 6)
            y = int(y * rows / 6)
        x *= 2
        y *= 2
        self.real_center -= Hex(x, y)
        self.__reposition_vfx()

    def reset_view(self, *a):
        self.real_center = Hex(0, 0)
        self._adjust_zoom()

    def zoom_in(self, *a):
        self._adjust_zoom(3/2)

    def zoom_out(self, *a):
        self._adjust_zoom(2/3)

    def _resize(self, w, size):
        widgets.kvClock.schedule_once(lambda *a: self._create_grid(), 0)

    def _create_grid(self):
        tile_radius = self.tile_radius
        tile_radius_padded = self.tile_radius_padded

        # We can check if the tiles need to change at all
        new_grid = tile_radius_padded, *self.size
        if new_grid == self.__current_grid:
            return
        self.__current_grid = new_grid

        tile_size = self.__get_tile_size(tile_radius)
        cols, rows = self.__get_axis_sizes(tile_radius_padded)
        half_cols, half_rows = int(cols / 2), int(rows / 2)
        screen_center = self.screen_center

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
            tile_pos = hex.pixels(tile_radius_padded) + screen_center
            self.tiles[hex].reset(tile_pos, tile_size)
        logger(f'Recreated tile map with {cols+1} × {rows} = {len(currently_visible)} tiles. Radius: {tile_radius_padded:.1f} ({tile_radius:.1f} + {self.__tile_padding}% padding) size: {tile_size}')

    @property
    def tile_radius(self):
        return self.__tile_radius

    @property
    def tile_radius_padded(self):
        return self.__tile_radius * (100 + self.__tile_padding) / 100

    @property
    def axis_sizes(self):
        cols, rows = self.__get_axis_sizes(self.tile_radius_padded)
        # We add one more column which is added by _create_grid to account for
        # horizontal offset of every other row
        return cols+1, rows

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

    @staticmethod
    def __get_tile_and_neighbors_size(radius):
        return radius * 6 * WIDTH_HEIGHT_RATIO, radius * 5

    def _adjust_zoom(self, d=None):
        if d is None:
            new_radius = TILE_RADIUS
        else:
            new_radius = self.__tile_radius * d
        minimum_radius = self.__get_minimum_radius(self.size)
        if new_radius < minimum_radius:
            logger(f'Cannot zoom out any more.')
            new_radius = minimum_radius
        if new_radius > MAX_TILE_RADIUS:
            logger(f'Cannot zoom in any more.')
            new_radius = MAX_TILE_RADIUS
        self.__tile_radius = new_radius
        self._create_grid()
        self.__reposition_vfx()

    @property
    def screen_center(self):
        return np.asarray(self.size) / 2

    def update(self):
        center = self.real_center
        get_tile_info = self.get_tile_info
        for hex in self.tiles:
            real_hex = hex - center
            self.tiles[hex].update(get_tile_info(real_hex))
        for vfx_kwargs in self.get_vfx():
            self.add_vfx(*vfx_kwargs)
        logic_time = self.get_logic_time()
        for vfx in list(self.__vfx):
            if vfx.expiration <= logic_time:
                logger(f'Found expired VFX {vfx.expiration} >= {logic_time} {vfx}')
                self.__remove_vfx(vfx)

    def real2tile(self, real_hex):
        return self.real_center + real_hex

    def real2pix(self, real_hex):
        tile = self.real2tile(real_hex)
        tile_pos = tile.pixels(self.tile_radius_padded) + self.screen_center
        return tile_pos

    def add_vfx(self, vfx_name, hex, neighbor=None, time=1):
        if neighbor is None:
            neighbor = hex.neighbors[0]
        assert neighbor in hex.neighbors
        rotation = -60 * hex.neighbors.index(neighbor)
        expiration = self.get_logic_time() + time
        vfx = VFX(hex,
            expiration=expiration,
            rotation=rotation,
            source=str(VFX_DIR / f'{vfx_name}.png'),
            )
        self.__reposition_vfx_single(vfx)
        logger(f'Adding VFX: {vfx} @ {hex} -> {neighbor} with pos: {vfx.pos_center} rotation: {rotation} for {time:.3f} seconds')
        self.__vfx.add(vfx)
        self.canvas.after.add(vfx)

    def clear_vfx(self, *a):
        all_vfx = list(self.__vfx)
        for vfx in all_vfx:
            self.__remove_vfx(vfx)

    def __remove_vfx(self, vfx):
        logger(f'Removing VFX: {vfx}')
        self.canvas.after.remove(vfx)
        self.__vfx.remove(vfx)

    def __reposition_vfx(self):
        size = self.__get_tile_and_neighbors_size(self.tile_radius_padded)
        for vfx in self.__vfx:
            vfx.reset(self.real2pix(vfx.hex), size)

    def __reposition_vfx_single(self, vfx):
        vfx.reset(
            pos=self.real2pix(vfx.hex),
            size=self.__get_tile_and_neighbors_size(self.tile_radius_padded)
            )

    def debug(self):
        pix = self.real2pix(Hex(0, 0))
        vfx_hex = Hex(random.randint(0, 5), random.randint(0, 5))
        vfx_neighbor = random.choice(vfx_hex.neighbors)
        vfx_action = random.choice(('move', 'push'))
        self.add_vfx(vfx_action, vfx_hex, vfx_neighbor)
        logger('\n'.join([
            f'Map center in pixel coords: {pix}',
            f'Tile map size: {self.axis_sizes} = {len(self.visible_tiles)} tiles',
            f'Tile radius: {self.tile_radius_padded:.3f} ({self.tile_radius:.3f} + {self.__tile_padding:.3f}% padding)',
            f'Tile size: {self.__get_tile_size(self.tile_radius)}',
            f'Tile size padded: {self.__get_tile_size(self.tile_radius_padded)}',
            f'VFX size (padded): {self.__get_tile_and_neighbors_size(self.tile_radius_padded)}',
            f'VFX count: {len(self.__vfx)}',
        ]))


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


class VFX(widgets.kvInstructionGroup):
    def __init__(self, hex, source, expiration, rotation=0, pos=None, size=None, **kwargs):
        super().__init__(**kwargs)
        self.expiration = expiration
        self.pos_center = 0, 0
        self.hex = hex
        self.add(widgets.kvColor(1, 1, 1, 1))
        self.add(widgets.kvPushMatrix())
        self.rot = widgets.kvRotate(angle=rotation)
        self.add(self.rot)
        self.rect = widgets.kvRectangle(source=source)
        self.add(self.rect)
        self.add(widgets.kvPopMatrix())
        if pos and size:
            self.reset(pos, size)

    def reset(self, pos, size):
        self.pos_center = pos
        self.rot.origin = pos
        self.rect.size = size
        self.rect.pos = center_sprite(pos, size)
