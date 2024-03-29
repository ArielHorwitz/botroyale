""".. include:: ../docs/homepage.md"""  # noqa: D415

# For the sake of a convenient API, we star import the api subpackage, which
# defines __all__ to contain all the names to be available directly.
from botroyale import api
from botroyale.api import *  # noqa: F401,F403


__all__ = api.__all__
__pdoc__ = {
    # The bots subpackage contains the built-in bots
    "bots": False,
    # The run subpackage has arg parsing for help
    "run": False,
    # Filter out attributes that would be documented because of the start import
    **{n: False for n in api.DOCUMENTED_API},
}
