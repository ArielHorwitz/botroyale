import random

import numpy as np
from api.bot_api import WorldInfo
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module


class Direction:
    N = np.asarray([1, 0])
    S = np.asarray([-1, 0])
    E = np.asarray([0, 1])
    W = np.asarray([0, -1])
    NW = np.asarray([1, -1])
    NE = np.asarray([1, 1])
    SW = np.asarray([-1, -1])
    SE = np.asarray([-1, 1])
    HOLD = np.asarray([0, 0])


class BaseBot:
    DIRECTIONS = [
        Direction.N,
        Direction.S,
        Direction.E,
        Direction.W,
        Direction.NW,
        Direction.NE,
        Direction.SW,
        Direction.SE,
        Direction.HOLD]

    def __init__(self, id: int):
        self.id = id

    def get_move(self, world: WorldInfo = None):
        """
        Called by the Game Logic
        :param world: state of world
        :return: action to take
        """
        return Direction.HOLD


def bot_importer():
    """
    Imports all bots from modules in package
    """
    bots = []
    package_dir = Path(__file__).resolve().parent
    for (_, module_name, _) in iter_modules([package_dir]):
        module = import_module(f"{__name__}.{module_name}")
        print(f'module: {module}, module_name: {module_name}')
        if hasattr(module, "BOT"):
            bot = getattr(module, "BOT")
            if issubclass(bot, BaseBot):
                bots.append(bot)
    return bots


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
        game_classes = random.choices(BOTS, k=num_of_bots)
    bots_instances = [game_classes[i](i) for i in range(num_of_bots)]
    return bots_instances
