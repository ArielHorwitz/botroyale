import numpy as np
from api.logic import BaseLogicAPI, EventDeath
from bots import make_bots
from logic import maps
from api.bots import world_info
import copy
from util.settings import Settings
from api.actions import Move, Push, IllegalAction, Idle
from util.hexagon import Hex


MAX_ROUNDS = Settings.get('round_cap', 300)
DEBUG = Settings.get('battle_debug', True)
RNG = np.random.default_rng()


class Battle(BaseLogicAPI):
    def __init__(self):
        super().__init__()
        map = maps.get_map()
        # Bots
        self.num_of_bots = len(map.spawns)
        self.bots = make_bots(self.num_of_bots)
        self.unit_colors = [self.get_color(bot.COLOR_INDEX) for bot in self.bots]
        # Map
        self.center = Hex(0, 0)
        # Ring contracts before the first round, so we set the ring even
        # further out than one tile past the map radius.
        self.ring_radius = map.radius + 2
        self.positions = map.spawns
        self.walls = map.walls
        # Add the first ring now (the one added before the first round)
        self.pits = map.pits | set(self.center.ring(map.radius+1))
        # Metadata
        self.alive_mask = np.ones(self.num_of_bots, dtype=bool)
        self.turn_count = 0
        self.round_count = 0
        self.ap = np.zeros(self.num_of_bots)
        self.round_ap_spent = np.zeros(self.num_of_bots)
        # when round_priority is empty, round is over.
        self.round_remaining_turns = []
        self.history = []

    def next_step(self):
        if self.game_over:
            return
        if len(self.round_remaining_turns) == 0:
            self._next_round()
            return
        bot_id = self.round_remaining_turns[0]
        debug(f'Round/Turn: {self.round_count} / {self.turn_count}')
        debug(f'Getting action from bot #{bot_id}')
        action = self._get_bot_action(bot_id)
        if not action.has_effect:
            self.round_remaining_turns.pop(0)
            self.turn_count += 1
            return
        debug(f'Applying bot #{bot_id} action: {action}')
        self._apply_action(bot_id, action)

    def _next_round(self):
        self._next_round_order()
        self.round_ap_spent = np.zeros(self.num_of_bots)
        self.ap[self.alive_mask] += 50
        self.ap[self.ap > 100] = 100
        self.round_count += 1
        self.ring_radius -= 1
        self.pits |= set(self.center.ring(self.ring_radius))
        self._apply_mortality()

    def _next_round_order(self):
        bots_id = np.arange(self.num_of_bots)
        p = RNG.permutation(bots_id[self.alive_mask])
        while len(p) > 0:
            min_index = np.argmin(self.round_ap_spent[p][self.alive_mask[p]])
            self.round_remaining_turns.append(p[min_index])
            p = np.delete(p, min_index)

    def _get_bot_action(self, bot_id):
        world_state = self.set_world_info()
        action = self.bots[bot_id].get_action(world_state)
        if self._check_legal_action(bot_id, action):
            return action
        return IllegalAction()

    def _check_legal_action(self, bot_id, action):
        if not self.check_ap(bot_id, action.ap):
            debug(f'Unit #{bot_id} missing AP: {action}')
            return False
        if isinstance(action, Push):
            return self._check_legal_push(bot_id, action.target)
        if isinstance(action, Move):
            return self._check_legal_move(bot_id, action.target)
        raise TypeError(f'Unknown action: {action}')

    def check_ap(self, bot_id, ap_cost):
        return self.ap[bot_id] >= ap_cost

    def _check_legal_move(self, bot_id, target_tile):
        # check if target is a neighbor
        self_position = self.positions[bot_id]
        if not self_position.get_distance(target_tile) == 1:
            debug(f'Illegal move by Unit #{bot_id}: not neighbor {self_position} -> {target_tile}')
            return False
        # check if moving into a wall
        if target_tile in self.walls:
            debug(f'Illegal move by Unit #{bot_id}: is wall {self_position} -> {target_tile}')
            return False
        # check if moving on top of another bot
        if target_tile in self.positions:
            debug(f'Illegal move by Unit #{bot_id}: is unit {self_position} -> {target_tile}')
            return False
        return True

    def _check_legal_push(self, bot_id, target_tile):
        # check if target is a neighbor
        self_position = self.positions[bot_id]
        if not self_position.get_distance(target_tile) == 1:
            debug(f'Illegal push by Unit #{bot_id}: not neighbor {self_position} -> {target_tile}')
            return False
        # check if actually pushing a bot
        if not (target_tile in self.positions):
            debug(f'Illegal push by Unit #{bot_id}: no unit {self_position} -> {target_tile}')
            return False
        # check if pushing to a wall
        self_pos = self.positions[bot_id]
        push_end = next(self_pos.straight_line(target_tile))
        if push_end in self.walls:
            debug(f'Illegal move by Unit #{bot_id}: against wall {self_position} -> {target_tile}')
            return False
        # check if pushing on top of another bot
        if push_end in self.positions:
            debug(f'Illegal move by Unit #{bot_id}: against unit {self_position} -> {target_tile}')
            return False
        return True

    def _apply_action(self, bot_id, action):
        assert action.has_effect
        if isinstance(action, Push):
            debug(f'{bot_id} APPLY PUSH: {action}')
            opp_id = self.positions.index(action.target)
            self_pos = self.positions[bot_id]
            self.positions[opp_id] = next(self_pos.straight_line(action.target))
        elif isinstance(action, Move):
            debug(f'{bot_id} APPLY MOVE: {action}')
            self.positions[bot_id] = action.target
        self._apply_mortality()
        self.ap[bot_id] -= action.ap
        self.round_ap_spent[bot_id] += action.ap

    def _apply_mortality(self):
        live_bots = np.flatnonzero(self.alive_mask)
        for bot_id in live_bots:
            if self.positions[bot_id] in self.pits:
                self.add_event(EventDeath(bot_id))
                self.alive_mask[bot_id] = False
                if bot_id in self.round_remaining_turns:
                    self.round_remaining_turns.remove(bot_id)
                # Move to graveyard
                # TODO move to graveyard when GUI can handle it
                # self.positions[bot_id] = Hex(10**6+bot_id, 10**6)

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

    def set_world_info(self):
        return world_info(
            positions=copy.copy(self.positions),
            walls=copy.copy(self.walls),
            pits=copy.copy(self.pits),
            alive_mask=copy.deepcopy(self.alive_mask),
            turn_count=self.turn_count,
            round_count=self.round_count,
            ap=copy.deepcopy(self.ap),
            round_remaining_turns=copy.deepcopy(self.round_remaining_turns)
            )

    def debug(self):
        self.debug_mode = not self.debug_mode

    @staticmethod
    def _calc_ap(pos, target):
        return 10 * (pos is not target)

    @property
    def game_over(self):
        cond1 = self.round_count > MAX_ROUNDS
        cond2 = self.alive_mask.sum() <= 1
        return cond1 or cond2


def debug(m):
    if DEBUG:
        print(m)
