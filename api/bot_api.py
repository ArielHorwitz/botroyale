import numpy as np


class Direction:
    N = np.asarray([1, 0])
    S = np.asarray([-1, 0])
    E = np.asarray([0, 1])
    W = np.asarray([0, -1])
    NW = np.asarray([1, -1])
    NE = np.asarray([1, 1])
    SW = np.asarray([-1, -1])
    SE = np.asarray([-1, 1])
    HOLD = np.asarray([0, 0])


class WorldInfo:
    # TODO: Add info for the bots
    def __init__(self, spawns, walls, pits):
        # Map
        self.positions = spawns
        self.walls = walls
        self.pits = pits
        # Metadata
        self.alive_mask = np.ones(len(self.positions), dtype=bool)
        self.turn_count = 0
        self.round_count = 0
        self.ap = np.zeros(len(self.positions))
        # when round_priority is empty, round is over.
        self.round_remaining_turns = []


class BaseBot:
    DIRECTIONS = [
        Direction.N,
        Direction.S,
        Direction.E,
        Direction.W,
        Direction.NW,
        Direction.NE,
        Direction.SW,
        Direction.SE,
        Direction.HOLD]

    def __init__(self, id: int):
        self.id = id

    def get_move(self, world: WorldInfo = None):
        """
        Called by the Game Logic
        :param world: state of world
        :return: action to take
        """
        return Direction.HOLD
