""".. include:: ../docs/homepage.md"""


from botroyale.util import VERSION
from botroyale.api.bots import BaseBot
from botroyale.bots import register_bot
from botroyale.run.gui import run as run_gui
from botroyale.logic.state import State
from botroyale.util.hexagon import ORIGIN, Hex as get_hex
from botroyale.api import actions


__all__ = [
    'BaseBot',
    'register_bot',
    'run_gui',
    'actions',
    'ORIGIN',
    'get_hex',
    'State',
]

__version__ = VERSION
__pdoc__ = {
    "gui": False,
    **{a: False for a in __all__}
}
