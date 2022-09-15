"""Random bots."""
import random
import time
from botroyale.api.bots import BaseBot, center_distance
from botroyale.api.actions import Move, Jump


class RandomBot(BaseBot):
    """A bot that randomly chooses their next action."""

    NAME = "random"
    TESTING_ONLY = True
    COLOR_INDEX = 5
    SPRITE = "ellipse"

    def poll_action(self, state):
        """Overrides `botroyale.api.bots.BaseBot.poll_action`."""
        pos = state.positions[self.id]
        action = self.get_target(pos)
        attempts = 5
        while not self.safe_target(action.target, state) and attempts:
            action = self.get_target(pos)
            attempts -= 1
        return action

    def safe_target(self, target, state):
        """Checks if the target is "safe" to move to."""
        return all(
            [
                target not in state.pits,
                center_distance(target) < state.death_radius,
            ]
        )

    def get_target(self, pos):
        """Return a random target to move to."""
        return random.choice(
            [
                Move(random.choice(pos.neighbors)),
                Jump(random.choice(pos.ring(radius=2))),
            ]
        )


class SleeperBot(RandomBot):
    """A bot that takes several seconds to poll for action."""

    NAME = "sleeper"
    TESTING_ONLY = True
    sleep_time = 3

    def poll_action(self, state):
        """Overrides `botroyale.api.bots.BaseBot.poll_action`."""
        time.sleep(self.sleep_time)
        return super().poll_action(state)


class SnoozerBot(SleeperBot):
    """A bot that takes a significant fraction of a seconds to poll for action."""

    NAME = "snoozer"
    sleep_time = 0.2


BOTS = [RandomBot, SleeperBot, SnoozerBot]
