import time
from bots import BaseBot
from api.actions import Move


class SleeperBot(BaseBot):
    NAME = "SleeperBot"
    TESTING_ONLY = True
    sleep_time = 3

    def __init__(self, id):
        super().__init__(id)

    def get_action(self, world_state):
        time.sleep(self.sleep_time)
        pos = world_state.positions[self.id]
        return Move(pos)


class SnoozerBot(SleeperBot):
    NAME = 'SnoozerBot'
    sleep_time = 1


BOTS = [SleeperBot, SnoozerBot]
