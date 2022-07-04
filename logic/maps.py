from collections import namedtuple
import itertools
import random
import numpy as np
from util.settings import Settings
from util.hexagon import Hex


RNG = np.random.default_rng()
MapGen = namedtuple('Map', ['radius', 'spawns', 'pits', 'walls'])
SELECTED_MAP_NAME = Settings.get('map.selected_map', 'basic')


class Map:
    radius = 5
    def __init__(self):
        self.center = Hex(0, 0)
        self.all_tiles = set()
        for _ in range(2, self.radius-1):
            self.all_tiles |= set(self.center.ring(_))
        self.empty_tiles = list(self.all_tiles)
        random.shuffle(self.empty_tiles)
        self.pits = set()
        self.walls = set()
        self.spawns = []
        self.make_map()

    def add_spawn(self, tile):
        self.spawns.append(tile)
        if tile in self.empty_tiles:
            self.empty_tiles.remove(tile)

    def add_pit(self, tile):
        self.pits.add(tile)
        if tile in self.empty_tiles:
            self.empty_tiles.remove(tile)

    def add_wall(self, tile):
        self.walls.add(tile)
        if tile in self.empty_tiles:
            self.empty_tiles.remove(tile)

    def make_map(self):
        pass

    def get(self):
        assert not set(self.spawns) & self.pits
        assert not set(self.spawns) & self.walls
        assert not self.pits & self.walls
        return MapGen(self.radius, self.spawns, self.pits, self.walls)


class EmptyMap(Map):
    spawn_count = 12

    def make_map(self):
        # Spawns
        spawn_options = self.center.ring(self.radius-1)
        assert len(spawn_options) >= self.spawn_count
        random.shuffle(spawn_options)
        for s in spawn_options[:self.spawn_count]:
            self.add_spawn(s)


class BasicMap(Map):
    radius = 10
    pit_freq = 0.075
    wall_freq = 0.15
    spawn_count = 12

    def make_map(self):
        # Spawns
        spawn_options = self.center.ring(self.radius-1)
        assert len(spawn_options) >= self.spawn_count
        random.shuffle(spawn_options)
        for s in spawn_options[:self.spawn_count]:
            self.add_spawn(s)
        # Pits
        pit_count = round(len(self.empty_tiles) * self.pit_freq)
        wall_count = round(len(self.empty_tiles) * self.wall_freq)
        for i in range(pit_count):
            if not self.empty_tiles:
                break
            self.add_pit(self.empty_tiles.pop())
        # Walls
        for i in range(wall_count):
            if not self.empty_tiles:
                break
            self.add_wall(self.empty_tiles.pop())


class GiantMap(BasicMap):
    radius = 25


MAPS = {
    'basic': BasicMap,
    'empty': EmptyMap,
    'giant': GiantMap,
}
print('\n'.join([f'Available maps:', *(f'- {m}' for m in MAPS.keys())]))

def get_map():
    map = MAPS[SELECTED_MAP_NAME]()
    return map.get()
