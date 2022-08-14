"""
The logging module is mostly used for the `api.logging.logger` function, as well as `Logger.set_logging_temp`.

Currently, logging is done by printing to console.
"""
from typing import Callable
import contextlib
from util.settings import Settings


# Permanently disables logging globally if False
GLOBAL_LOGGING = Settings.get('logging.global', True)


class Logger:
    """
    Handles logging globally.

    All of the following lines are equivalent:
    ```
    Logger.log('Print this to logs')
    Logger('Print this to logs')
    logger('Print this to logs')
    ```
    """
    enable_logging: bool = True
    """Disables logging globally if False."""

    @classmethod
    def log(cls, text: str):
        """
        Output text to console if logging is enabled globally."""
        if cls.enable_logging and GLOBAL_LOGGING:
            print(text)

    @classmethod
    def __call__(cls, text: str):
        cls.log(text)

    @classmethod
    @contextlib.contextmanager
    def set_logging_temp(cls, enabled: bool):
        """
        Context manager for temporarily enabling / disabling the logger globally.

        <u>__Example usage:__</u>
        ```
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
