import random
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


DIRECTIONS = [
    Direction.N,
    Direction.S,
    Direction.E,
    Direction.W,
    Direction.NW,
    Direction.NE,
    Direction.SW,
    Direction.SE]


class Battle:
    def __init__(self, bots, initial_state):
        self.bots = bots
        self.positions = initial_state

    def next_turn(self):
        diff = self.get_changes()
        # self.apply_changes(diff)

    def get_changes(self):
        return None

    def get_map_state(self):
        return f'{self}.get_map_state() not implemented.'

    @property
    def game_over(self):
        return True


class Bot:
    def __init__(self):
        pass

    def move(self):
        diff = random.choice(DIRECTIONS)
        return diff


class Map:
    def __init__(self, initial_state):


