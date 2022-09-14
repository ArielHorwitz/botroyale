"""Bot definitions and functions.

## BaseBot and Registration
Every bot in Bot Royale must subclass from `BaseBot`. Once defined, you must
register them using `register_bot` to make them available for play. Registration
is local to runtime (as long as the script is running), so we must then run the
GUI app and select the bot.
```python
import botroyale as br

class MyBot(br.BaseBot):
    NAME = "mybot"

    def poll_action(self, state: br.State) -> br.actions.Action:
        return br.actions.Idle()

br.register_bot(MyBot)
br.run_gui()  # "mybot" will be available for selection
```
Instead of running the GUI app, we can also select them for custom battles (see
below).

## Programmatic Bot Selection
A `botroyale.logic.battle.Battle` object will collect bot classes from a given
`BotSelection` object, initialize them and call their `BaseBot.setup` method
with the battle's first `botroyale.logic.state.State` object (before any turn
is to be played).

To manually create a battle that will include a particular bot, something like
this should suffice:
```python
import botroyale as br
from botroyale.api.bots import BotSelection

class MyBot(br.BaseBot):
    NAME = "mybot"

br.register_bot(MyBot)
battle = br.Battle(bots=br.BotSelection(["mybot"]))
battle.play_all()
print(f"Winner: {battle.winner}")  # May be None in case of draw
```

## Available Bots
To see all bots that are registered see the `BOTS` dictionary, which maps each
bot name to their class definition.
"""
from typing import Optional, Any, Sequence, TypeVar
import random
from pkgutil import iter_modules
from importlib import import_module
from botroyale.util import PACKAGE_DIR
from botroyale.util.hexagon import Hexagon, ORIGIN
from botroyale.api.logging import logger as glogger
from botroyale.api.actions import Action, Idle
from botroyale.logic.state import State


# MISCELLANEOUS
VFXArgs = dict[str, Any]
VFXArgsList = list[VFXArgs]


CENTER: Hexagon = ORIGIN
"""Map center. Alias for `botroyale.util.hexagon.ORIGIN`."""


def center_distance(hex: Hexagon) -> int:
    """Returns distance of *hex* from the `CENTER`."""
    return ORIGIN.get_distance(hex)


# BOT CLASS
class BaseBot:
    """See module documenation for details."""

    NAME: str = "BaseBot"
    """The bot class name. Must be unique."""
    SPRITE: str = "bot"
    """The bot class sprite. Must be a name of a file in `assets/sprites`
    (without the .png extension)."""
    TESTING_ONLY: bool = False
    """Marks the bot class as a test bot. Indicates that it should not be used
    by default."""
    COLOR_INDEX: int = 0
    """The color (as an index) of the bot class. See `botroyale.logic.UNIT_COLORS`."""
    logging_enabled: bool = True
    """Enables `BaseBot.logger`."""

    def __init__(self, id: int):
        """Initialize the class."""
        self.id: int = id
        """The id of the bot in the battle.

        Is commonly used as an index in lists. Also known as `uid`."""
        self.name: str = self.NAME

    def setup(self, state: State):
        """Used by the bot to perform startup procedures.

        Called in round 0, before any turns have started. When subclassing,
        override this method to prepare the bot.

        Args:
            state: The initial state of the battle.
        """
        pass

    def poll_action(self, state: State) -> Action:
        """Called by a Battle on our turn.

        This method is where a bot "does their turn".

        Args:
            state: Current state of the battle.

        Returns:
            Action object.
        """
        return Idle()

    def gui_click(self, hex: Hexagon, button: str, mods: str) -> Optional[VFXArgsList]:
        """May be called when we are clicked on in the GUI.

        See: `botroyale.logic.battle_manager.BattleManager.handle_hex_click`.

        Args:
            hex: The hex on which the unit was clicked.
            button: The name of the mouse button that was clicked with. May be
                one of: *left*, *right*, *middle*, *mouse1*, *mouse2*, etc.
            mods: A string representing the keyboard modifiers that were pressed
                during the mouse clicked.

        Returns:
            None, or a list of dictionaries of vfx keyword arguments.
                See `botroyale.api.gui.VFX`.
        """
        vfx = {"left": "green", "right": "red"}.get(button, "blue")
        return [{"name": f"mark-{vfx}", "hex": hex}]

    def logger(self, text: str):
        """Logger for the bot.

        Is enabled/disabled by `BaseBot.logging_enabled`.
        """
        if self.logging_enabled:
            glogger(text)

    def __repr__(self):
        """Repr."""
        return f"<Bot #{self.id} {self.name}>"

    @property
    def gui_label(self):
        """Formatted name with uid."""
        id_label = f"#{self.id}"
        return f"{id_label:>3} {self.name}"


BotLike = TypeVar("BotLike", bound=BaseBot)
"""A type variable for subclasses of `BaseBot`."""


# BOT SELECTION
class NotFairError(Exception):
    """Raised when a request for bots cannot be fulfilled fairly."""

    pass


