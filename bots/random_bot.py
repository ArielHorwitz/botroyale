import random

from api.bot_api import WorldInfo
from bots import BaseBot


class RandomBot(BaseBot):
    def __init__(self, id):
        super().__init__(id)

    def get_move(self, world: WorldInfo = None):
        return random.choice(self.DIRECTIONS)


BOT = RandomBot
