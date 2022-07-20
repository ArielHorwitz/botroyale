import random
from bots import BaseBot
from util.hexagon import Hex
from api.actions import Move, Push, Jump


class RandomBot(BaseBot):
    NAME = 'RandomBot'
    SPRITE = 'ellipse'
    TESTING_ONLY = True

    def __init__(self, id):
        super().__init__(id)

    def poll_action(self, state):
        pos = state.positions[self.id]
        action = self.get_target(pos)
        attempts = 5
        while not self.safe_target(action.target, state) and attempts:
            self.logger(f'Unsafe target {action}, finding new target (remaining attemps: {attempts})')
            action = self.get_target(pos)
            attempts -= 1
        self.logger(f'Found safe target: {action}')
        return action

    def safe_target(self, target, state):
        return all([
            target not in state.pits,
            target.get_distance(Hex(0, 0)) < state.death_radius,
            ])

    def get_target(self, pos):
        return random.choice([
            Move(random.choice(pos.neighbors)),
            Jump(random.choice(pos.ring(radius=2))),
        ])


BOT = RandomBot
