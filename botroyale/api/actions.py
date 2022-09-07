"""Actions used by bots and game mechanics.

See also: `botroyale.api.bots.BaseBot.poll_action`,
`botroyale.logic.state.State.apply_action`,
`botroyale.logic.state.State.check_legal_action`.

Currently available actions:

- Idle (*0 AP*): do nothing and end our turn.
- Move (*20 AP*): move to an adjascent tile.
- Push (*30 AP*): push a unit from an adjascent tile to the tile behind it.
- Jump (*45 AP*): move to a tile at a distance of 2.
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
    """*20 AP:* Move to an adjascent tile."""

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
    """*30 AP:* Push a unit from an adjascent tile to the tile behind it."""

    ap = 30


class Jump(Move):
    """*45 AP:* Move to a tile at a distance of 2."""

    ap = 45


class Idle(Action):
    """*0 AP:* Do nothing and end our turn."""


ALL_ACTIONS: tuple[Action, ...] = (Idle, Move, Push, Jump)
"""A tuple of all the Actions."""
