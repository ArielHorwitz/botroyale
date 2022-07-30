import contextlib
from util.settings import Settings


GLOBAL_LOGGING = Settings.get('logging.global', True)


class Logger:
    enable_logging = True

    @classmethod
    def log(cls, text):
        """Output text to console. Considers if logging is enabled."""
        if cls.enable_logging and GLOBAL_LOGGING:
            print(text)

    @classmethod
    def __call__(cls, text):
        cls.log(text)

    @classmethod
    @contextlib.contextmanager
    def set_logging_temp(cls, enabled: bool):
        """Context manager for temporarily setting the logger enabled/disabled."""
        last_state = cls.enable_logging
        cls.enable_logging = enabled
        yield last_state
        cls.enable_logging = last_state


logger = Logger.log
