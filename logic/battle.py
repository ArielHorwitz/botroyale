from typing import Union, Optional, Sequence, Callable
import numpy as np
from api.logging import logger as glogger
from api.bots import BaseBot
from api.actions import Action
from bots import make_bots
from logic.maps import get_map_state, DEFAULT_MAP_NAME
from logic.state import State
from util.time import pingpong
from util.settings import Settings


LOGIC_DEBUG = Settings.get('logging.battle', True)
LINEBR = '='*75


class Battle:
    """The Battle manages the states and bots of a single battle.

    It remembers a history of states as well as the current state.
    It also creates the bots and polls them for an action on their turn.
    """

    def __init__(self,
            initial_state: Optional[State] = None,
            bot_getter: Callable[[int], Sequence[BaseBot]] = make_bots,
            only_bot_turn_states: bool = True,
            ):
        """
        initial_state -- the first state of the battle. If initial_state is not
        provided, it will be generated using the map generator based on
        configured settings.

        bot_getter -- a function that takes a number and returns that many
        initialized bots. If bot_getter is not provided, the default `make_bots`
        will be used that is based on configured settings.

        only_bot_turn_states -- determines whether to skip "end_of_round" states
        and other states that are not expecting an action from a unit. This is
        useful for bot developers who may not care about "mid-states" and only
        care to see when a bot needs to take action. This essentially determines
        whether actions are applied to states with `apply_action` or
        `apply_action_no_round_increment`.
        """
        self._map_name = 'Custom initial state'
        if initial_state is None:
            initial_state = get_map_state()
            self._map_name = DEFAULT_MAP_NAME
        self.__current_state: State = initial_state
        self.history: Sequence[State] = [initial_state]
        self.__only_bot_turn_states: bool = only_bot_turn_states
        # Bots
        bot_count: int = initial_state.num_of_units
        self.bots: Sequence[BaseBot] = bot_getter(bot_count)
        # Bot timers
        self.bot_timer: TurnTimer = TurnTimer(bot_count)
        # Once everything is ready, allow bots to prepare
        for bot in self.bots:
            bot.setup(initial_state)
        # Skip to the first bot's turn if set to do so
        assert self.state.round_count == 0
        if only_bot_turn_states:
            self.play_state()
            assert self.state.round_count == 1

    # History
    @property
    def state(self) -> State:
        """The current state."""
        return self.__current_state

    @property
    def previous_state(self) -> Union[State, None]:
        """The last state before the current one (or None if currently at first state)."""
        if self.history_size <= 1:
            return None
        return self.history[self.history_size-2]

    @property
    def history_size(self):
        return len(self.history)

    # Play
    def play_state(self):
        """Plays the next state, and adds it to history."""
        state = self.state
        self.log_state(state)
        if state.end_of_round:
            new_state = state.increment_round()
            self.logger(f'Death radius: {new_state.death_radius}')
        else:
            unit_id = state.current_unit
            action = self._get_bot_action(unit_id, state)
            self.logger(f'Applying {action} to state')
            if self.__only_bot_turn_states:
                new_state = state.apply_action(action)
            else:
                new_state = state.apply_action_no_round_increment(action)
                if not new_state.is_last_action_legal:
                    self.logger(f'ILLEGAL: {action}')
        self.__current_state = new_state
        self.history.append(new_state)
        if new_state.round_count >= self.bot_timer.round_count:
            self.bot_timer.add_round()

    def play_states(self, count: int):
        """Plays a number of states."""
        while not self.state.game_over and count:
            self.play_state()
            count -= 1

    def play_all(self):
        """Plays the battle to completion."""
        while not self.state.game_over:
            self.play_state()

    def play_to_next_round(self):
        """Plays until the first state in the next round."""
        start_round = self.state.round_count
        while not self.state.game_over and self.state.round_count == start_round:
            self.play_state()

    def _get_bot_action(self, unit_id: int, state: State):
        state = state.copy()
        bot = self.bots[unit_id]
        pingpong_desc = f'{bot} poll_action (step {state.step_count})'
        def add_bot_time(elapsed):
            self.bot_timer.add_time(unit_id, elapsed)
        with pingpong(pingpong_desc, logger=self.logger, return_elapsed=add_bot_time):
            action = bot.poll_action(state)
        self.logger(LINEBR)
        self.logger(f'Received action: {action}')
        assert isinstance(action, Action)
        return action

    # Logging
    def logger(self, text: str):
        if LOGIC_DEBUG:
            glogger(text)

    def log_state(self, state: State):
        """Log a quick summary of the current state."""
        self.logger('\n'.join([
            LINEBR,
            ' '.join([
                f'Step: {str(state.step_count):^4}',
                f'Turn: {str(state.turn_count):^4}',
                f'Round: {str(state.round_count):^3}',
                '|',
                f'{self.get_state_str(state)}',
                ]),
            LINEBR,
        ]))

    def get_state_str(self, state: State) -> str:
        """A string representation of the type of state (bot turn / end of round)."""
        if state.end_of_round:
            return 'end of round'
        assert state.current_unit is not None
        return f"{self.bots[state.current_unit].gui_label}'s turn"

    def get_unit_str(self, unit_id: int) -> str:
        """An internal repr for a unit."""
        return self.bots[unit_id].gui_label

    # Miscallaneous
    @property
    def winner(self) -> Union[int, None]:
        """Returns the unit id that won, or None if draw or game isn't over."""
        return self.state.winner

    @property
    def losers(self) -> Union[Sequence[int], None]:
        """Returns a list of unit ids that did not win, or None if game isn't over."""
        if self.state.game_over:
            return [b for b in self.bots if b.id != self.winner]
        return None


class TurnTimer:
    """A class for keeping track of calculation times for multiple bots over
    the course of multiple turns."""

    def __init__(self, num_of_units: int):
        self.num_of_units: int = num_of_units
        self.round_timers: np.ndarray = np.zeros((1, num_of_units), dtype=np.float64)

    @property
    def all_times(self) -> np.ndarray:
        """Return the full table of times (numpy array). Not a copy.

        The ndarray shape will be (num_of_rounds, num_of_units), such that every
        element in the array represents the time that unit has in that round.
        """
        return self.round_timers

    def rounds_played(self, unit_id: int) -> int:
        return int(np.sum(self.round_timers[:, unit_id] > 0))

    def total(self, unit_id: int) -> float:
        return float(np.sum(self.round_timers[:, unit_id]))

    def mean(self, unit_id: int) -> float:
        """Returns the mean of unit_id. Assumes rounds with 0.0 time do not count."""
        rounds_played = self.rounds_played(unit_id)
        if rounds_played > 0:
            return float(self.total(unit_id) / rounds_played)
        return 0.0

    def max(self, unit_id: int) -> float:
        return float(np.max(self.round_timers[:, unit_id]))

    @property
    def round_count(self) -> int:
        return len(self.round_timers)

    def add_round(self):
        new_row = np.zeros(self.num_of_units, dtype=np.float64)
        self.round_timers = np.vstack((self.round_timers, new_row))

    def add_time(self, unit_id: int, time: float, round: Optional[int] = None):
        if round is None:
            round = self.round_count - 1
        self.round_timers[round, unit_id] += time
