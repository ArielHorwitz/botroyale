from typing import Optional, Sequence, Callable
import random
from pkgutil import iter_modules
from importlib import import_module
from util import PROJ_DIR
from api.bots import BaseBot


BOTS_DIR = PROJ_DIR / 'bots'


class NotFairError(Exception):
    pass


def get_bot_classes(
        total_slots: int,
        selection: Optional[Sequence[str]] = None,
        ignore: Optional[Sequence[str]] = None,
        include_testing: bool = False,
        keep_fair: bool = True,
        no_dummies: bool = False,
        all_play: bool = False,
        ) -> list[type]:
    """Returns a list of bot classes.

    total_slots         -- number of bots to return
    selection           -- list of bot names to select from (will select from all bots if no selection provided)
    ignore              -- list of bot names to remove from selection
    include_testing     -- include bots marked as "testing only"
    keep_fair           -- ensure an equal number of slots for each bot, filling remaining slots with dummy bots
    no_dummies          -- when keep_fair is true, ensure that no dummy bots are added
    all_play            -- ensure that every bot is selected at least once
    """
    available_bots = set(BOTS.keys())
    # Filter bots
    if selection is not None:
        available_bots &= set(selection)
    if ignore is not None:
        available_bots -= set(ignore)
    if not include_testing:
        testing_only = {b for b in available_bots if BOTS[b].TESTING_ONLY}
        available_bots -= testing_only

    # Count slots
    total_bots = len(available_bots)
    if total_bots == 0:
        raise NotFairError(f'Found 0 bots to fill {total_slots} slots. Selection: {selection} - {ignore} (minus testing: {not include_testing})')
    slots_per_bot = int(total_slots / total_bots)


    # Fill slots
    if slots_per_bot < 1:
        # We have more bots than slots - choose a random sample, size of total_slots
        if all_play:
            raise NotFairError(f'Requested for all {total_bots} bots to play, but only {total_slots} slots available.')
        selected_bots = list(available_bots)
        random.shuffle(selected_bots)
        selected_bots = selected_bots[:total_slots]
    else:
        # We have enough slots for all bots
        selected_bots = list(available_bots) * slots_per_bot
        remaining_slots = total_slots - len(selected_bots)
        if remaining_slots:
            if keep_fair and no_dummies:
                raise NotFairError(f'Requested to keep fair and no dummies, but we have {total_slots} total slots for {len(selected_bots)} bots ({remaining_slots} slots remainder).')
            elif keep_fair:
                # Fill with dummies
                fill = ['dummy'] * remaining_slots
            else:
                # Fill with as many different bots as we can fit
                fill = list(available_bots)
                random.shuffle(fill)
                fill = fill[:remaining_slots]
            selected_bots.extend(fill)

    # Convert to classes
    bot_classes = []
    for bot_name in selected_bots:
        bot_classes.append(BOTS[bot_name])
    random.shuffle(bot_classes)

    assert len(bot_classes) == total_slots
    return bot_classes


def bot_getter(**kwargs) -> Callable[[int], list[type]]:
    """Returns a callable to `get_bot_classes` with preconfigued kwargs.
    The statement `bot_getter()` (the return value) is functionally equivalent
    to `get_bot_classes` (the function name).

    Example usage:

    `bot_getter = get_bots(selection=['random', 'idle'], include_testing=True)`
    `Battle(bot_classes_getter=bot_getter)`
    """
    def bot_getter_inner(slots: int) -> list[type]:
        return get_bot_classes(slots, **kwargs)
    return bot_getter_inner


def _bot_importer(get_legend: bool = False) -> dict[str, type]:
    """Imports and returns bot names and classes from modules in the bots package."""
    bots = {}
    for (finder, module_name, ispkg) in iter_modules([str(BOTS_DIR)]):
        module = import_module(f"{__name__}.{module_name}")
        if hasattr(module, "BOT"):
            module_bots = [getattr(module, "BOT")]
        elif hasattr(module, "BOTS"):
            module_bots = getattr(module, "BOTS")
        else:
            continue
        for bot in module_bots:
            assert issubclass(bot, BaseBot)
            if bot.NAME in bots:
                raise KeyError(f'Bot name: "{bot.NAME}" (from module: {module_name}) already in use.')
            bots[bot.NAME] = bot
    return bots


BOTS = _bot_importer()
assert 'dummy' in BOTS  # There should always be at least one bot, let it be a dummy
