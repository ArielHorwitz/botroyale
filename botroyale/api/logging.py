"""Logging tools.

The logging module is mostly used for the `Logger.log` function, as
well as `Logger.set_logging_temp`.

Currently, logging is done by printing to console.
"""
import contextlib
from botroyale.util import settings


# Permanently disables logging globally if False
GLOBAL_LOGGING = settings.get("logging.global")


class Logger:
    """Handles logging globally. Use `Logger.log` for logging."""

    enable_logging: bool = True
    """Disables logging globally if False."""

    @classmethod
    def log(cls, text: str):
        """Output text to console if logging is enabled globally."""
        if cls.enable_logging and GLOBAL_LOGGING:
            print(text)

    @classmethod
    @contextlib.contextmanager
    def set_logging_temp(cls, enabled: bool):
        """Context manager for temporarily enabling / disabling the logger globally.

        <u>__Example usage:__</u>
        ```python
        Logger.enable_logging = True
        logger('This will be logged')
        with Logger.set_logging_temp(False):
            logger('This will not be logged')
            with Logger.set_logging_temp(True):
                logger('This will be logged')
            logger('This will not be logged')
        logger('This will be logged')
        ```
        """
        last_state = cls.enable_logging
        cls.enable_logging = enabled
        yield last_state
        cls.enable_logging = last_state


logger = Logger.log
"""Alias for `Logger.log`."""
