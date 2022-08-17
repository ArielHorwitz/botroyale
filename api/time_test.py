"""
Home of `timing_test` - a tool for measuring calculation time of bots.
"""
from typing import Optional, Sequence, Mapping, NamedTuple
import numpy as np
from collections import namedtuple
import random
from api.logging import Logger, logger as glogger
from logic.battle_manager import BattleManager
from bots import NotFairError
from bots.idle_bot import DummyBot


class TimeResult(NamedTuple):
    mean: float
    """Mean calculation time"""
    max: float
    """Max calculation time"""


def timing_test(
        bots: Sequence[type],
        battle_count: int,
        shuffle_bots: bool = True,
        disable_logging: bool = True,
        verbose_results: bool = True,
        ) -> dict[str, TimeResult]:
    """A timing test for bots.

    Plays a number of battles and logs bot calculation times. Returns a dictionary of bot names to a `TimeResult` of calc time per turn.

    Asserts each bot specified in *bots* will play in every game. If more bots than specified are required, dummy bots will be supplied.

    Args:
        bots: List of bot classes.
        battle_count: Number of battles to play.
        shuffle_bots: Automatically shuffle the order of the bots for each battle.
        disable_logging: Disable logging during battles.
        verbose_results: Show time table of each battle.

    Returns:
        Dictionary of bot names mapped to a `TimeResult`.
    """
    bots = [b for b in bots if b.NAME != 'dummy']
    requested_bot_count = len(bots)
    battle_index = 0
    all_results = {bot.NAME: TimeResult([], []) for bot in bots}

    glogger(f'\n\n========== Timing Test ==========')
    glogger('Selected:\n'+'\n'.join(f'{i:>2} {b.NAME}' for i, b in enumerate(bots)))

    def get_bots(num_of_units):
        try:
            assert requested_bot_count <= num_of_units
        except AssertionError:
            raise NotFairError(f'Requested for {requested_bot_count} bots to play, but only {num_of_units} slots available.')
        selected_bot_classes = [*bots]
        missing_units = num_of_units - requested_bot_count
        selected_bot_classes.extend([DummyBot] * missing_units)
        if shuffle_bots:
            random.shuffle(selected_bot_classes)
        return selected_bot_classes

    def get_final_results(results):
        final_results = {}
        for bot_name, result in results.items():
            final_results[bot_name] = TimeResult(
                mean=np.mean(np.asarray(result.mean)),
                max=np.max(np.asarray(result.max)),
                )
        return final_results

    def print_final_results(results):
        glogger('\n\n========== Timing Test Results ==========')
        glogger('\n'.join([
            f'Played {battle_index+1:>3} / {battle_count:>3} battles.',
            'One of each bot played in each game.',
            'Mean represents the mean of means given by each game (itself a mean of turns).',
            'Max represents the maximum time the bot timed in a single turn over all games.',
            '\n',
            ]))
        for bot_name, result in results.items():
            glogger(f'{bot_name:<20}    Mean: {f"{result.mean:.3f}":>12} ms/t      Max: {f"{result.max:.3f}":>14} ms')
        glogger('\n_________________________________________')

    for battle_index in range(battle_count):
        battle = BattleManager(bot_classes_getter=get_bots, enable_logging=not disable_logging)

        glogger(f'\nPlaying battle {battle_index+1} / {battle_count} : {battle.description}')
        battle.play_all(print_progress=disable_logging)
        if verbose_results:
            glogger(f'Battle time results:\n{battle.get_timer_str()}')

        for uid, bot in enumerate(battle.bots):
            if type(bot) is DummyBot:
                continue
            all_results[bot.NAME].mean.append(battle.bot_timer.mean(uid))
            all_results[bot.NAME].max.append(battle.bot_timer.max(uid))
        print_final_results(get_final_results(all_results))

    final_results = get_final_results(all_results)
    return final_results
