""".. include:: ../docs/homepage.md"""  # noqa: D415


from botroyale.api.bots import BaseBot, register_bot
from botroyale.run.gui import run as run_gui
from botroyale.logic.state import State
from botroyale.util.hexagon import ORIGIN, Hex as get_hex
from botroyale.api import actions


__all__ = [
    "BaseBot",
    "register_bot",
    "run_gui",
    "actions",
    "ORIGIN",
    "get_hex",
    "State",
]
__pdoc__ = {
    "gui": False,
    "bots": False,
    "BaseBot": False,
    "register_bot": False,
    "run_gui": False,
    "get_hex": False,
    "State": False,
}
