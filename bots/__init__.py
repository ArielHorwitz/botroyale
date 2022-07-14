import random

from api.bots import BaseBot
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
    print('Available bots:')
    for (_, module_name, _) in iter_modules([str(package_dir)]):
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
            print(f'- {bot.NAME} (from module: {module_name})')
    return bots


BOT_REQ = Settings.get("bots.bot_names", ['basebot', 'basebot'])
BOTS_IGNORED = Settings.get("bots.bot_names_ignore", [])
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
        print('Requested bots:')
        print('\n'.join(f'#{i:<2} {r}' for i, r in enumerate(BOT_REQ[:num_of_bots])))
        print('Ignoring bots:')
        print('\n'.join(ibn for ibn in BOTS_IGNORED))
        game_classes = [BOTS[req] for req in BOT_REQ if req in BOTS]
        non_testing_bots = [bot for bot in BOTS.values() if not bot.TESTING_ONLY and bot.NAME not in BOTS_IGNORED]
        random.shuffle(non_testing_bots)
        while len(game_classes) < num_of_bots:
            idx = (num_of_bots - len(game_classes)) % len(non_testing_bots)
            game_classes.append(non_testing_bots[idx])
    print('Selected bots:')
    print('\n'.join(f'#{i:<2} {cls.NAME}' for i, cls in enumerate(game_classes[:num_of_bots])))
    bots_instances = [game_classes[i](i) for i in range(num_of_bots)]
    return bots_instances
