import math
import itertools
import numpy as np
from botroyale.gui import kex, center_sprite, logger, ASSETS_DIR
from botroyale.gui.kex import widgets
from botroyale.api.gui import Control
from botroyale.util import settings
from botroyale.util.hexagon import Hex, ORIGIN, WIDTH_HEIGHT_RATIO, SQRT3


ZOOM_RATIO = 3/2
AUTO_ZOOM = settings.get('gui.tilemap.autozoom')
MAX_MAP_TILES = settings.get('gui.tilemap.max_draw_tiles')
TILE_PADDING = settings.get('gui.tilemap.tile_padding')
MAX_TILE_RADIUS = settings.get('gui.tilemap.max_tile_radius')
UNIT_SIZE = settings.get('gui.tilemap.unit_size')
font = settings.get('gui.fonts.tilemap')
FONT = str(ASSETS_DIR / 'fonts' / f'{font}.ttf')
FONT_SCALE = settings.get('gui.tilemap.font_scale')
MAX_FONT_SIZE = settings.get('gui.tilemap.max_font_size')
REDRAW_COOLDOWN = settings.get('gui.tilemap.redraw_cooldown')
SPRITES_DIR = ASSETS_DIR / 'sprites'
VFX_DIR = ASSETS_DIR / 'vfx'
HEX_PNG = str(SPRITES_DIR / 'hex.png')


