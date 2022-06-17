import random
import numpy as np
from itertools import permutations
from api.logic_api import BaseLogicAPI


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
RNG = np.random.default_rng()


class Battle(BaseLogicAPI):
    def __init__(self):
        bots = make_bots(10)
        self.bots = bots
        self.num_of_bots = len(bots)
        # Positions is a sequence of 2D coordinates (a 2-sequence)
        self.positions = np.zeros((self.num_of_bots, 2), dtype='int8')
        self.turn_count = 0
        self.round_count = 0
        self.ap = np.zeros(self.num_of_bots)
        self.axis_size, self.walls, self.pits = random_map()  # must have shape (num_walls, 2)
        self.map_size = int(self.axis_size), int(self.axis_size)
        # when round_priority is empty, round is over.
        self.round_remaining_turns = []
        self.history = []

    def _next_round(self):
        self.round_remaining_turns = list(range(self.num_of_bots))
        random.shuffle(self.round_remaining_turns)
        self.ap += 50
        self.ap[self.ap > 100] = 100
        self.round_count += 1

    def _apply_diff(self, diff):
        self.positions += diff
        self.turn_count += 1
        self.history.append(diff)

    def next_turn(self):
        if self.game_over:
            return
        if len(self.round_remaining_turns) == 0:
            self._next_round()
        bot_id = self.round_remaining_turns.pop(0)
        diff = self._get_bot_move(bot_id)
        self._apply_diff(diff)

    def _get_bot_move(self, bot_id):
        diff = np.zeros((self.num_of_bots, 2), dtype='int8')
        move_diff = self.bots[bot_id].get_move()
        if self._check_legal_move(move_diff, self.positions[bot_id]):
            diff[bot_id] += move_diff
        return diff

    def _check_legal_move(self, diff, position):
        new_position = position + diff
        if np.sum(new_position < 0) or np.sum(new_position > self.axis_size - 1):
            return False
        if ((self.walls == new_position).sum(axis=1) >= 2).sum() > 0:
            return False
        return True

    def get_map_state(self):
        lines = [[' '] * self.axis_size for i in range(self.axis_size)]
        for i, (x, y) in enumerate(self.positions):
            lines[y][x] = str(i)
        border = '-' * (self.axis_size * 2)
        map = '\n'.join(' '.join(line) for line in lines)
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

    def get_move(self):
        return self.move()


def random_map():
    axis_size = RNG.integers(low=5, high=15, size=1)[0]
    diagonal = list(zip(range(axis_size), range(axis_size)))
    coords_tuples = list(permutations(range(axis_size), 2))
    coords = diagonal + coords_tuples
    random.shuffle(coords)

    num_of_walls = RNG.integers(
        low=axis_size, high=2*axis_size, size=1)[0]
    walls = [coords.pop(0) for _ in range(num_of_walls)]

    num_of_pits = RNG.integers(
        low=axis_size, high=2*axis_size, size=1)[0]
    pits = [coords.pop(0) for _ in range(num_of_pits)]

    return axis_size, walls, pits


def make_bots(num_of_bots):
    return [RandomBot(i) for i in range(num_of_bots)]
