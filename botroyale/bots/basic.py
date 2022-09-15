"""Basic bots."""
from itertools import chain
from botroyale.api.bots import BaseBot, center_distance
from botroyale.api.actions import Idle, Move, Jump, Push


class BasicBot(BaseBot):
    """A quick, simple bot."""

    NAME = "basic"
    COLOR_INDEX = 7
    state = None

    def poll_action(self, state):
        """Overrides `botroyale.api.bots.BaseBot.poll_action`."""
        self.logger("My options:")
        actions = list(self.get_actions(state))
        for a in actions:
            self.logger(f"{a=}")
        return actions[0]

    def get_actions(self, state, legal=True, sensible=True):
        """Generator of possible actions with filters.

        Args:
            state: State from which to act.
            legal: Filter illegal actions if True.
            sensible: Filter non-sensible actions if True.
        """
        pos = state.positions[self.id]
        possible_actions = chain(
            (Push(h) for h in pos.neighbors),
            (Move(h) for h in pos.neighbors),
            (Jump(h) for h in pos.ring(2)),
            [Idle()],
        )
        for a in possible_actions:
            new_state = state.apply_action_manual(a)
            if legal and not new_state.is_last_action_legal:
                continue
            if sensible and not new_state.alive_mask[self.id]:
                continue
            new_pos = new_state.positions[self.id]
            if center_distance(new_pos) >= new_state.death_radius - 1:
                continue
            yield a


BOT = BasicBot
