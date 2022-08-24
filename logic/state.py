"""
Home of the `logic.state.State` class.
"""
from typing import Optional, Sequence, NamedTuple
from numpy.typing import NDArray
from warnings import warn
import numpy as np
import copy
from util.hexagon import Hexagon, ORIGIN
from logic.prng import PRNG
from api.logging import logger as glogger
from api.actions import MAX_AP, REGEN_AP, ALL_ACTIONS, Action, Idle, Move, Jump, Push


# Assert AP is always an integer, this is assumed by the round order tiebreaker
assert all(isinstance(action.ap, int) for action in ALL_ACTIONS)


# Number of iterations on the PRNG to apply between rounds.
NEXT_SEED_ITERATIONS = 100


class Effect(NamedTuple):
    """Represents an in-game effect. Usually the result of an action."""
    name: str
    """The name of the effect, should match the names in `assets/vfx`."""
    origin: Hexagon
    """Origin of the effect."""
    target: Optional[Hexagon]
    """Target/direction of the effect."""


class OrderError(Exception):
    """Raised when something is done in the wrong order."""
    pass


class State:
    """The State object represents a point in time of a battle.

    Under most normal circumstances, a state should not be initialized directly. Usually, the only relevant methods are `State.check_legal_action` and `State.apply_action`. Given an existing State, these two methods will be all one needs in order to play an entire battle.

    The `State.apply_action` method will return the new state given after applying an
    action. The returned state will always be on a unit's turn (unless it is
    `State.game_over`), allowing you to repeatedly apply actions until game over.

    ### List attributes
    Many attributes of state are lists of values: one for each unit. For these attribtes, the index is by `api.bots.BaseBot.id`.

    ### Maps (initial states)
    To create an initial state (also known as a map), it is highly recommended
    to refer to the `logic.maps` module.

    When initializing new states for a map, it should be with only the
    following arguments: *death_radius*, *positions*, *pits*, and *walls*. Note that
    initial states are created by default at round 0, and not on a unit's turn.
    Use `State.increment_round` to get the state of the beginning of the first turn.

    ### Round incrementation
    For a more manual approach to applying actions, one can use
    `State.apply_action_no_round_increment`. This method is similar to `State.apply_action`
    but does not increment rounds automatically, allowing one to see states
    between turns (end_of_round), where the effects of a new round are applied.
    This requires using the method `State.increment_round` in order to play an entire
    battle.
    """
    def __init__(self,
            death_radius: int,
            positions: Optional[list[Hexagon]] = None,
            pits: Optional[set[Hexagon]] = None,
            walls: Optional[set[Hexagon]] = None,
            alive_mask: Optional[NDArray[np.bool_]] = None,
            ap: Optional[NDArray[np.int_]] = None,
            round_ap_spent: Optional[list[int]] = None,
            round_remaining_turns: Optional[list[int]] = None,
            round_done_turns: Optional[list[int]] = None,
            casualties: Optional[list[int]] = None,
            step_count: int = 0,
            turn_count: int = 0,
            round_count: int = 0,
            last_action: Optional[Action] = None,
            is_last_action_legal: bool = False,
            effects: Optional[list[Effect]] = None,
            seed: Optional[int] = None,
            ):
        # Units
        if positions is None:
            positions = []
        self.positions: list[Hexagon] = positions
        """A list of `util.hexagon.Hexagon`s representing the positions of the units."""
        self.num_of_units: int = len(positions)
        """Number of units."""
        if alive_mask is None:
            alive_mask = np.ones(self.num_of_units, dtype=np.bool_)
        self.alive_mask: NDArray[np.bool_] = alive_mask
        """Mask of living units (numpy array of bools)."""
        if ap is None:
            ap = np.zeros(self.num_of_units, dtype=np.int_)
        self.ap: NDArray[np.int_] = ap
        """List of unit AP values (numpy array of ints)."""
        if round_ap_spent is None:
            round_ap_spent = [0] * self.num_of_units
        self.round_ap_spent: list[int] = round_ap_spent
        """List of AP spent by each unit in this round."""
        if round_remaining_turns is None:
            round_remaining_turns = []
        self.round_remaining_turns: list[int] = round_remaining_turns
        """List of uids that still have not ended their turn this round.

        The first uid in this list is the unit in turn (`State.current_unit`). If the list is empty, it is nobody's turn (see: `State.end_of_round`)."""
        if round_done_turns is None:
            round_done_turns = [i for i in range(self.num_of_units)]
        self.round_done_turns: list[int] = round_done_turns
        """List of uids that have ended their turn this round."""
        if casualties is None:
            casualties = [-1] * self.num_of_units
        self.casualties: list[int] = casualties
        """List of when each unit died. Live units have a `casualties` value of -1."""

        # Map features
        self.death_radius: int = death_radius
        """The radius of the "ring of death".

        This radius determines at what distance from `util.hexagon.ORIGIN` would a unit die.
        """
        if pits is None:
            pits = set()
        self.pits: set[Hexagon] = pits
        """A set of hexes that are pits."""
        if walls is None:
            walls = set()
        self.walls: set[Hexagon] = walls
        """A set of hexes that are walls."""

        # Time-keeping
        self.step_count: int = step_count
        """A step is the smallest unit of in-game time.

        A single action in a turn is a step. "End of round" states are also a step (see: `State.end_of_round`).
        """
        self.turn_count: int = turn_count
        """Total number of turns taken."""
        self.round_count: int = round_count
        """Current round count.

        Initially, states begin at round 0, before any units have had a turn.
        """

        # Action
        self.last_action: Action = last_action
        """The action that was taken in the previous state."""
        self.is_last_action_legal: bool = is_last_action_legal
        """If `State.last_action` was a legal action."""
        if effects is None:
            effects = []
        self.effects: list[Effect] = effects
        """List of `Effect`s resulting from the last state resolving to this state."""

        # Metadata
        if seed is None:
            seed = PRNG.get_random_seed()
        self.seed: int = seed
        """A seed for the `logic.prng.PRNG`.

        Used by `State.next_round_order`.
        """

    # User methods - return new states
    # check_legal_action "unit" argument is being deprecated.
    def check_legal_action(self, unit: None = None, action: Optional[Action] = None) -> bool:
        """If applying *action* to this state is legal.

        .. warning:: Signature Change
            The *unit* argument is deprecated since v1.0 and will be removed in v2.0.
            Please only pass *action* like so: `check_legal_action(action=my_action)`
            until v2.0.
        """
        # DEPRECATING the unit argument.
        # The action argument is non-optional, despite the typing hints.
        # We still want the method name check_legal_action and so we make unit
        # an optional keyword argument. The action parameter must then also
        # be a keyword argument since it is positioned after the unit argument.
        # After deprecation, the action argument will be a normal positional
        # argument expecting an Action.
        if action is None:
            raise ValueError(f'Must provide an action.')
        assert isinstance(action, Action)
        # Check if user is still using the unit argument and warn if so.
        if unit is not None:
            warn(f'State.check_legal_action signature will change. Please see documentation.')
        if isinstance(action, Idle):
            return True
        return self._check_legal_action(action)

    def apply_action(self, action: Action) -> 'State':
        """Return the state resulting from applying *action* to this state.

        This is a high-level method that will increment the round if necessary, ensuring that the resulting state will always be on a unit's turn (at least if the resulting state is not a game over).

        For a more manual approach, use `State.apply_action_no_round_increment`.
        """
        new_state = self.apply_action_no_round_increment(action)
        if new_state.end_of_round:
            new_state._next_round()
        return new_state

    def apply_action_no_round_increment(self, action: Action) -> 'State':
        """Return the state resulting from applying *action* to this state.

        This will include `State.end_of_round` states, where it is no unit's turn. Most users will prefer to use `State.apply_action` as it does not reach "end of round" states and does not require using `State.increment_round`.
        """
        assert isinstance(action, Action)
        if self.game_over:
            raise OrderError(f'Game over, no more actions allowed')
        if self.end_of_round:
            raise OrderError(f'Cannot apply action, round is over: use state.increment_round()')
        # Create a copy and apply changes on it in place
        new_state = self.copy(copy_last_action=False)
        if isinstance(action, Idle):
            new_state.is_last_action_legal = True
            new_state._next_turn()
        elif self._check_legal_action(action):
            new_state.is_last_action_legal = True
            new_state._do_apply_action(action)
        else:
            new_state.is_last_action_legal = False
            new_state._next_turn()
            new_state._add_effect('illegal', self.positions[self.current_unit])
        new_state.last_action = action
        new_state.step_count += 1
        return new_state

    def increment_round(self) -> 'State':
        """Return the state resulting from starting the next round.

        Can only be used on `State.end_of_round` states.
        """
        if self.game_over:
            raise OrderError(f'Game over, no more rounds')
        if not self.end_of_round:
            raise OrderError('Not the end of round')
        # Create a copy and apply changes on it in place
        new_state = self.copy(copy_last_action=False)
        new_state._next_round()
        return new_state

    def copy(self, copy_last_action: bool = True) -> 'State':
        """Return a copy of the state.

        If copy_last_action is True, the copy will include information about
        the last_action: last_action, is_last_action_legal, and effects."""
        if copy_last_action:
            last_action = self.last_action
            is_last_action_legal = self.is_last_action_legal
            effects = copy.copy(self.effects)
        else:
            last_action = None
            is_last_action_legal = False
            effects = None
        return State(
            death_radius=self.death_radius,
            positions=copy.copy(self.positions),
            pits=copy.copy(self.pits),
            walls=copy.copy(self.walls),
            alive_mask=np.copy(self.alive_mask),
            ap=np.copy(self.ap),
            round_ap_spent=copy.copy(self.round_ap_spent),
            round_remaining_turns=copy.copy(self.round_remaining_turns),
            round_done_turns=copy.copy(self.round_done_turns),
            casualties=copy.copy(self.casualties),
            step_count=self.step_count,
            turn_count=self.turn_count,
            round_count=self.round_count,
            last_action=last_action,
            is_last_action_legal=is_last_action_legal,
            effects=effects,
            seed=self.seed,
            )

    def apply_kill_unit(self):
        """Return the state resulting from killing the `State.current_unit`.

        Works as an alternative for `State.apply_action` when a unit is
        non-cooperative and will not return an action.

        Returns:
            A new `State` after the current unit dies on their turn.
        """
        new_state = self.apply_kill_unit_no_round_increment()
        if new_state.end_of_round and not new_state.game_over:
            new_state._next_round()
        return new_state

    def apply_kill_unit_no_round_increment(self):
        """Return the state resulting from killing the `State.current_unit`.

        Works as an alternative for `State.apply_action_no_round_increment`
        when a unit is non-cooperative and will not return an action.

        Returns:
            A new `State` after the current unit dies on their turn.
        """
        if self.game_over:
            raise OrderError(f'Game over, cannot kill')
        if self.end_of_round:
            raise OrderError(f'Cannot apply kill, round is over: use state.increment_round()')
        current = self.current_unit
        new_state = self.copy(copy_last_action=False)
        if not new_state.game_over:
            new_state._next_turn()
        new_state._apply_mortality(force_kill=[current])
        new_state._add_effect('kill', self.positions[current])
        new_state.step_count += 1
        return new_state

    # Properties
    @property
    def current_unit(self) -> Optional[int]:
        """The uid of the current unit in turn, or None if the current state is `State.end_of_round` (and there is no unit in turn).

        .. caution:: A statement in Python will equate to `False` if it is either `None` (no unit in turn in this case) or `0` (unit #0 in turn in this case).

        Hence, do **not** use like this:
        ```python
        if state.winner:
            winner_uid = state.winner
        ```

        Instead use like this:
        ```python
        if state.winner is not None:
            winner_uid = state.winner
        ```
        """
        if not self.end_of_round:
            return self.round_remaining_turns[0]
        return None

    @property
    def game_over(self) -> bool:
        """If the game is over."""
        return self.alive_mask.sum() <= 1

    @property
    def winner(self) -> Optional[int]:
        """The uid of the winning unit, or None if it is a draw or it is not yet `State.game_over`.

        .. tip:: Check `State.game_over` before checking `State.winner`.
        .. caution:: A statement in Python will equate to `False` if it is either `None` (draw in this case) or `0` (unit #0 won in this case).

        Hence, do **not** use like this:
        ```python
        if state.winner:
            declare_victory(state.winner)
        else:
            declare_draw()
        ```

        Instead use like this:
        ```python
        if state.winner is not None:
            declare_victory(state.winner)
        else:
            declare_draw()
        ```
        """
        if self.alive_mask.sum() == 1:
            return np.flatnonzero(self.alive_mask)[0]
        return None

    @property
    def next_round_order(self) -> list[int]:
        """List of uids sorted by the order of turns in the next round.

        This assumes no more AP is spent for the rest of the round. The round order is sorted by AP spent and uses `logic.prng.PRNG` as tiebreaker."""
        return self._get_round_order()

    @property
    def end_of_round(self) -> bool:
        """If it is currently the end of round and no unit is in turn.

        This indicates that the method `State.increment_round` should be used before trying to apply an action."""
        return len(self.round_remaining_turns) == 0

    @property
    def death_order(self) -> list[int]:
        """List of unit uids that have died, in order of their death."""
        dead_units = np.flatnonzero(~self.alive_mask)
        return sorted(dead_units, key=lambda u: self.casualties[u])

    # Legality methods
    def _check_legal_action(self, action: Action) -> bool:
        """Returns if applying the action is legal."""
        if self.ap[self.current_unit] < action.ap:
            return False
        if type(action) is Move:
            return self._check_legal_move(action.target)
        elif type(action) is Jump:
            return self._check_legal_jump(action.target)
        elif type(action) is Push:
            return self._check_legal_push(action.target)
        raise TypeError(f'Unknown action: {action}')

    def _check_legal_move(self, target: Hexagon) -> bool:
        if not self._check_unit_distance(target, 1):
            return False
        return self._check_legal_movement(target)

    def _check_legal_jump(self, target: Hexagon) -> bool:
        if not self._check_unit_distance(target, 2):
            return False
        return self._check_legal_movement(target)

    def _check_legal_push(self, target: Hexagon) -> bool:
        # Can only push an adjascent target
        if not self._check_unit_distance(target, 1):
            return False
        # Target must contain a unit
        if not target in self.positions:
            return False
        # Must push to a tile that can be moved on to
        push_end = next(self.positions[self.current_unit].straight_line(target))
        return self._check_legal_movement(push_end)

    def _check_unit_distance(self, target: Hexagon, distance: int) -> bool:
        """Returns if the current unit is at a specific distance from a target tile."""
        target_dist = target.get_distance(self.positions[self.current_unit])
        return target_dist == distance

    def _check_legal_movement(self, target: Hexagon) -> bool:
        """Returns if a unit may move on to a target tile."""
        # Cannot stand on walls
        if target in self.walls:
            return False
        # Cannot stand on other units
        if target in self.positions:
            return False
        return True

    # Internal methods - apply changes in place (on self)
    def _do_apply_action(self, action: Action):
        """Applies the action in place. Does not check or assert legality."""
        assert not isinstance(action, Idle)
        unit = self.current_unit
        unit_pos = self.positions[unit]
        target = action.target
        if type(action) is Move:
            self.positions[unit] = target
            self._add_effect('move', unit_pos, target)
        elif type(action) is Jump:
            self.positions[unit] = target
            self._add_effect('jump', unit_pos, target)
        elif type(action) is Push:
            opp_id = self.positions.index(target)
            self.positions[opp_id] = next(unit_pos.straight_line(target))
            self._add_effect('push', unit_pos, target)
        else:
            raise TypeError(f'Unkown action: {action}')
        self.ap[unit] -= action.ap
        self.round_ap_spent[unit] += action.ap
        self._apply_mortality()

    def _next_turn(self):
        """Increment turn in place."""
        self.round_done_turns.append(self.current_unit)
        self.round_remaining_turns.pop(0)
        self.turn_count += 1

    def _next_round(self, set_death_pits: bool = True):
        """Increment round in place."""
        # Setting the new turn order uses AP spent and this round's seed.
        # Let's do that before resetting either.
        self.round_remaining_turns = self._get_round_order()
        self.round_done_turns = []
        self.round_ap_spent = [0] * self.num_of_units
        self.ap[self.alive_mask] += REGEN_AP
        self.ap[self.ap > MAX_AP] = MAX_AP
        self.death_radius -= 1
        if set_death_pits:
            self.pits |= set(ORIGIN.ring(self.death_radius))
        # Contracting ring of death may kill, let's apply that
        self._apply_mortality()
        self.step_count += 1
        self.round_count += 1
        # New round, new seed
        self.seed = self._get_next_seed()

    def _get_next_seed(self) -> int:
        """Derives the next round's seed. We simply take the seed value from
        several iterations ahead of the current seed value."""
        rng = PRNG(self.seed)
        rng.iterate(NEXT_SEED_ITERATIONS)
        return rng.seed

    def _get_round_order(self) -> list[int]:
        """Gets the round order of the next round.

        The round order is sorted by AP spent and uses the PRNG as tiebreaker.
        We assume AP spent is an integer so we use numbers between 0 and 1
        for tiebreakers."""
        live_uids = np.flatnonzero(self.alive_mask)
        tiebreakers = PRNG(self.seed).generate_list(self.num_of_units)
        return sorted(live_uids,
            key=lambda uid: self.round_ap_spent[uid] + tiebreakers[uid])

    def _apply_mortality(self, force_kill: Optional[Sequence[int]] = None):
        """Checks if any live units are supposed to be dead, and kills them in
        place. Should be called any time positions, pits, or death_radius change.

        Units die if they are standing on a pit or beyond the death_radius.

        Args:
            force_kill: A sequence of uids to kill.
        """
        if force_kill is None:
            force_kill = []
        for uid in np.flatnonzero(self.alive_mask):
            pos = self.positions[uid]
            death_by_force = uid in force_kill
            death_by_pits = pos in self.pits
            death_by_ROD = pos.get_distance(ORIGIN) >= self.death_radius
            if death_by_pits or death_by_ROD or death_by_force:
                self.alive_mask[uid] = False
                self.casualties[uid] = self.step_count
                if uid in self.round_remaining_turns:
                    self.round_remaining_turns.remove(uid)
                self._add_effect('death', pos)

    def _add_effect(self, name: str, origin: Hexagon, target: Optional[Hexagon] = None):
        """Adds an effect to the effect list in place. This is used to record
        the effects of the last action."""
        self.effects.append(Effect(
            name=name,
            origin=origin,
            target=target,
        ))
