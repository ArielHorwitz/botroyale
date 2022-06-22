from collections import namedtuple
import itertools
import random
import numpy as np


RNG = np.random.default_rng()
Map = namedtuple('Map', ['axis_size', 'pits', 'walls', 'spawns'])


def small_test_map():
    axis_size = 2
    # Spawns
    spawns = RNG.integers(low=0, high=axis_size - 1, size=(2, 2))
    # Map features
    coords = list(itertools.product(range(axis_size), repeat=2))
    for spawn in spawns:
        if tuple(spawn) in coords:
            coords.remove(tuple(spawn))
    random.shuffle(coords)
    # Walls
    num_of_walls = 1
    walls = [coords.pop(0) for _ in range(num_of_walls)]
    # Pits
    num_of_pits = 1
    pits = [coords.pop(0) for _ in range(num_of_pits)]
    # Return the map tuple
    return Map(axis_size, pits, walls, spawns.astype(np.int8))


def random_map():
    axis_size = random.randint(5, 15)
    # Spawns
    spawns = RNG.integers(low=0, high=axis_size-1, size=(8, 2))
    # Map features
    coords = list(itertools.product(range(axis_size), repeat=2))
    for spawn in spawns:
        if tuple(spawn) in coords:
            coords.remove(tuple(spawn))
    random.shuffle(coords)
    # Walls
    num_of_walls = random.randint(0, 2*axis_size)
    walls = [coords.pop(0) for _ in range(num_of_walls)]
    # Pits
    num_of_pits = random.randint(0, 2*axis_size)
    pits = [coords.pop(0) for _ in range(num_of_pits)]
    # Return the map tuple
    return Map(axis_size, pits, walls, spawns.astype(np.int8))


def basic_map(radius=7, edge_size=1, spawn_radius=2):
    assert radius >= 2
    assert edge_size >= 1
    assert spawn_radius <= radius
    axis_size = (edge_size + radius) * 2 + 1
    spawn_offset = edge_size + radius - spawn_radius
    # Spawns
    near = spawn_offset
    mid = axis_size // 2
    far = axis_size - near - 1
    spawns = list(itertools.product([near, mid, far], repeat=2))
    spawns.remove((mid, mid))
    spawns = np.asarray(spawns)
    # Pits
    pit_grid = np.zeros((axis_size, axis_size), dtype=np.bool_)
    pit_edge = [*range(0, edge_size), *range(axis_size-1, axis_size-edge_size-1, -1)]
    pit_grid[:, pit_edge] = True
    pit_grid[pit_edge, :] = True
    random_pits = RNG.integers(low=0, high=axis_size, size=(2, axis_size*2))
    pit_grid[random_pits[0], random_pits[1]] = True
    # Prevent pits generating at spawn points
    pit_grid[spawns[:, 0], spawns[:, 1]] = False
    pits = np.dstack(np.nonzero(pit_grid))[0]
    # Walls
    wall_grid = np.zeros((axis_size, axis_size), dtype=np.bool_)
    random_walls = RNG.integers(low=0, high=axis_size, size=(2, axis_size*4))
    wall_grid[random_walls[0], random_walls[1]] = True
    # Prevent walls generating at spawn points or pits
    wall_grid[spawns[:, 0], spawns[:, 1]] = False
    wall_grid[np.nonzero(pit_grid)] = False
    walls = np.dstack(np.nonzero(wall_grid))[0]
    # Return the map tuple
    return Map(axis_size, pits, walls, spawns)
