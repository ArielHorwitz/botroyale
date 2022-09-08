"""Home of the bots.

Submodules of this package (not shown here) contain the bot classes (subclasses
of `botroyale.api.bots.BaseBot`).
"""
from typing import Optional, Sequence, Callable
import random
from pkgutil import iter_modules
from importlib import import_module
from botroyale.util import PACKAGE_DIR
from botroyale.api.bots import BaseBot, BotLike


BOTS_DIR = PACKAGE_DIR / "bots"


class NotFairError(Exception):
    """Raised when a request for bots cannot be fulfilled fairly."""

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

    Will return at least two bots or raise a `NotFairError`.

    Args:
        total_slots: The number of bot classes to return.
        selection: List of bot names to select from (will select from all bots
            if no selection provided).
        ignore: List of bot names to remove from *selection*.
        include_testing: Include bots marked as `botroyale.api.bots.BaseBot.TESTING_ONLY`.
        keep_fair: Ensure an equal number of slots for each bot, filling
            remaining slots with dummy bots.
        no_dummies: When *keep_fair* is true, ensure that no dummy bots are
            added.
        all_play: Ensure that every bot is selected at least once.

    Returns:
        List of bot classes. Will have at least one bot.

    Raises:
        NotFairError: Raised when no bots could be collected given the
            arguments.
        NotFairError: Raised when *fair_play* is true and not all bots in
            *selection* can be returned at least once.
        NotFairError: Raised when *fair_play* and *no_dummies* are true, and
            *selection* does not divide with *total_slots* without remainder.
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

    # Fill slots
    selected_bots = _fill_slots(
        total_slots,
        available_bots,
        all_play,
        keep_fair,
        no_dummies,
    )

    # Convert to classes
    bot_classes = []
    for bot_name in selected_bots:
        bot_classes.append(BOTS[bot_name])
    random.shuffle(bot_classes)
    assert len(bot_classes) == total_slots
    return bot_classes


def bot_getter(**kwargs) -> Callable[[int], list[type]]:
    """A more convenient way to use `get_bot_classes`.

    The statement *bot_getter()* (return value of this function) is functionally
    equivalent to *get_bot_classes* (the `get_bot_classes` function name).

    <u>__Example usage:__</u>
    ```python
    get_bots = bots.bot_getter(
        selection=['random', 'idle'],
        include_testing=True,
    )
    logic.battle.Battle(bot_classes_getter=get_bots)
    ```

    Which is equivalent to:
    ```python
    def get_bots(n):
        return bots.get_bot_classes(
            n,
            selection=['random', 'idle'],
            include_testing=True,
        )
    logic.battle.Battle(bot_classes_getter=get_bots)
    ```

    Args:
        Equivalent to arguments of `get_bot_classes` (not including
            `total_slots`).

    Returns:
        A callable to `get_bot_classes` with preconfigued arguments.
    """

    def bot_getter_inner(slots: int) -> list[type]:
        return get_bot_classes(slots, **kwargs)

    return bot_getter_inner


def _fill_slots(
    total_slots: int,
    available_bots: set[str],
    all_play: bool,
    keep_fair: bool,
    no_dummies: bool,
) -> list[str]:
    """Fill slots based on a set of bot names."""
    # Count slots
    total_bots = len(available_bots)
    if total_bots == 0:
        raise NotFairError(f"Found 0 bots to fill {total_slots} slots.")
    slots_per_bot = int(total_slots / total_bots)

    # If we have more bots than slots - choose a random sample, size of total_slots
    if slots_per_bot < 1:
        if all_play:
            raise NotFairError(
                f"Requested for all {total_bots} bots to play, but only "
                f"{total_slots} slots available."
            )
        selected_bots = list(available_bots)
        random.shuffle(selected_bots)
        return selected_bots[:total_slots]

    # We have enough slots for all bots
    selected_bots = list(available_bots) * slots_per_bot
    remaining_slots = total_slots - len(selected_bots)
    if remaining_slots:
        if keep_fair and no_dummies:
            raise NotFairError(
                "Requested to keep fair and no dummies, but we have "
                f"{total_slots} total slots for {len(selected_bots)} bots "
                f"({remaining_slots} slots remainder)."
            )
        elif keep_fair:
            # Fill with dummies
            fill = ["dummy"] * remaining_slots
        else:
            # Fill with as many different bots as we can fit
            fill = list(available_bots)
            random.shuffle(fill)
            fill = fill[:remaining_slots]
        selected_bots.extend(fill)
    return selected_bots


def _bot_importer(get_legend: bool = False) -> dict[str, type]:
    """Import and return bot names and classes from modules in the bots package."""
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
                raise KeyError(
                    f'Bot name: "{bot.NAME}" (from module: {module_name}) '
                    "already in use."
                )
            bots[bot.NAME] = bot
    return bots


BOTS: dict[str, type] = _bot_importer()
"""A dictionary of bot names mapped to bot classes."""


# There should always be at least one bot, let it be a dummy
assert "dummy" in BOTS


def register_bot(bot_class: BotLike):
    """Register a bot for botroyale.

    This registration is only valid for runtime. You must re-register every time
    the script is run.

    Args:
        bot_class: The class of the bot to register.
    """
    if not issubclass(bot_class, BaseBot):
        raise TypeError("Bots must subclass from botroyale.api.bots.BaseBot.")
    bot_name = bot_class.NAME
    if bot_name in BOTS:
        raise KeyError(f'The name "{bot_name}" is already taken.')
    BOTS[bot_name] = bot_class
    print(f"Registered bot: {bot_name} ({bot_class})")


# Do not add the submodules (bot code) to documentation.
__pdoc__ = {
    module_name: False for (finder, module_name, ispkg) in iter_modules([str(BOTS_DIR)])
}
# Do include the standard simple bots
# __pdoc__['idle_bot'] = True
# __pdoc__['random_bot'] = True
