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
MAX_TURNS = 1000
MAP_SIZE = 10


class Battle:
    def __init__(self, bots=None, initial_state=None):
        if bots is None:
            bots = make_bots(2)
        self.bots = bots
        self.num_of_bots = len(bots)
        if initial_state is None:
            initial_state = np.zeros((self.num_of_bots, 2), dtype='int8')
        self.positions = initial_state
        self.turn_count = 0
        self.map_size = MAP_SIZE, MAP_SIZE

    def next_turn(self):
        if self.game_over:
            raise RuntimeError('Game over, no turns left')
        diff = self.get_changes()
        # check legal moves
        self.positions += diff
        self.positions.reshape(-1)
        self.positions[self.positions < 0] = 0
        self.positions[self.positions > MAP_SIZE - 1] = MAP_SIZE - 1
        self.positions.reshape((self.num_of_bots, 2))
        self.turn_count += 1

    def get_changes(self):
        diff = np.zeros((self.num_of_bots, 2), dtype='int8')
        for i in range(self.num_of_bots):
            diff[i] += self.bots[i].move()
        return diff

    def get_map_state(self):
        lines = [[' '] * 10 for i in range(MAP_SIZE)]
        for i, (x, y) in enumerate(self.positions):
            lines[y][x] = str(i)
        border = '--------------------'
        map = '|\n'.join('|'.join(line) for line in lines) + '|'
        turn = f'turn: {self.turn_count}'
        return '\n'.join([
            turn,
            border,
            map,
            border])

    @property
    def game_over(self):
        return self.turn_count >= MAX_TURNS


class RandomBot:
    def __init__(self, id):
        self.id = id

    def move(self):
        return random.choice(DIRECTIONS)


def make_bots(num_of_bots):
    return [RandomBot(i) for i in range(num_of_bots)]
