from collections import namedtuple
import itertools
import random
import numpy as np
from util.settings import Settings
from util.hexagon import Hex


RNG = np.random.default_rng()
Map = namedtuple('Map', ['axis_size', 'pits', 'walls', 'spawns'])
SELECTED_MAP_NAME = Settings.get('selected_map', 'basic')
MAP_RADIUS = Settings.get('map_radius', 5)
EDGE_SIZE = Settings.get('edge_size', 2)
SPAWN_COUNT = Settings.get('spawn_count', 8)
SPAWN_RADIUS = Settings.get('spawn_radius', 2)
PIT_COUNT = Settings.get('pit_count', 20)
WALL_COUNT = Settings.get('wall_count', 40)


class Maps:
    @staticmethod
    def small_test_map():
        axis_size = 2
        # Spawns
        spawns = RNG.integers(low=0, high=axis_size - 1, size=(2, 2))
        # Map features
        coords = list(itertools.product(range(axis_size), repeat=2))
        print(coords)
        for spawn in spawns:
            if tuple(spawn) in coords:
                coords.remove(tuple(spawn))
        random.shuffle(coords)
        # Walls
        walls = [coords.pop(0) for _ in range(1)]
        # Pits
        pits = [coords.pop(0) for _ in range(1)]
        # Return the map tuple
        return Map(axis_size, pits, walls, spawns.astype(np.int8))

    @staticmethod
    def random_map():
        axis_size = MAP_RADIUS * 2
        # Map features
        coords = list(itertools.product(range(axis_size), repeat=2))
        random.shuffle(coords)
        # Spawns
        spawns = np.asarray([coords.pop(0) for _ in range(SPAWN_COUNT)])
        # Walls
        walls = [coords.pop(0) for _ in range(WALL_COUNT)]
        # Pits
        pits = [coords.pop(0) for _ in range(PIT_COUNT)]
        # Return the map tuple
        return Map(axis_size, pits, walls, spawns.astype(np.int8))

    @staticmethod
    def empty_map():
        return Map(MAP_RADIUS*2, np.asarray([[1, 0]]), np.asarray([[1, 1]]), np.asarray([[0, 0]]))

    @staticmethod
    def test_color_map():
        spawns = np.asarray([(i, 0) for i in range(SPAWN_COUNT)])
        return Map(SPAWN_COUNT, np.asarray([[0, 1]]), np.asarray([[1, 1]]), spawns)

    @staticmethod
    def basic_map():
        assert MAP_RADIUS >= 2
        assert EDGE_SIZE >= 1
        assert SPAWN_RADIUS <= MAP_RADIUS
        axis_size = (EDGE_SIZE + MAP_RADIUS) * 2 + 1
        spawn_offset = EDGE_SIZE + MAP_RADIUS - SPAWN_RADIUS
        # Spawns
        near = spawn_offset
        mid = axis_size // 2
        far = axis_size - near - 1
        spawns = list(itertools.product([near, mid, far], repeat=2))
        spawns.remove((mid, mid))
        spawns = np.asarray(spawns[:min(len(spawns), SPAWN_COUNT)])
        # Pits
        pit_grid = np.zeros((axis_size, axis_size), dtype=np.bool_)
        pit_edge = [*range(0, EDGE_SIZE), *range(axis_size-1, axis_size-EDGE_SIZE-1, -1)]
        pit_grid[:, pit_edge] = True
        pit_grid[pit_edge, :] = True
        random_pits = RNG.integers(low=0, high=axis_size, size=(2, PIT_COUNT))
        pit_grid[random_pits[0], random_pits[1]] = True
        # Prevent pits generating at spawn points
        pit_grid[spawns[:, 0], spawns[:, 1]] = False
        pits = np.dstack(np.nonzero(pit_grid))[0]
        # Walls
        wall_grid = np.zeros((axis_size, axis_size), dtype=np.bool_)
        random_walls = RNG.integers(low=0, high=axis_size, size=(2, WALL_COUNT))
        wall_grid[random_walls[0], random_walls[1]] = True
        # Prevent walls generating at spawn points or pits
        wall_grid[spawns[:, 0], spawns[:, 1]] = False
        wall_grid[np.nonzero(pit_grid)] = False
        walls = np.dstack(np.nonzero(wall_grid))[0]
        # Return the map tuple
        return Map(axis_size, pits, walls, spawns)


    @staticmethod
    def another_basic_map():
        assert MAP_RADIUS >= 2
        assert EDGE_SIZE >= 1
        assert SPAWN_RADIUS <= MAP_RADIUS
        axis_size = (EDGE_SIZE + MAP_RADIUS) * 2 + 1
        spawn_offset = EDGE_SIZE + MAP_RADIUS - SPAWN_RADIUS
        # Spawns
        near = spawn_offset
        mid = axis_size // 2
        far = axis_size - near - 1
        spawns = list(itertools.product([near, mid, far], repeat=2))
        spawns.remove((mid, mid))
        spawns = np.asarray(spawns[:min(len(spawns), SPAWN_COUNT)])
        # Pits
        pit_grid = np.zeros((axis_size, axis_size), dtype=np.bool_)
        pit_edge = [*range(0, EDGE_SIZE), *range(axis_size-1, axis_size-EDGE_SIZE-1, -1)]
        pit_grid[:, pit_edge] = True
        pit_grid[pit_edge, :] = True
        random_pits = RNG.integers(low=0, high=axis_size, size=(2, PIT_COUNT))
        pit_grid[random_pits[0], random_pits[1]] = True
        # Prevent pits generating at spawn points
        pit_grid[spawns[:, 0], spawns[:, 1]] = False
        pits = np.dstack(np.nonzero(pit_grid))[0]
        # Walls
        wall_grid = np.zeros((axis_size, axis_size), dtype=np.bool_)
        random_walls = RNG.integers(low=0, high=axis_size, size=(2, WALL_COUNT))
        wall_grid[random_walls[0], random_walls[1]] = True
        # Prevent walls generating at spawn points or pits
        wall_grid[spawns[:, 0], spawns[:, 1]] = False
        wall_grid[np.nonzero(pit_grid)] = False
        walls = np.dstack(np.nonzero(wall_grid))[0]
        # Return the map tuple
        pits = set(Hex(x, y) for x, y in pits)
        walls = set(Hex(x, y) for x, y in walls)
        spawns = [Hex(x, y) for x, y in spawns]
        return Map(axis_size, pits, walls, spawns)


def get_map():
    f = getattr(Maps, f'{SELECTED_MAP_NAME}_map')
    return f()
