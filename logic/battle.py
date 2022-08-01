from typing import Union, Optional, Sequence, Callable
import numpy as np
from api.logging import Logger, logger as glogger
from api.bots import BaseBot
from api.actions import Action
from bots import get_bot_classes
from logic.maps import get_map_state, DEFAULT_MAP_NAME
from logic.state import State
from util.time import pingpong
from util.settings import Settings


LINEBR = '='*75


class Battle:
    """The Battle manages the states and bots of a single battle.

    It remembers a history of states as well as the current state.
    It also creates the bots and polls them for an action on their turn.
    """

    def __init__(self,
            initial_state: Optional[State] = None,
            bot_classes_getter: Callable[[int], Sequence[type]] = get_bot_classes,
            enable_logging: bool = True,
            only_bot_turn_states: bool = True,
            threshold_bot_block_seconds: float = 20.0,
            ):
        """
        initial_state -- The first state of the battle. If initial_state is not
        provided, it will be generated using the map generator based on
        configured settings.

        bot_classes_getter -- A function that takes an integer and returns that
        many bots classes. If bot_classes_getter is not provided, the default
        `get_bot_classes` will be used that is based on configured settings.

        enable_logging -- Passing False will disable the logger for the battle.
        It also disables logging while calling the bot_classes_getter.

        only_bot_turn_states -- Determines whether to skip "end_of_round" states
        and other states that are not expecting an action from a unit. This is
        useful for bot developers who may not care about "mid-states" and only
        care to see when a bot needs to take action. This essentially determines
        whether actions are applied to states with `apply_action` or
        `apply_action_no_round_increment`.

        threshold_bot_block_seconds -- Threshold of calculation time for bots to
        trigger a warning in the log.
        """
        self.enable_logging = enable_logging
        self._map_name = 'Custom initial state'
        if initial_state is None:
            initial_state = get_map_state()
            self._map_name = DEFAULT_MAP_NAME
        self.logger(f'Making battle on map: {self._map_name}')
        self.__current_state: State = initial_state
        self.history: list[State] = [initial_state]
        self.__only_bot_turn_states: bool = only_bot_turn_states
        self.__threshold_bot_block_ms: float = threshold_bot_block_seconds * 1000
        # Bots
        bot_count = initial_state.num_of_units
        self.bot_timer: TurnTimer = TurnTimer(bot_count)
        with Logger.set_logging_temp(enable_logging):
            bot_classes = bot_classes_getter(bot_count)
        assert len(bot_classes) == bot_count
        self.bots = tuple(bcls(i) for i, bcls in enumerate(bot_classes))
        # Allow bots to prepare
        for uid, bot in enumerate(self.bots):
            assert isinstance(bot, BaseBot)
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

    def play_all(self, disable_logging: bool = False, print_progress: bool = False):
        """Plays the battle to completion.

        disable_logging     -- disable logging globally while playing
        print_progress      -- disable logging globally while playing and print
                                    a progress bar to console
        """
        def print_progress_bar():
            rc = self.state.round_count
            done = '█' * rc
            remaining = '░' * (self.state.death_radius - 1)
            pbar = f'{done}{remaining}  ({rc} / {rc+self.state.death_radius-1} rounds)'
            print(f'\r{pbar}', end='')

        if print_progress:
            disable_logging = True
            print_progress_bar()
        last_rc = self.state.round_count
        with Logger.set_logging_temp(not disable_logging):
            while not self.state.game_over:
                last_rc = self.state.round_count
                self.play_state()
                if print_progress and self.state.round_count > last_rc:
                    print_progress_bar()
        if print_progress:
            print('')

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
        ttime = self.bot_timer.get_time(unit_id)
        if ttime > self.__threshold_bot_block_ms:
            self.logger(f'BLOCK TIME WARNING : {bot} has taken {ttime/1000:.2f} seconds this turn')
        return action

    # Logging
    def logger(self, text: str):
        if self.enable_logging:
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
    def losers(self) -> Union[list[int], None]:
        """Returns a list of unit ids that did not win, or None if game isn't over."""
        if self.state.game_over:
            return [b.id for b in self.bots if b.id != self.winner]
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
        """Return the number of rounds that have times recorded for a unit."""
        return int(np.sum(self.round_timers[:, unit_id] > 0))

    def total(self, unit_id: int) -> float:
        """Return the total time recorded for a unit."""
        return float(np.sum(self.round_timers[:, unit_id]))

    def mean(self, unit_id: int) -> float:
        """Return the mean of times recorded for a unit.

        Assumes rounds with 0.0 time do not count.
        """
        rounds_played = self.rounds_played(unit_id)
        if rounds_played > 0:
            return float(self.total(unit_id) / rounds_played)
        return 0.0

    def max(self, unit_id: int) -> float:
        """Return the max of times recorded for a unit."""
        return float(np.max(self.round_timers[:, unit_id]))

    @property
    def round_count(self) -> int:
        """Number of rounds in the table."""
        return len(self.round_timers)

    def add_round(self):
        """Add a new round to the table."""
        new_row = np.zeros(self.num_of_units, dtype=np.float64)
        self.round_timers = np.vstack((self.round_timers, new_row))

    def add_time(self, unit_id: int, time: float, round: Optional[int] = None):
        """Add time for a unit at a given round.

        Will use the last round if none is provided.
        """
        if round is None:
            round = self.round_count - 1
        self.round_timers[round, unit_id] += time

    def get_time(self, unit_id: int, round: Optional[int] = None) -> float:
        """Get the time recorded for a unit at a given round.

        Will use the last round if none is provided.
        See also: TurnTimer.all_times
        """
        if round is None:
            round = self.round_count - 1
        return float(self.round_timers[round, unit_id])
