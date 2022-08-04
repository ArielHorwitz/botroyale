from typing import Optional
from collections import namedtuple
import itertools
import random
import numpy as np
from logic.state import State
from api.logging import logger
from util.settings import Settings
from util.hexagon import Hex


DEFAULT_MAP_NAME = Settings.get('map.selected_map', 'danger')


class MapGenerator:
    radius = 5
    def __init__(self):
        self.center = Hex(0, 0)
        self.empty_tiles = list(set(self.center.range(self.radius-1)) - {self.center, *self.center.neighbors})
        random.shuffle(self.empty_tiles)
        self.pits = set()
        self.walls = set()
        self.spawns = []
        self.make_map()

    def add_spawn(self, tile):
        self.spawns.append(tile)
        if tile in self.empty_tiles:
            self.empty_tiles.remove(tile)
        self.validate_map()

    def add_pit(self, tile):
        self.pits.add(tile)
        if tile in self.empty_tiles:
            self.empty_tiles.remove(tile)
        self.validate_map()

    def add_wall(self, tile):
        self.walls.add(tile)
        if tile in self.empty_tiles:
            self.empty_tiles.remove(tile)
        self.validate_map()

    def make_map(self):
        pass

    def validate_map(self):
        assert not set(self.spawns) & self.pits
        assert not set(self.spawns) & self.walls
        assert not self.pits & self.walls

    def get_state(self):
        self.validate_map()
        return State(
            death_radius=self.radius+2,
            positions=self.spawns,
            pits=self.pits,
            walls=self.walls,
            )


class EmptyMap(MapGenerator):
    spawn_count = 12

    def make_map(self):
        # Spawns
        spawn_options = list(self.center.ring(self.radius-1))
        assert len(spawn_options) >= self.spawn_count
        random.shuffle(spawn_options)
        for s in spawn_options[:self.spawn_count]:
            self.add_spawn(s)


class BasicMap(MapGenerator):
    radius = 10
    pit_freq = 0.075
    wall_freq = 0.15
    spawn_count = 12

    def make_map(self):
        # Spawns
        spawn_options = list(self.center.ring(self.radius-1))
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


class ClassicMap(MapGenerator):
    radius = 15
    spawn_count = 12

    def make_map(self):
        # Spawns
        spawns = Hex(6, -14), Hex(-6, -14), Hex(3, -14), Hex(-3, -14)
        walls = set()
        radial_walls = list(self.center.straight_line(Hex(0, -1), max_distance=self.radius-1))
        radial_walls = set(w for i, w in enumerate(radial_walls[1:]) if i%4 != 2)
        walls |= radial_walls
        jebait_corridor = {
            Hex(-2, -12), Hex(-1, -12), Hex(0, -12), Hex(1, -12), Hex(2, -12),
            Hex(-2, -14), Hex(-1, -14), Hex(0, -14), Hex(1, -14), Hex(2, -14),
        }
        walls |= jebait_corridor
        walls.add(Hex(0, -8))

        pits = set()
        pits |= {Hex(-2, -6), Hex(-1, -6), Hex(1, -6), Hex(2, -6)}
        pits |= {Hex(-5, -12), Hex(-4, -12), Hex(4, -12), Hex(5, -12)}
        pits |= {Hex(-2, -9), Hex(-1, -10), Hex(0, -10), Hex(1, -10), Hex(1, -9)}

        for rot in range(6):
            for spawn in spawns:
                self.add_spawn(spawn.rotate(rot))
            for pit in pits:
                self.add_pit(pit.rotate(rot))
            for wall in walls:
                self.add_wall(wall.rotate(rot))

        for rpit in range(15):
            self.add_pit(self.empty_tiles.pop(0))
        for rwall in range(15):
            self.add_wall(self.empty_tiles.pop(0))


class DangerMap(MapGenerator):
    radius = 12
    random_radius = 10

    pits_spiral_start_pos = Hex(0, 0)
    pits_spiral_line_sizes = (2, 3, 5, 8)
    pits_gap_prob = 0.075

    walls_spiral_start_pos = Hex(0, 0)
    walls_spiral_line_sizes = (2, 3, 5, 8)
    walls_gap_prob = 0.05

    def make_map(self):
        # Spawns
        spawns = Hex(0, -10), Hex(5, -10)
        for rot in range(6):
            for spawn in spawns:
                spawn_tile = spawn.rotate(rot)
                safe_tiles = spawn_tile.neighbors
                self.empty_tiles = [t for t in self.empty_tiles if t not in safe_tiles]
                self.add_spawn(spawn_tile)

        center_pits = [Hex(0, -1), Hex(-1, 0), Hex(0, 1), Hex(-4, 3), Hex(-4, 1),
                       Hex(2, 3), Hex(4, 2), Hex(1, -4), Hex(-1, -5)]
        for pit in center_pits:
            self.add_pit(pit)

        spiral_pits = self.spiral_calc(self.pits_spiral_start_pos,
                                       self.pits_spiral_line_sizes,
                                       False,
                                       self.pits_gap_prob
                                       )
        spiral_walls = self.spiral_calc(self.walls_spiral_start_pos,
                                        self.walls_spiral_line_sizes,
                                        True,
                                        self.walls_gap_prob
                                        )
        for rot in range(3):
            for pit in spiral_pits:
                pit_pos = pit.rotate(rot * 2)
                if pit_pos in self.empty_tiles:
                    self.add_pit(pit_pos)

            for wall in spiral_walls:
                wall_pos = wall.rotate((rot * 2))
                if wall_pos in self.empty_tiles:
                    self.add_wall(wall_pos)

        random_tile_options = [t for t in self.empty_tiles if t.get_distance(Hex(0, 0)) >= self.random_radius]
        if len(random_tile_options) > 40:
            for rpit in range(15):
                self.add_pit(random_tile_options.pop(0))
            for rwall in range(15):
                self.add_wall(random_tile_options.pop(0))

    def spiral_calc(self, start_pos=Hex(0, 0), line_sizes=(2, 3, 5, 8),
                    inverse=False, gap_prob=0.2):
        spiral = set()
        pos = start_pos
        for n_index in range(len(line_sizes)):
            current_neighbor = pos.neighbors[((6 - n_index) if inverse else n_index) % 6]
            spiral.add(current_neighbor)
            for tile in pos.straight_line(current_neighbor, line_sizes[n_index] - 1):
                if tile not in self.spawns and gap_prob < random.random():
                    spiral.add(tile)
                pos = tile
        return spiral


MAPS = {
    'danger': DangerMap,
    'classic': ClassicMap,
    'basic': BasicMap,
    'giant': GiantMap,
    'empty': EmptyMap,
}
logger('\n'.join([f'Available maps:', *(f'- {m}' for m in MAPS.keys())]))

def get_map_state(map_name: Optional[str] = None) -> State:
    """Returns the initial state of `map_name`.

    `map_name` defaults to the name configured in settings.
    """
    if map_name is None:
        map_name = DEFAULT_MAP_NAME
    map_generator = MAPS[map_name]()
    return map_generator.get_state()
