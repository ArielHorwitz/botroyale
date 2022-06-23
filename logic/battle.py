import random
import numpy as np
from api.logic_api import BaseLogicAPI, EventDeath
from bots import make_bots
from logic import maps


MAX_TURNS = 10000
RNG = np.random.default_rng()


class Battle(BaseLogicAPI):
    def __init__(self):
        super().__init__()
        map = maps.get_map()
        assert len(map.pits) > 0
        assert len(map.walls) > 0
        # Bots
        self.num_of_bots = len(map.spawns)
        self.bots = make_bots(self.num_of_bots)
        # Map
        self.positions = np.asarray(map.spawns)
        self.axis_size = np.asarray(map.axis_size)
        self.walls = np.asarray(map.walls)
        self.pits = np.asarray(map.pits)
        # Metadata
        self.alive_mask = np.ones(self.num_of_bots, dtype=bool)
        self.turn_count = 0
        self.round_count = 0
        self.ap = np.zeros(self.num_of_bots)
        self.round_ap_spent = np.zeros(self.num_of_bots)
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
        last_alive = set(np.flatnonzero(self.alive_mask))
        self._apply_diff(bot_id, diff, ap_spent)
        now_alive = set(np.flatnonzero(self.alive_mask))
        for dead_unit in last_alive - now_alive:
            self.add_event(EventDeath(dead_unit))

    def _next_round(self):
        self._next_round_order()
        self.round_ap_spent = np.zeros(self.num_of_bots)
        self.ap[self.alive_mask] += 50
        self.ap[self.ap > 100] = 100
        self.round_count += 1

    def _next_round_order(self):
        bots_id = np.arange(self.num_of_bots)
        p = RNG.permutation(bots_id[self.alive_mask])
        while len(p) > 0:
            min_index = np.argmin(self.round_ap_spent[p][self.alive_mask[p]])
            self.round_remaining_turns.append(p[min_index])
            p = np.delete(p, min_index)

    def _get_bot_move(self, bot_id):
        diff = np.zeros((self.num_of_bots, 2), dtype='int8')
        move_diff = self.bots[bot_id].get_move()
        ap_spent = self._calc_ap(move_diff)
        if self._check_legal_move(bot_id, move_diff, ap_spent):
            diff[bot_id] += move_diff
        else:
            ap_spent = 0
        return diff, ap_spent

    def _calc_ap(self, diff):
        if any(diff):
            return 10
        else:
            return 0

    def _check_legal_move(self, bot_id, diff, spent_ap):
        position = self.positions[bot_id]
        if self.ap[bot_id] - spent_ap < 0:
            return False
        if tuple(diff) != (0, 0):
            new_position = position + diff

            # check if moving out of bounds
            if np.sum(new_position < 0) or np.sum(new_position > self.axis_size - 1):
                return False

            # check if moving to a wall tile
            if ((self.walls == new_position).sum(axis=1) >= 2).sum() > 0:
                return False

            # check if moving on top of another bot
            if ((self.positions == new_position).sum(axis=1) >= 2).sum() > 0:
                return False
        return True

    def _apply_diff(self, bot_id, diff, ap_spent):
        self.positions += diff
        self._apply_mortality()
        self.ap[bot_id] -= ap_spent
        self.round_ap_spent[bot_id] += ap_spent
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
        casualties = np.arange(self.num_of_bots)[~self.alive_mask]
        state_str = '\n'.join([
            f'Round #{self.round_count}',
            f'Turn #{self.turn_count}',
            f'Turn order: {self.round_remaining_turns}',
            f'Casualties: {casualties}',
            f'\n{units}',
        ])
        if self.game_over:
            winner_str = ''
            if self.alive_mask.sum() == 1:
                winner = np.arange(self.num_of_bots)[self.alive_mask]
                winner_str = f'This game winner is: unit #{winner[0]}\n\n'
            state_str = 'GAME OVER\n' + winner_str + state_str
        return state_str

    @property
    def game_over(self):
        cond1 = self.turn_count >= MAX_TURNS
        cond2 = self.alive_mask.sum() <= 1
        return cond1 or cond2
