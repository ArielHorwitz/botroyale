import numpy as np
from util.hexagon import Hex


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
    def __init__(self, id: int):
        self.id = id

    def get_action(self, pos):
        return Hex(0, 0)
