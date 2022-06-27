import random
from bots import BaseBot
from util.hexagon import Hex
from api.actions import Move, Push


class RandomBot(BaseBot):
    NAME = "Random1"

    def __init__(self, id):
        super().__init__(id)

    def get_action(self, world_state):
        pos = world_state.positions[self.id]
        return Move(random.choice(Hex(*pos).neighbors))


BOT = RandomBot
