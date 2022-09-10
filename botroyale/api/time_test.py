"""Home of `timing_test` - a tool for measuring calculation time of bots."""
from typing import Optional, Sequence, NamedTuple
import numpy as np
import random
from botroyale.api.logging import logger as glogger
from botroyale.logic.maps import get_map_state
from botroyale.logic.battle_manager import BattleManager
from botroyale.api.bots import NotFairError
from botroyale.bots.idle_bot import DummyBot


class TimeResult(NamedTuple):
    """Nametuple with fields (mean, max)."""

    mean: float
    """Mean calculation time"""
    max: float
    """Max calculation time"""


def timing_test(
    bots: Sequence[type],
    battle_count: int,
    map_name: Optional[str] = None,
    shuffle_bots: bool = True,
    disable_logging: bool = True,
    verbose_results: bool = True,
) -> dict[str, TimeResult]:
    """A timing test for bots.

    Plays a number of battles and logs bot calculation times. Asserts each bot
    specified in *bots* will play in every game. If more bots than specified are
    required, dummy bots will be supplied.

    Args:
        bots: List of bot classes.
        battle_count: Number of battles to play.
        map_name: Name of map to play on.
        shuffle_bots: Automatically shuffle the order of the bots for each battle.
        disable_logging: Disable logging during battles.
        verbose_results: Show time table of each battle.

    Returns:
        Dictionary of bot names mapped to a `TimeResult`.
    """
    bots = [b for b in bots if b.NAME != "dummy"]
    requested_bot_count = len(bots)
    battle_index = 0
    all_results = {bot.NAME: TimeResult([], []) for bot in bots}

    glogger("\n\n========== Timing Test ==========")
    glogger("Selected:\n" + "\n".join(f"{i:>2} {b.NAME}" for i, b in enumerate(bots)))

    def get_bots(num_of_units):
        try:
            assert requested_bot_count <= num_of_units
        except AssertionError:
            raise NotFairError(
                f"Requested for {requested_bot_count} bots to play, but only"
                f"{num_of_units} slots available."
            )
        selected_bot_classes = [*bots]
        missing_units = num_of_units - requested_bot_count
        selected_bot_classes.extend([DummyBot] * missing_units)
        if shuffle_bots:
            random.shuffle(selected_bot_classes)
        return selected_bot_classes

    for battle_index in range(battle_count):
        initial_state = get_map_state(map_name)
        battle = BattleManager(
            bot_classes_getter=get_bots,
            initial_state=initial_state,
            description=f"time test {battle_index+1} / {battle_count} @ {map_name}",
            enable_logging=not disable_logging,
            enable_bot_logging=not disable_logging,
        )

        glogger(f"\nPlaying battle : {battle.description}")
        battle.play_all(print_progress=disable_logging)
        if verbose_results:
            glogger(f"Battle time results:\n{battle.get_timer_str()}")

        for uid, bot in enumerate(battle.bots):
            if type(bot) is DummyBot:
                continue
            all_results[bot.NAME].mean.append(battle.bot_timer.mean(uid))
            all_results[bot.NAME].max.append(battle.bot_timer.max(uid))
        _print_final_results(
            _get_final_results(all_results),
            battle_index,
            battle_count,
        )

    final_results = _get_final_results(all_results)
    return final_results


def _get_final_results(results):
    final_results = {}
    for bot_name, result in results.items():
        final_results[bot_name] = TimeResult(
            mean=np.mean(np.asarray(result.mean)),
            max=np.max(np.asarray(result.max)),
        )
    return final_results


def _print_final_results(results, battle_index, battle_count):
    glogger("\n\n========== Timing Test Results ==========")
    glogger(
        "\n".join(
            [
                f"Played {battle_index+1:>3} / {battle_count:>3} battles.",
                "One of each bot played in each game.",
                "Mean represents the mean of means given by each game"
                "(itself a mean of turns).",
                "Max represents the maximum time the bot timed in a single"
                "turn over all games.",
                "\n",
            ]
        )
    )
    for bot_name, result in results.items():
        glogger(
            f'{bot_name:<20}    Mean: {f"{result.mean:.3f}":>12} ms/t      '
            f'Max: {f"{result.max:.3f}":>14} ms'
        )
    glogger("\n_________________________________________")
