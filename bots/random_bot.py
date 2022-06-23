import random
from bots import BaseBot


class RandomBot(BaseBot):
    def __init__(self, id):
        super().__init__(id)

    def get_action(self, pos):
        return random.choice(pos.neighbors)


BOT = RandomBot
