"""Specifications and functions for interfacing different parts of the program.

# API for Bot Developers

This module collects many commonly useful attributes from all over for the
convenience of bot developers, and makes them available directly in the
`botroyale` package.

This means that for most use cases, it is enough to import `botroyale` alone.
For example:
```python
import botroyale as br

# Creating my own bot
class MyBot(br.BaseBot):
    NAME = "mybot"

    def poll_action(self, state: br.State) -> br.Action:
        return br.Idle()

# Register my bot
br.register_bot(MyBot)

# Run the GUI app (with "mybot" being selectable)
br.run_gui()
```

### All available attributes
- `botroyale.api.run_gui`
- `botroyale.api.bots.BaseBot`
- `botroyale.api.bots.register_bot`
- `botroyale.api.bots.BOTS`
- `botroyale.api.bots.BotSelection`
- `botroyale.api.actions.Idle`
- `botroyale.api.actions.Move`
- `botroyale.api.actions.Jump`
- `botroyale.api.actions.Push`
- `botroyale.api.actions.Action`
- `botroyale.api.actions.MAX_AP`
- `botroyale.api.actions.REGEN_AP`
- `botroyale.logic.state.State`
- `botroyale.logic.battle.Battle`
- `botroyale.logic.maps.MAPS`
- `botroyale.logic.maps.get_map_state`
- `botroyale.util.hexagon.Hexagon`
- `botroyale.api.bots.CENTER`
- `botroyale.api.bots.center_distance`
<br>
### Useful modules
- `botroyale.api.bots`
- `botroyale.api.actions`
- `botroyale.util.hexagon`
- `botroyale.logic.state`
- `botroyale.logic.battle`
"""

from botroyale.util.hexagon import Hexagon
from botroyale.api.actions import (
    Action,
    Idle,
    Move,
    Jump,
    Push,
    MAX_AP,
    REGEN_AP,
)
from botroyale.api.bots import (
    BaseBot,
    register_bot,
    BotSelection,
    CENTER,
    center_distance,
    BOTS,
)
from botroyale.logic.maps import MAPS, get_map_state
from botroyale.logic.state import State
from botroyale.logic.battle import Battle


def run_gui():
    """Run the GUI app."""
    # We import from inside the function as a hotfix until the gui can be
    # imported without opening a window.
    from botroyale.run.gui import entry_point_gui

    entry_point_gui(args=[])


# Names to be available in botroyale/__init__.py
__all__ = [
    "run_gui",
    "BaseBot",
    "register_bot",
    "BOTS",
    "BotSelection",
    "Idle",
    "Move",
    "Jump",
    "Push",
    "Action",
    "MAX_AP",
    "REGEN_AP",
    "State",
    "Battle",
    "MAPS",
    "get_map_state",
    "Hexagon",
    "CENTER",
    "center_distance",
]
# Specify which names that are [not] documented -- useful for botroyale/__init__.py
__NOT_DOCUMENTED = [
    "MAX_AP",
    "REGEN_AP",
    "BOTS",
    "CENTER",
    "MAPS",
]
DOCUMENTED_API = [n for n in __all__ if n not in __NOT_DOCUMENTED]
# Do not show attributes in docs -- too cluttered, prefer the module docstring
__pdoc__ = {n: False for n in DOCUMENTED_API}
__pdoc__["run_gui"] = True
