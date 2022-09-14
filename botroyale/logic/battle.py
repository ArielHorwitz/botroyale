"""Home of the `botroyale.logic.battle.Battle` class.

The `Battle` class is used to manage the states and bots of a full battle. Bot
developers will use this module when playing battles programatically (without
the GUI).

## Setup and Play
The Battle collects bots from a given `botroyale.api.bots.BotSelection` object,
initializes them and calls their `botroyale.api.bots.BaseBot.setup` method
before any turns begin. When it is requested to play states, the Battle will
manage calling the bot's `botroyale.api.bots.BaseBot.poll_action` method on
their turn and applying the action. See: `Battle.play_all`.

## State History
The latest state in a Battle can be found using `Battle.state`. All previous
states instances reside in the `Battle.history` list.

## Example Usage
```python
new_battle = br.Battle(
    initial_state=br.get_map_state("classic")
    bots=br.BotSelection(["mybot", "mybot2"])
)
new_battle.play_all()
print(f"Winner: {new_battle.winner}")  # May be None in case of draw
```
"""
from typing import Optional
import sys
import traceback
import numpy as np
from botroyale.api.logging import Logger, logger as glogger
from botroyale.api.bots import BaseBot, BotSelection
from botroyale.api.actions import Action
from botroyale.logic.maps import get_map_state
from botroyale.logic.state import State
from botroyale.util.time import pingpong


LINEBR = "=" * 75


