"""Actions used by bots and game mechanics.

When in turn, bots will be polled for action via
`botroyale.api.bots.BaseBot.poll_action` and are required to return an `Action`
subclass instance. Each action has an AP cost and effect which determine if
using said action is legal at any given moment (see:
`botroyale.logic.state.State.apply_action` and
`botroyale.logic.state.State.check_legal_action`).

Bots regenerate 50 AP (`REGEN_AP`) per round and cannot have more than 100 AP
(`MAX_AP`) at any given moment.

## Available Actions
- `Idle` (*0 AP*): do nothing and end our turn.
- `Move` (*20 AP*): move to an adjascent tile.
- `Push` (*30 AP*): push a unit from an adjascent tile to the tile behind it.
- `Jump` (*45 AP*): move to a tile at a distance of 2 (ignoring what's in between).

> **Note:** AP values are subject to change as the game is balanced. Make sure
you don't hardcode them but rather use the values provided in this module.
"""
from botroyale.util.hexagon import Hexagon


MAX_AP: int = 100
"""Maximum amount of AP that a unit can accumulate."""
REGEN_AP: int = 50
"""Amount of AP that a unit will gain per round."""


class Action:
    """Base class for all Actions. Not to be used directly."""

    ap: int = 0
    """The AP cost of the action."""

    def __repr__(self):
        """Repr."""
        return f"<{self.__class__.__name__}>"


class Move(Action):
    """See module documenation for details."""

    ap = 20

    def __init__(self, target_tile: Hexagon):
        """Initialize the class.

        Args:
            target_tile: Target of the action.
        """
        assert isinstance(target_tile, Hexagon)
        self.target = target_tile

    def __repr__(self):
        """Repr."""
        return f"<{self.__class__.__name__}: {self.target.x}, {self.target.y}>"


class Push(Move):
    """See module documenation for details."""

    ap = 30


class Jump(Move):
    """See module documenation for details."""

    ap = 45


class Idle(Action):
    """See module documenation for details."""


ALL_ACTIONS: tuple[Action, ...] = (Idle, Move, Push, Jump)
"""A tuple of all the Actions."""