class BotSelection:
    """An object for providing bots to `botroyale.logic.battle.Battle`."""

    def __init__(
        self,
        selection: Optional[Sequence[str]] = None,
        ignore: Optional[Sequence[str]] = None,
        keep_fair: bool = False,
        no_dummies: bool = False,
        all_play: bool = False,
        max_repeat: Optional[int] = None,
    ):
        """Initialize the class.

        The configuration given by the initialization arguments are used later
        by `BotSelection.get_bots`.

        Args:
            selection: List of bot names to select from. None will select from
                all bots (that are not marked at "testing").
            ignore: List of bot names to ignore (remove from selection).
            keep_fair: Ensure that an equal number of each bot is selected.
                Fills remaining slots with dummy bots.
            no_dummies: If *keep_fair* is True, will raise `NotFairError` if
                dummy bots are required to keep fair.
            all_play: If true, will raise `NotFairError` if not all bots in
                selection can be slotted.
            max_repeat: Ensure that at most *max_repeat* number of each bot is
                selected.
        """
        self.selection = selection
        self.ignore = ignore
        self.keep_fair = keep_fair
        self.no_dummies = no_dummies
        self.all_play = all_play
        self.max_repeat = max_repeat

    def get_bots(self, total_slots: int) -> list[BotLike]:
        """Return *total_slots* number of bots based on our configuration.

        Args:
            total_slots: Number of bot classes to return.

        Returns:
            List of bot classes.

        Raises:
            `NotFairError` if cannot satisfy providing *total_slots* bot classes
                given our configuration.
        """
        available_bots = set(BOTS.keys())
        # Filter bots
        if self.selection is not None:
            available_bots &= set(self.selection)
        else:
            testing_only = {b for b in available_bots if BOTS[b].TESTING_ONLY}
            available_bots -= testing_only
        if self.ignore is not None:
            available_bots -= set(self.ignore)
        # Fill slots
        selected_bots = self._fill_slots(
            total_slots,
            available_bots,
            all_play=self.all_play,
            keep_fair=self.keep_fair,
            no_dummies=self.no_dummies,
            max_repeat=self.max_repeat,
        )
        # Convert to classes
        bot_classes = []
        for bot_name in selected_bots:
            bot_classes.append(BOTS[bot_name])
        random.shuffle(bot_classes)
        assert len(bot_classes) == total_slots
        return bot_classes

    @staticmethod
    def _fill_slots(
        total_slots: int,
        available_bots: set[str],
        all_play: bool,
        keep_fair: bool,
        no_dummies: bool,
        max_repeat: Optional[int] = None,
    ) -> list[str]:
        """Fill slots based on a set of bot names."""
        # Count slots
        total_bots = len(available_bots)
        if total_bots == 0:
            raise NotFairError(f"Found 0 bots to fill {total_slots} slots.")
        slots_per_bot = int(total_slots / total_bots)
        if max_repeat is not None:
            slots_per_bot = min(max_repeat, slots_per_bot)

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
            if no_dummies and (keep_fair or max_repeat):
                reason = "to keep fair" if keep_fair else f"max {max_repeat} per bot"
                raise NotFairError(
                    f"Requested {reason} and no dummies, but we have "
                    f"{total_slots} total slots for {len(selected_bots)} bots "
                    f"({remaining_slots} slots remainder)."
                )
            elif keep_fair or max_repeat:
                # Fill with dummies
                fill = ["dummy"] * remaining_slots
            else:
                # Fill with as many different bots as we can fit
                fill = list(available_bots)
                random.shuffle(fill)
                fill = fill[:remaining_slots]
            selected_bots.extend(fill)
        return selected_bots

    def __repr__(self):
        """Repr."""
        options = []
        if self.ignore:
            options.append(f"{len(self.ignore)} ignored")
        if self.keep_fair:
            options.append("fair")
        if self.no_dummies:
            options.append("no dummies")
        if self.all_play:
            options.append("all play")
        if self.max_repeat:
            options.append(f"max repeat {self.max_repeat}")
        options = ": " + ", ".join(options) if options else ""
        return f"<BotSelection {len(self.selection)} selected{options}>"


# BOT IMPORTING
BOTS_DIR = PACKAGE_DIR / "bots"
BOTS_PACKAGE = "botroyale.bots"


def _bot_importer(get_legend: bool = False) -> dict[str, type]:
    """Import and return bot names and classes from modules in the bots package."""
    bots = {}
    for (finder, module_name, ispkg) in iter_modules([str(BOTS_DIR)]):
        module = import_module(f"{BOTS_PACKAGE}.{module_name}")
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
"""A dictionary of registered bot names mapped to bot classes."""


# There should always be at least one bot, let it be a dummy
assert "dummy" in BOTS


def register_bot(bot_class: BotLike):
    """Register a bot for botroyale.

    This registration is only valid for runtime. You must register every time
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
