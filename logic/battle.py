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
MAX_TURNS = 10000
RNG = np.random.default_rng()


class Battle(BaseLogicAPI):
    def __init__(self):
        bots = make_bots(10)
        self.bots = bots
        self.num_of_bots = len(bots)
        # Positions is a sequence of 2D coordinates (a 2-sequence)
        self.positions = np.zeros((self.num_of_bots, 2), dtype='int8')
        self.alive_mask = np.ones(self.num_of_bots, dtype=bool)
        self.turn_count = 0
        self.round_count = 0
        self.ap = np.zeros(self.num_of_bots)
        # walls and pits are sequences of 2D coordinates (a 2-sequence)
        self.axis_size, self.walls, self.pits = random_map()
        self.map_size = int(self.axis_size), int(self.axis_size)
        # when round_priority is empty, round is over.
        self.round_remaining_turns = []
        self.history = []

    def next_turn(self):
        if self.game_over:
            return
        if len(self.round_remaining_turns) == 0:
            self._next_round()
            return
        bot_id = self.round_remaining_turns.pop(0)
        diff, ap_spent = self._get_bot_move(bot_id)
        self._apply_diff(bot_id, diff, ap_spent)

    def _next_round(self):
        bots_id = np.arange(self.num_of_bots)[self.alive_mask]
        self.round_remaining_turns = list(bots_id)
        random.shuffle(self.round_remaining_turns)
        self.ap[self.alive_mask] += 50
        self.ap[self.ap > 100] = 100
        self.round_count += 1

    def _get_bot_move(self, bot_id):
        diff = np.zeros((self.num_of_bots, 2), dtype='int8')
        move_diff = self.bots[bot_id].get_move()
        ap_spent = self._calc_ap(move_diff)
        if self._check_legal_move(bot_id, move_diff, self.positions[bot_id], ap_spent):
            diff[bot_id] += move_diff
        return diff, ap_spent

    def _calc_ap(self, diff):
        if diff.any() != 0:
            return 10
        else:
            return 0

    def _check_legal_move(self, bot_id, diff, position, spent_ap):
        if self.ap[bot_id] - spent_ap < 0:
            return False
        new_position = position + diff
        if np.sum(new_position < 0) or np.sum(new_position > self.axis_size - 1):
            return False
        if ((self.walls == new_position).sum(axis=1) >= 2).sum() > 0:
            return False
        return True

    def _apply_diff(self, bot_id, diff, ap_spent):
        self.positions += diff
        self._apply_mortality()
        self.ap[bot_id] -= ap_spent
        self.turn_count += 1
        self.history.append(diff)

    def _apply_mortality(self):
        modified_positions = self.positions[:, None, :]
        mortality = ((self.pits == modified_positions).sum(axis=-1) >= 2).sum(axis=-1)
        mortality = mortality != 0
        self.alive_mask[mortality] = False

    def get_map_state(self):
        return self.get_match_state()

    def get_match_state(self):
        units = []
        for i in range(self.num_of_bots):
            ap = self.ap[i]
            pos = self.positions[i]
            units.append(f'Unit #{i} {ap}AP {pos}')
        units = '\n'.join(units)
        casualties = np.arange(self.num_of_bots)[self.alive_mask != True]
        state_str = '\n'.join([
            f'Round #{self.round_count}',
            f'Turn #{self.turn_count}',
            f'Turn order: {self.round_remaining_turns}',
            units,
            f'Casualties: {casualties}',
        ])
        if self.game_over:
            winner_str = ''
            if self.alive_mask.sum() == 1:
                winner = np.arange(self.num_of_bots)[self.alive_mask]
                winner_str = f'\n\n This game winner is: {winner}'
            state_str = 'GAME OVER\n\n' + state_str + winner_str
        return state_str

    @property
    def game_over(self):
        cond1 = self.turn_count >= MAX_TURNS
        cond2 = self.alive_mask.sum() <= 1
        return cond1 or cond2


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
    if (0, 0) in pits:
        pits.remove((0, 0))
    return axis_size, walls, pits


def make_bots(num_of_bots):
    return [RandomBot(i) for i in range(num_of_bots)]
