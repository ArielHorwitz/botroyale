# Maintainer: ninja
import random
import time
from api.bots import BaseBot, center_distance
from api.actions import Move, Push, Jump


class RandomBot(BaseBot):
    NAME = 'random'
    SPRITE = 'ellipse'
    TESTING_ONLY = True

    def poll_action(self, state):
        pos = state.positions[self.id]
        action = self.get_target(pos)
        attempts = 5
        while not self.safe_target(action.target, state) and attempts:
            action = self.get_target(pos)
            attempts -= 1
        return action

    def safe_target(self, target, state):
        return all([
            target not in state.pits,
            center_distance(target) < state.death_radius,
            ])

    def get_target(self, pos):
        return random.choice([
            Move(random.choice(pos.neighbors)),
            Jump(random.choice(pos.ring(radius=2))),
        ])


class SleeperBot(RandomBot):
    NAME = "sleeper"
    TESTING_ONLY = True
    sleep_time = 3

    def poll_action(self, state):
        time.sleep(self.sleep_time)
        return super().poll_action(state)


class SnoozerBot(SleeperBot):
    NAME = 'snoozer'
    sleep_time = 0.2


BOTS = [RandomBot, SleeperBot, SnoozerBot]
