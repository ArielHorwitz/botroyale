"""Idle bots."""
# Maintainer: ninja
from botroyale.api.bots import BaseBot
from botroyale.api.actions import Idle


class IdleBot(BaseBot):
    """A bot that does nothing."""

    NAME = "idle"
    TESTING_ONLY = True
    COLOR_INDEX = 7
    SPRITE = "ellipse"

    def poll_action(self, state):
        """Overrides `botroyale.api.bots.BaseBot.poll_action`."""
        return Idle()


class DummyBot(IdleBot):
    """A bot that does nothing."""

    NAME = "dummy"


BOTS = [IdleBot, DummyBot]
