from pathlib import Path
import math
import numpy as np
from gui import kex
from gui.tilemap import TileMap
import gui.kex.widgets as widgets
from api.logic import EventDeath
from util.hexagon import Hex


class Map(widgets.AnchorLayout):
    def __init__(self, app, api, **kwargs):
        super().__init__(**kwargs)
        self.api = api
        self.real_center = Hex(0, 0)
        self.tile_layer = self.add(TileMap(
            get_center=self.get_real_center,
            get_tile_info=api.get_gui_tile_info,
            ))
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

    def scroll_wheel(self, w, m):
        if m.button == 'scrollup':
            self.zoom_out()
            return True
        elif m.button == 'scrolldown':
            self.zoom_in()
            return True
        return False

    def get_real_center(self):
        return self.real_center

    def pan(self, x=0, y=0, zoom_scale=False):
        if zoom_scale:
            cols, rows = self.tile_layer.axis_sizes
            x = int(x * cols / 6)
            y = int(y * rows / 6)
        x *= 2
        y *= 2
        self.real_center -= Hex(x, y)

    def reset_view(self, *a):
        self.real_center = Hex(0, 0)
        self.tile_layer.adjust_zoom()

    def zoom_in(self, *a):
        self.tile_layer.adjust_zoom(3/2)

    def zoom_out(self, *a):
        self.tile_layer.adjust_zoom(2/3)

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
