# Maintainer: ninja
from bots import BaseBot
from api.actions import Idle


class IdleBot(BaseBot):
    NAME = 'idle'
    TESTING_ONLY = True
    COLOR_INDEX = 7
    SPRITE = 'ellipse'

    def poll_action(self, state):
        return Idle()


class DummyBot(IdleBot):
    NAME = 'dummy'


BOTS = [IdleBot, DummyBot]
