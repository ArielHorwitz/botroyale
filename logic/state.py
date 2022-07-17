import numpy as np
from api.logic import BaseLogicAPI
from bots import make_bots
from logic import maps
from api.bots import world_info
import copy
from util.time import pingpong
from util.settings import Settings
from api.actions import Action, Move, Push, IllegalAction, Idle
from util.hexagon import Hex


RNG = np.random.default_rng()


class OrderError(Exception):
    pass


class State:
    def __init__(
            self,
            death_radius, positions, walls, pits, alive_mask=None,
            ap=None,
            round_ap_spent=None,
            round_remaining_turns=None,
            step_count=0, turn_count=0, round_count=0,
            ):
        self.num_of_units = len(positions)
        # Map
        self.center = Hex(0, 0)
        self.death_radius = death_radius
        self.positions = positions
        self.walls = walls
        self.pits = pits | set(self.center.ring(death_radius))
        # Metadata
        if alive_mask is None:
            alive_mask = np.ones(self.num_of_units, dtype=bool)
        self.alive_mask = alive_mask
        if ap is None:
            ap = np.zeros(self.num_of_units)
        self.ap = ap
        if round_ap_spent is None:
            round_ap_spent = np.zeros(self.num_of_units)
        self.round_ap_spent = round_ap_spent
        if round_remaining_turns is None:
            round_remaining_turns = []
        self.round_remaining_turns = round_remaining_turns
        self.step_count = step_count
        self.turn_count = turn_count
        self.round_count = round_count

    def apply_action(self, action):
        if len(self.round_remaining_turns) == 0:
            raise OrderError(f'cannot apply action, remaining turns is empty')
        unit = self.round_remaining_turns[0]
        if not action.has_effect:
            return self._next_turn()
        if self._check_legal_action(unit, action):
            return self._do_apply_action(unit, action)
        return self._next_turn()

    def _next_turn(self):
        new_state = self.copy()
        new_state.round_remaining_turns.pop(0)
        new_state.turn_count += 1
        if len(new_state.round_remaining_turns) == 0:
            new_state._next_round()
        return new_state

    def _next_round(self):
        self._next_round_order()
        self.round_ap_spent = np.zeros(self.num_of_units)
        self.ap[self.alive_mask] += 50
        self.ap[self.ap > 100] = 100
        self.round_count += 1
        self.death_radius -= 1
        self.pits |= set(self.center.ring(self.death_radius))
        self._apply_mortality()

    def _next_round_order(self):
        bots_id = np.arange(self.num_of_units)
        p = RNG.permutation(bots_id[self.alive_mask])
        while len(p) > 0:
            min_index = np.argmin(self.round_ap_spent[p][self.alive_mask[p]])
            self.round_remaining_turns.append(p[min_index])
            p = np.delete(p, min_index)

    def _check_legal_action(self, unit, action):
        if self.ap[unit] < action.ap:
            return False
        if isinstance(action, Push):
            return self._check_legal_push(unit, action.target)
        if isinstance(action, Move):
            return self._check_legal_move(unit, action.target)
        raise TypeError(f'Unknown action: {action}')

    def _check_legal_move(self, unit, target_tile):
        # check if target is a neighbor
        self_position = self.positions[unit]
        if not self_position.get_distance(target_tile) == 1:
            return False
        # check if moving into a wall
        if target_tile in self.walls:
            return False
        # check if moving on top of another bot
        if target_tile in self.positions:
            return False
        return True

    def _check_legal_push(self, unit, target_tile):
        # check if target is a neighbor
        self_position = self.positions[unit]
        if not self_position.get_distance(target_tile) == 1:
            return False
        # check if actually pushing a bot
        if not (target_tile in self.positions):
            return False
        # check if pushing to a wall
        self_pos = self.positions[unit]
        push_end = next(self_pos.straight_line(target_tile))
        if push_end in self.walls:
            return False
        # check if pushing on top of another bot
        if push_end in self.positions:
            return False
        return True

    def _do_apply_action(self, unit, action):
        assert action.has_effect
        new_state = self.copy()
        if isinstance(action, Push):
            opp_id = new_state.positions.index(action.target)
            self_pos = new_state.positions[unit]
            new_state.positions[opp_id] = next(self_pos.straight_line(action.target))
        elif isinstance(action, Move):
            new_state.positions[unit] = action.target
        new_state._apply_mortality()
        new_state.ap[unit] -= action.ap
        new_state.round_ap_spent[unit] += action.ap
        return new_state

    def _apply_mortality(self):
        live_units = np.flatnonzero(self.alive_mask)
        for unit in live_units:
            if self.positions[unit] in self.pits:
                self.alive_mask[unit] = False
                if unit in self.round_remaining_turns:
                    self.round_remaining_turns.remove(unit)

    @property
    def casualties(self):
        return np.arange(self.num_of_units)[~self.alive_mask]

    @property
    def round_done_turns(self):
        return [bid for bid in range(self.num_of_units) if (bid not in self.casualties and bid not in self.round_remaining_turns)]

    def copy(self):
        return State(
            positions=copy.copy(self.positions),
            walls=copy.copy(self.walls),
            pits=copy.copy(self.pits),
            death_radius=self.death_radius,
            alive_mask=copy.deepcopy(self.alive_mask),
            ap=copy.deepcopy(self.ap),
            round_ap_spent=copy.deepcopy(self.round_ap_spent),
            round_remaining_turns=copy.deepcopy(self.round_remaining_turns),
            step_count=self.step_count,
            turn_count=self.turn_count,
            round_count=self.round_count,
            )

    @property
    def game_over(self):
        return self.alive_mask.sum() <= 1
