import copy
from collections import namedtuple
from dataclasses import dataclass, field
from typing import List, Set, Optional, Union
import numpy as np

from api.actions import Move, Push, Idle, Jump, Action
from util.hexagon import Hex, Hexagon

RNG = np.random.default_rng()

Effect = namedtuple('Effect', [
    'name',
    'origin',
    'target',
    ])


class OrderError(Exception):
    pass


@dataclass
class State:
    
    # Initialization parameters
    death_radius: int = field(repr=True)
    positions : List[Hexagon]
    walls: Set[Hexagon]
    pits: Set[Hexagon]
    alive_mask: Optional[np.ndarray] = field(default=None)
    ap: Optional[np.ndarray] = field(default=None)
    round_ap_spent: Optional[np.ndarray] = field(default=None)
    round_remaining_turns: List[int] = field(default_factory=list)
    step_count: int = 0
    turn_count: int = 0
    round_count: int = field(default=0, repr=True)

    num_of_units: int = field(init=False)
    center: Hexagon = field(init=False, default=Hex(0, 0))
    effects: List[Effect] = field(init=False, default_factory=list)
    last_action: Union[Action, None] = field(init=False, default=None)
    is_last_action_legal: bool = field(init=False, default=False)

    def __post_init__(self):
        self.num_of_units = len(self.positions)
        self.pits = self.pits | set(self.center.ring(self.death_radius))

        if self.alive_mask is None:
            self.alive_mask = np.ones(self.num_of_units, dtype=bool)

        if self.ap is None:
            self.ap = np.zeros(self.num_of_units)

        if self.round_ap_spent is None:
            self.round_ap_spent = np.zeros(self.num_of_units)

    def apply_action(self, action):
        new_state = self.apply_action_no_round_increment(action)
        if new_state.end_of_round:
            new_state._next_round()
        return new_state

    def apply_action_no_round_increment(self, action):
        if self.game_over:
            raise OrderError(f'Game over, no more actions allowed')
        if self.end_of_round:
            raise OrderError(f'Cannot apply action, round is over, use increment_round()')
        unit = self.round_remaining_turns[0]
        new_state = self.copy()
        if isinstance(action, Idle):
            new_state._next_turn()
            new_state.is_last_action_legal = True
        elif self._check_legal_action(unit, action):
            new_state._do_apply_action(unit, action)
            new_state.is_last_action_legal = True
        else:
            new_state._next_turn()
            new_state._add_effect('illegal', self.positions[unit])
        new_state.last_action = action
        return new_state

    def increment_round(self):
        if self.game_over:
            raise OrderError(f'Game over, no more rounds')
        if not self.end_of_round:
            raise OrderError('Not the end of round')
        new_state = self.copy()
        new_state._next_round()
        return new_state

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

    def check_legal_action(self, unit, action):
        if isinstance(action, Idle):
            return True
        return self._check_legal_action(unit, action)

    def _next_turn(self):
        self.round_remaining_turns.pop(0)
        self.turn_count += 1

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
        units = np.arange(self.num_of_units)
        p = RNG.permutation(units[self.alive_mask])
        while len(p) > 0:
            min_index = np.argmin(self.round_ap_spent[p][self.alive_mask[p]])
            self.round_remaining_turns.append(p[min_index])
            p = np.delete(p, min_index)

    def _check_legal_action(self, unit, action):
        if self.ap[unit] < action.ap:
            return False
        if isinstance(action, Jump):
            return self._check_legal_jump(unit, action.target)
        if isinstance(action, Push):
            return self._check_legal_push(unit, action.target)
        if isinstance(action, Move):
            return self._check_legal_move(unit, action.target)
        raise TypeError(f'Unknown action: {action}')

    def _check_legal_jump(self, unit, target):
        return self._check_legal_move(unit, target, distance=2)

    def _check_legal_move(self, unit, target_tile, distance=1):
        # check if target is a neighbor
        self_position = self.positions[unit]
        if not self_position.get_distance(target_tile) == distance:
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
        assert not isinstance(action, Idle)
        self_pos = self.positions[unit]
        if isinstance(action, Push):
            opp_id = self.positions.index(action.target)
            self.positions[opp_id] = next(self_pos.straight_line(action.target))
            self._add_effect('push', self_pos, action.target)
        elif isinstance(action, Jump):
            self.positions[unit] = action.target
            self._add_effect('jump', self_pos, action.target)
        elif isinstance(action, Move):
            self.positions[unit] = action.target
            self._add_effect('move', self_pos, action.target)
        self._apply_mortality()
        self.ap[unit] -= action.ap
        self.round_ap_spent[unit] += action.ap

    def _apply_mortality(self):
        live_units = np.flatnonzero(self.alive_mask)
        for unit in live_units:
            pos = self.positions[unit]
            death_by_pits = pos in self.pits
            death_by_ROD = pos.get_distance(self.center) >= self.death_radius
            if death_by_pits or death_by_ROD:
                self.alive_mask[unit] = False
                if unit in self.round_remaining_turns:
                    self.round_remaining_turns.remove(unit)
                self._add_effect('death', self.positions[unit])

    def _add_effect(self, name, origin, target=None):
        effect = Effect(
            name=name,
            origin=origin,
            target=target,
        )
        self.effects.append(effect)


    @property
    def end_of_round(self):
        return len(self.round_remaining_turns) == 0

    @property
    def casualties(self):
        return np.arange(self.num_of_units)[~self.alive_mask]

    @property
    def round_done_turns(self):
        return [unit for unit in range(self.num_of_units) if (unit not in self.casualties and unit not in self.round_remaining_turns)]

    @property
    def game_over(self):
        return self.alive_mask.sum() <= 1

    @property
    def winner(self):
        if self.alive_mask.sum() == 1:
            return np.flatnonzero(self.alive_mask)[0]
        return None

    @property
    def current_unit(self):
        if not self.end_of_round:
            return self.round_remaining_turns[0]
        else:
            return None
