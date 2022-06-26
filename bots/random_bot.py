import random
from bots import BaseBot
from util.hexagon import Hex


class RandomBot(BaseBot):
    def __init__(self, id):
        super().__init__(id)

    def get_action(self, world_state):
        pos = world_state.positions[self.id]
        return random.choice(Hex(*pos).neighbors)


BOT = RandomBot
