import random

from api.logging import logger
from api.bots import BaseBot
from pkgutil import iter_modules
from importlib import import_module

from util import PROJ_DIR
from util.settings import Settings


BOTS_DIR = PROJ_DIR / 'bots'


def bot_importer():
    """
    Imports all bots from modules in package
    """
    bots = {}
    logger('Available bots:\n(Legend: » competitive - test)')
    for (_, module_name, _) in iter_modules([str(BOTS_DIR)]):
        module = import_module(f"{__name__}.{module_name}")
        if hasattr(module, "BOT"):
            module_bots = [getattr(module, "BOT")]
        elif hasattr(module, "BOTS"):
            module_bots = getattr(module, "BOTS")
        else:
            continue
        for bot in module_bots:
            assert issubclass(bot, BaseBot)
            if bot.NAME in bots:
                raise KeyError(f'Bot name: "{bot.NAME}" (from module: {module_name}) already in use.')
            bots[bot.NAME] = bot
            prefix = '-' if bot.TESTING_ONLY else '»'
            logger(f'{prefix} {bot.NAME:<20} | from module: {module_name:<20}')
    return bots


BOT_REQ = Settings.get("bots.bot_names", [])
BOTS_IGNORED = Settings.get("bots.bot_names_ignore", [])
BOTS = bot_importer()


def get_bot_classes(num_of_bots: int) -> list[type]:
    """
    Returns a list of bot classes from BOTS as configured in settings.

    :param num_of_bots:     number of bots classes to collect
    :return:                list of bot classes
    """
    if len(BOTS) == 0:
        game_classes = [BaseBot] * num_of_bots
    else:
        game_classes = [BOTS[req] for req in BOT_REQ if req in BOTS]
        non_testing_bots = [bot for bot in BOTS.values() if not bot.TESTING_ONLY and bot.NAME not in BOTS_IGNORED]
        random.shuffle(non_testing_bots)
        while len(game_classes) < num_of_bots:
            idx = (num_of_bots - len(game_classes)) % len(non_testing_bots)
            game_classes.append(non_testing_bots[idx])
    game_classes = game_classes[:num_of_bots]
    logger('Selected bots:')
    logger('\n'.join(f'#{i:<2} {cls.NAME}' for i, cls in enumerate(game_classes)))
    return game_classes
