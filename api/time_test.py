from typing import Optional, Sequence, Mapping
import numpy as np
from collections import namedtuple
import random
from api.logging import Logger, logger as glogger
from logic.battle_manager import BattleManager
from bots.idle_bot import DummyBot


TimeResult = namedtuple('TimeResult', ['mean', 'max'])


def timing_test(
        bots: Sequence[type],
        battle_count: int,
        shuffle_bots: Optional[bool] = True,
        disable_logging: Optional[bool] = True,
        ) -> Mapping[str, TimeResult]:
    """A timing test for bots.

    Plays a number of battles and logs bot calculation times. Returns a
    dictionary of bot names to a tuple of (mean, max) calc time per turn.

    Asserts each bot specified in `bots` will play in every game. If more bots
    than specified are required, dummy bots will be supplied.

    bots            -- a list of bot classes
    battle_count    -- number of battles to play
    shuffle_bots    -- automatically shuffle the order of the bots
    disable_logging -- disable logging during battles
    """
    bots = [b for b in bots if b.NAME != 'dummy']
    requested_bot_count = len(bots)
    def get_bots(num_of_units):
        assert requested_bot_count <= num_of_units
        selected_bot_classes = [*bots]
        missing_units = num_of_units - requested_bot_count
        selected_bot_classes.extend([DummyBot] * missing_units)
        if shuffle_bots:
            random.shuffle(selected_bot_classes)
        return selected_bot_classes

    glogger(f'\n\n========== Timing Test ==========')
    glogger('Selected:\n'+'\n'.join(f'- {i:>2} : {b.NAME}' for i, b in enumerate(bots)))
    remember_logger_enabled = Logger.enable_logging
    if disable_logging:
        Logger.enable_logging = False
    results = {bot.NAME: TimeResult([], []) for bot in bots}
    for battle_number in range(battle_count):
        battle = BattleManager(bot_classes_getter=get_bots)
        Logger.enable_logging = True
        glogger(f'\nPlaying battle {battle_number+1} / {battle_count} (map: {battle.map_name})...')
        battle.play_all(print_progress=True)
        glogger(battle.get_timer_str())
        if disable_logging:
            Logger.enable_logging = False
        for uid, bot in enumerate(battle.bots):
            if type(bot) == DummyBot:
                continue
            results[bot.NAME].mean.append(battle.bot_timer.mean(uid))
            results[bot.NAME].max.append(battle.bot_timer.max(uid))
    Logger.enable_logging = True
    glogger('\n\n========== Timing Test Results ==========')
    glogger(f'Played {battle_count} battles.\n')
    final_results = {}
    for bot_name, result in results.items():
        bot_mean = np.mean(np.asarray(result.mean))
        bot_max = np.max(np.asarray(result.max))
        final_results[bot_name] = TimeResult(bot_mean, bot_max)
        glogger(f'{bot_name:>25} : {f"{bot_mean:.3f}":>10} ms/t   Max: {f"{bot_max:.3f}":>10} ms')
    Logger.enable_logging = remember_logger_enabled
    return final_results