class TileMap(widgets.RelativeLayout):
    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        self.get_tile_info = api.get_gui_tile_info
        self.get_vfx = api.flush_vfx
        self.get_logic_time = api.get_time
        self.check_clear_vfx_flag = api.clear_vfx_flag
        self.get_map_size_hint = api.get_map_size_hint

        self.__redraw_request = 0
        self.__current_grid = 0, 0, 0  # tile_radius, canvas_width, canvas_height
        self.__size_hint = self.get_map_size_hint()
        self.__tile_radius = MAX_TILE_RADIUS
        self.__tile_padding = 1 + (TILE_PADDING / 100)
        self.real_center = ORIGIN
        assert callable(api.handle_hex_click)
        self.handle_hex_click = api.handle_hex_click
        self.tiles = {}
        self.visible_tiles = set()
        self.__vfx = set()
        self._create_grid()
        self.bind(size=self._resize)
        self.bind(on_touch_down=self.on_touch_down)
        widgets.kvClock.schedule_once(self.reset_view, 1)

    def get_controls(self):
        return {
            'Map': [
                Control('Zoom in', self.zoom_in, '+ pageup'),
                Control('Zoom out', self.zoom_out, '+ pagedown'),
                Control('Reset view', self.reset_view, '+ home'),
                Control('Clear VFX', self.clear_vfx, '^+ c'),
                Control('Pan up', lambda: self.pan(y=1), '+ i'),
                Control('Pan down', lambda: self.pan(y=-1), '+ k'),
                Control('Pan right', lambda: self.pan(x=1), '+ l'),
                Control('Pan left', lambda: self.pan(x=-1), '+ j'),
                Control('Debug', self.debug),
                ],
            }

    def on_touch_down(self, w, m=None):
        if m is None:
            # Not a mouse click
            return
        if not self.collide_point(*m.pos):
            return False
        if m.button == 'scrollup':
            self.zoom_out()
            return True
        elif m.button == 'scrolldown':
            self.zoom_in()
            return True
        else:
            btn = m.button
            pos = np.asarray(m.pos) - self.screen_center
            pos = self.to_widget(*pos, relative=True)
            hex = self.real_center.pixel_position_to_hex(self.tile_radius_padded, pos)
            mods = widgets.get_app().im.currently_pressed_mods
            logger(f'Clicked {btn=} with {mods=} : {pos} -> {hex}')
            self.handle_hex_click(hex, btn, mods=mods)
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
        self.real_center = ORIGIN
        self._adjust_zoom()
        self.__reposition_vfx()

    def zoom_in(self, *a):
        self._adjust_zoom(ZOOM_RATIO)

    def zoom_out(self, *a):
        self._adjust_zoom(1/ZOOM_RATIO)

    def _resize(self, w, size):
        """
        When window is resized, the grid must be recreated.
        However when a window is resized with a mouse drag, we will get size
        for every frame. We don't want to redraw every frame so we set a
        cooldown.
        """
        # Record the redraw request. A new resize will override this one.
        self.__redraw_request += 1
        request = self.__redraw_request
        # Schedule the redraw in REDRAW_COOLDOWN time.
        widgets.kvClock.schedule_once(
            lambda *a: self._resize_redraw(request), REDRAW_COOLDOWN)

    def _resize_redraw(self, redraw_request):
        # Skip redrawing if this request is obsolete (if a new request has been
        # made since).
        if redraw_request != self.__redraw_request:
            return
        self.__tile_radius = self.__tile_radius_from_sizehint(self.__size_hint)
        self._create_grid()

    def _create_grid(self):
        self.__tile_radius = max(self.__tile_radius, self.__get_minimum_radius(self.size))
        self.__tile_radius = min(self.__tile_radius, MAX_TILE_RADIUS)
        tile_radius = self.tile_radius
        tile_radius_padded = self.tile_radius_padded

        # We can check if the tiles need to change at all
        new_grid = tile_radius_padded, *self.size
        if new_grid == self.__current_grid:
            return
        self.__current_grid = new_grid

        screen_center = self.screen_center
        cols, rows = self.__get_axis_sizes_flat(tile_radius_padded)
        tile_size = self.__get_tile_size(tile_radius)

        # Add / remove tile intruction groups
        half_cols, half_rows = int(cols / 2), int(rows / 2)
        visible_tiles_coords = itertools.product(range(-half_cols-1, half_cols+1), range(-half_rows, half_rows+1))
        currently_visible = {Hex(x,y) for x,y in visible_tiles_coords}
        assert len(currently_visible) == (cols+1) * rows
        newly_visible = currently_visible - self.visible_tiles
        newly_invisible = self.visible_tiles - currently_visible
        self.visible_tiles = currently_visible
        for hex in newly_invisible:
            self.canvas.remove(self.tiles[hex])
        for hex in newly_visible:
            if hex not in self.tiles:
                self.tiles[hex] = Tile(bg=HEX_PNG, fg=HEX_PNG)
            self.canvas.add(self.tiles[hex])
        for hex in currently_visible:
            tile_pos = hex.pixel_position(tile_radius_padded) + screen_center
            self.tiles[hex].reset(tile_pos, tile_size)
        logger(f'Recreated tile map with ({cols} + 1) × {rows} = {len(currently_visible)} tiles. Radius: {tile_radius_padded:.2f} ({tile_radius:.2f} * {self.__tile_padding:.2f} padding) size: {tile_size}. Pixel size: {self.size}')
        self.__reposition_vfx()

    @property
    def tile_radius(self):
        return self.__tile_radius

    @property
    def tile_radius_padded(self):
        return self.__tile_radius * self.__tile_padding

    @property
    def axis_sizes(self):
        cols, rows = self.__get_axis_sizes_flat(self.tile_radius_padded)
        # We add one more column which is added by _create_grid to account for
        # horizontal offset of every other row
        return cols+1, rows

    def __get_axis_sizes_flat(self, tile_radius):
        """
        Get size of map that will fit given a tile radius.
        Includes tiles that are partially visible.
        Does not consider offset of odd rows.
        """
        w, h = self.__get_tile_size(tile_radius)
        cols = math.ceil(self.width / w)
        rows = math.ceil(self.height / (h * 3/4))
        # Ensure there is an odd number of cols and rows for center tile
        cols += cols % 2 == 0
        rows += rows % 2 == 0
        return cols, rows

    def __get_minimum_radius(self, pix_size, limit=MAX_MAP_TILES):
        # Find the smallest radius that will fit at most MAX_MAP_TILES.
        # This is an estimate and will result in a tile count marginally higher
        # than MAX_MAP_TILES.
        # cols = (can_x) / (r * sqrt3)     = canvas_x / tile_x
        # rows = (can_y - r/2) / (r * 1.5) = (canvas_y - first_row_offset) / tile_y
        # max_tiles >= cols * rows
        # Solve for r.
        x, y = pix_size
        t = MAX_MAP_TILES
        radius = 1.3175*10**-8 * (
            1208.59 * math.sqrt(1518005008*t*x*y + 36517525*x**2) -7303505*x
            ) / t
        final_radius = radius / self.__tile_padding
        resulting_size = self.__get_axis_sizes_flat(radius)
        return final_radius

    def __tile_radius_from_sizehint(self, size_hint):
        """
        Finds the radius that will fit size_hint tiles on each side of the
        center tile vertically and horizontally.
        E.g. a size_hint of 5 will result in a radius that will fit at least
        11 x 11 tiles (5 radius * 2 + center tile).
        """
        pix_size = self.size
        diameter_tiles = size_hint * 2 + 1  # radius * 2 + center tile
        # For cols, we need just see how many fit side by side...
        half_tile_width = pix_size[0] / diameter_tiles / 2
        # .. and convert half of tile width to radius
        width_max_radius = 2 * half_tile_width / SQRT3
        # rows = (canvas_y - r/2) / (r * 1.5)
        # r = (2/3 * canvas_y) / (rows + 1/3)
        height_max_radius = (2/3 * pix_size[1]) / (diameter_tiles + 1/3)
        radius = min((width_max_radius, height_max_radius))
        final_radius = radius / self.__tile_padding
        resulting_size = self.__get_axis_sizes_flat(radius)
        return final_radius

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
            new_radius = self.__tile_radius_from_sizehint(self.__size_hint)
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

    @property
    def screen_center(self):
        return np.asarray(self.size) / 2

    def update(self):
        if self.check_clear_vfx_flag():
            self.clear_vfx()
        new_size_hint = self.get_map_size_hint()
        if self.__size_hint != new_size_hint:
            self.__size_hint = new_size_hint
            self.reset_view()
        center = self.real_center
        get_tile_info = self.get_tile_info
        for hex in self.tiles:
            real_hex = hex - center
            self.tiles[hex].update(get_tile_info(real_hex))
        logic_time = self.get_logic_time()
        for vfx_kwargs in self.get_vfx():
            self.add_vfx(**vfx_kwargs.asdict())
        for vfx in list(self.__vfx):
            if logic_time < vfx.start_step or vfx.expire_step <= logic_time:
                logger(f'Found expired VFX {logic_time} < {vfx.start_step} | {vfx.expire_step} <= {logic_time} {vfx}')
                self.__remove_vfx(vfx)

    def real2tile(self, real_hex):
        return self.real_center + real_hex

    def real2pix(self, real_hex):
        tile = self.real2tile(real_hex)
        tile_pos = tile.pixel_position(self.tile_radius_padded) + self.screen_center
        return tile_pos

    def add_vfx(self, name, hex, direction, start_step, expire_step, expire_seconds):
        if direction is None:
            direction = hex.neighbors[0]
        if direction in hex.neighbors:
            # Shortcut for angle of rotation
            rotation = -60 * hex.neighbors.index(direction)
        else:
            # Trigonometry for angle of rotation
            target_vector = direction - hex
            tx, ty = target_vector.pixel_position(radius=1)
            if tx:
                theta = math.atan(ty/tx) + math.pi * (tx < 0)
                rotation = math.degrees(theta)
            else:
                rotation = 90 if ty > 0 else -90
        vfx = VFX(hex,
            start_step=start_step,
            expire_step=expire_step,
            rotation=rotation,
            source=str(VFX_DIR / f'{name}.png'),
            )
        self.__reposition_vfx_single(vfx)
        logger(f'Adding VFX: {vfx} at position: {vfx.pos_center}')
        self.__vfx.add(vfx)
        self.canvas.after.add(vfx)
        if expire_seconds:
            widgets.kvClock.schedule_once(
                lambda *a: self.__remove_vfx(vfx), expire_seconds)

    def clear_vfx(self, *a):
        all_vfx = list(self.__vfx)
        for vfx in all_vfx:
            self.__remove_vfx(vfx)

    def __remove_vfx(self, vfx):
        if vfx not in self.__vfx:
            return
        logger(f'Removing VFX: {vfx}')
        self.canvas.after.remove(vfx)
        self.__vfx.remove(vfx)

    def __reposition_vfx(self):
        # For whatever reason, a Kivy canvas.after group does not adapt to
        # relative layout position, unlike the normal canvas group.
        offset = self.to_window(0, 0, initial=False, relative=True)
        size = self.__get_tile_and_neighbors_size(self.tile_radius_padded)
        for vfx in self.__vfx:
            pos = self.real2pix(vfx.hex) + offset
            vfx.reset(pos, size)

    def __reposition_vfx_single(self, vfx):
        # For whatever reason, a Kivy canvas.after group does not adapt to
        # relative layout position, unlike the normal canvas group.
        pos = self.to_window(*self.real2pix(vfx.hex), initial=False, relative=True)
        size = self.__get_tile_and_neighbors_size(self.tile_radius_padded)
        vfx.reset(pos, size)

    def debug(self):
        logger('\n'.join([
            f'Canvas size: {self.size} Offset: {self.pos} From real2pix: {self.real2pix(ORIGIN)}',
            f'Canvas center: {self.screen_center} to_window: {self.to_window(*self.screen_center, initial=False, relative=True)}',
            f'Tile map size: {self.axis_sizes} = {len(self.visible_tiles)} tiles',
            f'Tile radius: {self.tile_radius:.3f} * {self.__tile_padding:.2f} padding = {self.tile_radius_padded:.3f}',
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
        fg_size = size[0] * UNIT_SIZE, size[1] * UNIT_SIZE
        self._fg_color = widgets.kvColor(0,0,0,1)
        self._fg = widgets.kvRectangle(source=fg, size=fg_size)
        self._text_color = widgets.kvColor(0,0,0,0)
        self._text = widgets.kvRectangle(size=fg_size)

        self.add(self._bg_color)
        self.add(self._bg)
        self.add(self._fg_color)
        self.add(self._fg)
        self.add(self._text_color)
        self.add(self._text)

    def update(self, tile_info):
        # Always set the tile bg sprite
        if tile_info.tile is None:
            self._bg.source = HEX_PNG
        else:
            self._bg.source = str(SPRITES_DIR / f'{tile_info.tile}.png')
        # Always set the bg color
        self._bg_color.rgba = (*tile_info.bg, 1)
        # Set/hide the fg
        if tile_info.color is None:
            self._fg_color.rgba = 0,0,0,0
        else:
            self._fg_color.rgba = (*tile_info.color, 1)
            self._fg.source = str(SPRITES_DIR / f'{tile_info.sprite}.png')
        # Set/hide text
        if not tile_info.text:
            self._text_color.rgba = 0,0,0,0
            fg_text = None
        else:
            self._text_color.rgba = 1,1,1,1
            fg_text = tile_info.text
        self.set_text(fg_text)

    def reset(self, pos, size):
        self.__pos = pos
        self._bg.size = size
        self._bg.pos = center_sprite(pos, size)
        fg_size = size[0] * UNIT_SIZE, size[1] * UNIT_SIZE
        self._fg.size = fg_size
        self._fg.pos = center_sprite(pos, fg_size)
        # Hide the text as its size and position will be updated when set text
        self._text.size = 0, 0

    def set_text(self, text):
        if text is None:
            self._text.size = 0, 0
            return
        font_size = FONT_SCALE * self._bg.size[1] / 2
        font_size = min(font_size, MAX_FONT_SIZE)
        outline_width = font_size / 10
        self._text.texture = t = widgets.text_texture(text,
            font_name=FONT, font_size=font_size, outline_width=outline_width)
        self._text.size = t.size
        self._text.pos = center_sprite(self.__pos, t.size)


class VFX(widgets.kvInstructionGroup):
    def __init__(self,
            hex, source, start_step, expire_step,
            rotation=0, pos=None, size=None,
            **kwargs):
        super().__init__(**kwargs)
        self.start_step = start_step
        self.expire_step = expire_step
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

    def __repr__(self):
        return f'<VFX {self.rect.source} @{self.hex} {round(self.rot.angle)}° x:{self.expire_step}>'
