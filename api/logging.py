from util.settings import Settings


GLOBAL_LOGGING = Settings.get('logging.global', True)


class Logger:
    enable_logging = GLOBAL_LOGGING

    def __call__(self, text):
        if self.enable_logging:
            print(text)


logger = Logger()
