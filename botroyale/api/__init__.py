"""Specifications and functions for interfacing different parts of the program."""

from botroyale.util.hexagon import ORIGIN, Hex as get_hex
from botroyale.api import actions
from botroyale.api.bots import BaseBot, register_bot
from botroyale.logic.state import State
from botroyale.logic.battle import Battle


def run_gui():
    """Run the GUI app."""
    # We import from inside the function as a hotfix until the gui can be
    # imported without opening a window.
    from botroyale.run.gui import run as _run_gui

    _run_gui()


__all__ = [
    "BaseBot",
    "register_bot",
    "run_gui",
    "actions",
    "State",
    "Battle",
    "get_hex",
    "ORIGIN",
]
NOT_DOCUMENTED = [
    "actions",
    "ORIGIN",
]
DOCUMENTED = [n for n in __all__ if n not in NOT_DOCUMENTED]
