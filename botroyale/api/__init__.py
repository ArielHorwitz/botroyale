"""Specifications and functions for interfacing different parts of the program.

## Common API definitions
This module collects many commonly useful names from all over for convenience of
bot developers, and makes them available directly in the `botroyale` package.

This means that for most use cases, it is enough to import `botroyale` alone.
For example:
```python
import botroyale as br

# Creating my own bot
class MyBot(br.BaseBot):
    NAME = "mybot"

    def poll_action(self, state: br.State) -> br.actions.Action:
        return br.actions.Idle()

# Register my bot
br.register_bot(MyBot)

# Create and play a new battle programatically
new_battle = br.Battle(
    bots=br.BotSelection(["mybot"]),
    initial_state=br.get_map_state("classic"),
)
new_battle.play_all()

# Run the GUI app (with "mybot" being selectable)
br.run_gui()
```

## Bots
The `botroyale.api.bots` module provides the `botroyale.api.bots.BaseBot` base
class for bots, the `botroyale.api.bots.BOTS` dictionary of available bots, and
the `botroyale.api.bots.BotSelection` class for selecting bots for battle.

## Actions
The `botroyale.api.actions` module provides definitions related to bot actions,
including the `botroyale.api.actions.Action` classes and AP values.

## Under The Hood
For more advanced usage, the `botroyale.logic` package contains more definitions
useful for bot developers.
"""

from botroyale.util.hexagon import Hex as get_hex
from botroyale.api import actions
from botroyale.api.bots import BaseBot, register_bot, BotSelection, CENTER
from botroyale.logic.maps import get_map_state
from botroyale.logic.state import State
from botroyale.logic.battle import Battle


def run_gui():
    """Run the GUI app."""
    # We import from inside the function as a hotfix until the gui can be
    # imported without opening a window.
    from botroyale.run.gui import run as _run_gui

    _run_gui()


# Names to be available in botroyale/__init__.py
__all__ = [
    "BaseBot",
    "register_bot",
    "run_gui",
    "actions",
    "State",
    "Battle",
    "get_map_state",
    "BotSelection",
    "get_hex",
    "CENTER",
]
# Specify which names that are [not] documented -- useful for botroyale/__init__.py
NOT_DOCUMENTED = [
    "actions",
    "CENTER",
]
DOCUMENTED = [n for n in __all__ if n not in NOT_DOCUMENTED]
# Filtering out undocumented items raises a warning
__pdoc__ = {n: False for n in DOCUMENTED}
