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
    HOLD = np.asarray([0, 0])


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


class Battle:
    def __init__(self, bots, initial_state=None):
        self.bots = bots
        self.num_of_bots = len(bots)
        if initial_state is None:
            self.positions = np.zeros((self.num_of_bots, 2), dtype='int8')
        else:
            self.positions = initial_state

    def next_turn(self):
        diff = self.get_changes()
        self.positions += diff

    def get_changes(self):
        diff = np.zeros((self.num_of_bots, 2), dtype='int8')
        for i in range(self.num_of_bots):
            diff[i] += self.bots[i].move()
        return diff

    def get_map_state(self):
        return f'map state:\n{self.positions}'

    @property
    def game_over(self):
        return True


class RandomBot:
    def __init__(self, id):
        self.id = id

    def move(self):
        return random.choice(DIRECTIONS)


