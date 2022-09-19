"""The Kex library.

An interface to the [Kivy](https://kivy.org/) library with extended widgets for
convenience. It focuses on making it easier (and maybe a little more intuitive)
to write kivy apps programmatically.

## KexMixin
The `KexMixin` class is a mixin class for kivy widgets with convenience methods.
"""

import os

# Kivy configuration must be done before importing kivy
os.environ["KIVY_NO_ARGS"] = "1"  # no consuming script arguments
os.environ["KCFG_KIVY_LOG_LEVEL"] = "warning"  # no spamming console on startup


from .util import *  # noqa: E402,F401,F403
from .widgets import *  # noqa: E402,F401,F403