class Battle:
    """See module documentation for details."""

    def __init__(
        self,
        initial_state: Optional[State] = None,
        bots: Optional[BotSelection] = None,
        description: str = "No description set",
        enable_logging: bool = True,
        enable_bot_logging: Optional[bool] = None,
        only_bot_turn_states: bool = True,
        threshold_bot_block_seconds: float = 20.0,
    ):
        """Initialize the class.

        Args:
            initial_state: The first state of the battle. If initial_state is
                not provided, it will be generated using the map generator based
                on configured settings.

            bots: A `botroyale.api.bots.BotSelection` object that provides bots.

            description: A description of the battle.

            enable_logging: Passing False will disable battle logs. Not
                including bots.

            enable_bot_logging: Passing False will disable the logger while
                bots are called. Defaults to the same value as *enable_logging*.

            only_bot_turn_states: Determines whether to skip `State.end_of_round`
                states and other states that are not expecting an action from a
                unit. This is useful for bot developers who may not care about
                states out of turn and only care to see when a bot needs to take
                action. This essentially determines whether actions are applied
                to states with `State.apply_action` or
                `State.apply_action_manual`.

            threshold_bot_block_seconds: Threshold of calculation time for bots
                to trigger a warning in the log.
        """
        self.enable_logging: bool = enable_logging
        """Enable logging of the battle itself."""
        if enable_bot_logging is None:
            enable_bot_logging = enable_logging
        self.enable_bot_logging: bool = enable_bot_logging
        """Enable logging for the bots."""
        self.description: str = description
        """A description of the battle."""
        if initial_state is None:
            with Logger.set_logging_temp(enable_logging):
                initial_state = get_map_state()
        self.__current_state: State = initial_state
        self.history: list[State] = [initial_state]
        """A list of states."""
        self.__only_bot_turn_states: bool = only_bot_turn_states
        self.__threshold_bot_block_ms: float = threshold_bot_block_seconds * 1000
        # Bots
        bot_count = initial_state.num_of_units
        self.bot_timer: TurnTimer = TurnTimer(bot_count)
        """A `TurnTimer` object for keeping track of bot calculation times."""
        if bots is None:
            bots = BotSelection()
        with Logger.set_logging_temp(enable_bot_logging):
            bot_classes = bots.get_bots(bot_count)
        assert len(bot_classes) == bot_count
        self.bots: tuple[BaseBot, ...] = tuple(
            bcls(i) for i, bcls in enumerate(bot_classes)
        )
        """Tuple of bot instances."""
        # Allow bots to prepare
        with Logger.set_logging_temp(enable_bot_logging):
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
    def previous_state(self) -> Optional[State]:
        """The state before the current one (or None if currently at first state)."""
        if self.history_size <= 1:
            return None
        return self.history[self.history_size - 2]

    @property
    def history_size(self):
        """Size of state history."""
        return len(self.history)

    # Play
    def play_state(self):
        """Plays the next state, and adds it to history."""
        state = self.state
        self.log_state(state)
        if state.end_of_round:
            new_state = state.increment_round()
            self.logger(f"Death radius: {new_state.death_radius}")
        else:
            unit_id = state.current_unit
            action = self._get_bot_action(unit_id, state)
            if action is not None:
                # Bot returned an action, apply.
                self.logger(f"Applying {action} to state")
                if self.__only_bot_turn_states:
                    new_state = state.apply_action(action)
                else:
                    new_state = state.apply_action_manual(action)
                    if not new_state.is_last_action_legal:
                        self.logger(f"ILLEGAL: {action}")
            else:
                # Bot failed to return an action, kill.
                self.logger(f"Killing {self.bots[unit_id]}...")
                if self.__only_bot_turn_states:
                    new_state = state.apply_kill_unit()
                else:
                    new_state = state.apply_kill_unit_manual()
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

        Args:
            disable_logging: Disable logging globally while playing.
            print_progress: Disable logging globally while playing and print a
                progress bar to console.
        """

        def print_progress_bar():
            rc = self.state.round_count
            done = "█" * rc
            remaining = "░" * (self.state.death_radius - 1)
            pbar = f"{done}{remaining}  ({rc} / {rc+self.state.death_radius-1} rounds)"
            print(f"\r{pbar}", end="")

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
            print("")

    def _get_bot_action(self, unit_id: int, state: State) -> Optional[Action]:
        """Call the bot's `botroyale.api.bots.BaseBot.poll_action` to get their action.

        Args:
            unit_id: uid of the unit
            state: current state of the battle

        Returns:
            `botroyale.api.actions.Action` if *poll_action* is successful.
            None if there was an exception.
        """
        state = state.copy()
        bot = self.bots[unit_id]
        pingpong_desc = f"{bot} poll_action (step {state.step_count})"

        def add_bot_time(elapsed):
            self.bot_timer.add_time(unit_id, elapsed)

        with pingpong(pingpong_desc, logger=self.logger, return_elapsed=add_bot_time):
            try:
                with Logger.set_logging_temp(self.enable_bot_logging):
                    action = bot.poll_action(state)
                assert isinstance(action, Action)
            except Exception as e:
                formatted_exc = "".join(traceback.format_exception(*sys.exc_info()))
                self.logger(f"CRASH {bot}: {e}\n\n{formatted_exc}")
                return None
        self.logger(LINEBR)
        self.logger(f"Received action: {action}")
        ttime = self.bot_timer.get_time(unit_id)
        if ttime > self.__threshold_bot_block_ms:
            self.logger(
                f"BLOCK TIME WARNING : {bot} has taken {ttime/1000:.2f} "
                "seconds this turn"
            )
        return action

    # Logging
    def logger(self, text: str):
        """Logger for the battle."""
        if self.enable_logging:
            glogger(text)

    def log_state(self, state: State):
        """Log a quick summary of the current state."""
        self.logger(
            "\n".join(
                [
                    LINEBR,
                    " ".join(
                        [
                            f"Step: {str(state.step_count):^4}",
                            f"Turn: {str(state.turn_count):^4}",
                            f"Round: {str(state.round_count):^3}",
                            "|",
                            f"{self.get_state_str(state)}",
                        ]
                    ),
                    LINEBR,
                ]
            )
        )

    def get_state_str(self, state: State) -> str:
        """A string representation of the type of state (bot turn / end of round)."""
        if state.end_of_round:
            return "end of round"
        assert state.current_unit is not None
        return f"{self.bots[state.current_unit].gui_label}'s turn"

    def get_unit_str(self, unit_id: int) -> str:
        """An internal repr for a unit."""
        return self.bots[unit_id].gui_label

    # Miscallaneous
    @property
    def winner(self) -> Optional[int]:
        """Alias for `botroyale.logic.state.State.winner` of the current state."""
        return self.state.winner

    @property
    def losers(self) -> Optional[list[int]]:
        """Returns a list of unit ids that did not win, or None if game isn't over."""
        if self.state.game_over:
            return [b.id for b in self.bots if b.id != self.winner]
        return None


class TurnTimer:
    """Records calculation times for multiple bots over multiple turns."""

    def __init__(self, num_of_units: int):
        """Initialize the class."""
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
        """Get the time recorded for a unit at a given round (default: last round)."""
        if round is None:
            round = self.round_count - 1
        return float(self.round_timers[round, unit_id])
