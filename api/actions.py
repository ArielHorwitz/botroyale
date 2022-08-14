"""
The Action classes used by bots (see `api.bots.BaseBot`) and game mechanics (see `logic.state.State`).
"""
from util.hexagon import Hexagon


class Action:
    """
    Base class for all Actions. Not to be used directly.

    Represents an action that a bot will take during their turn.
    """

    ap = 0
    """The AP cost of the action."""


class Move(Action):
    """Move to an adjascent tile (distance of 1)."""

    ap = 20
    """The AP cost of the action."""

    def __init__(self, target_tile: Hexagon):
        assert isinstance(target_tile, Hexagon)
        self.target = target_tile

    def __repr__(self):
        return f'<Move: {self.target.x}, {self.target.y}>'


class Push(Move):
    """Push a unit from an adjascent tile to the tile behind it."""

    ap = 30
    """The AP cost of the action."""

    def __repr__(self):
        return f'<Push: {self.target.x}, {self.target.y}>'


class Jump(Move):
    """Move to a tile at a distance of 2."""

    ap = 45
    """The AP cost of the action."""

    def __repr__(self):
        return f'<Jump: {self.target.x}, {self.target.y}>'


class Idle(Action):
    """Do nothing and end our turn."""

    def __repr__(self):
        return f'<Idle>'


ALL_ACTIONS = (Idle, Move, Push, Jump)
