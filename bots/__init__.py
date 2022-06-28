import random

from api.bot_api import BaseBot
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module

from util.settings import Settings


def bot_importer():
    """
    Imports all bots from modules in package
    """
    bots = {}
    package_dir = Path(__file__).resolve().parent
    for (_, module_name, _) in iter_modules([str(package_dir)]):
        module = import_module(f"{__name__}.{module_name}")
        print(f'module: {module}, module_name: {module_name}')
        if hasattr(module, "BOT"):
            bot = getattr(module, "BOT")
            if issubclass(bot, BaseBot):
                assert bot.NAME not in bots
                bots[bot.NAME] = bot
    return bots


BOT_REQ = Settings.get("bot_names", [])
BOTS = bot_importer()


def make_bots(num_of_bots: int) -> list[BaseBot]:
    """
    makes bots using bots from BOTS
    :param num_of_bots: number of bots to make
    :return: list of instances of bots
    """
    if len(BOTS) == 0:
        game_classes = [BaseBot] * num_of_bots
    else:
        game_classes = [BOTS[req] for req in BOT_REQ if req in BOTS]
        game_classes.extend(random.choices(list(BOTS.values()), k=num_of_bots - len(game_classes)))
    bots_instances = [game_classes[i](i) for i in range(num_of_bots)]
    return bots_instances
