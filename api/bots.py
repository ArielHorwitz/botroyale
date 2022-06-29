from util.hexagon import Hex
from collections import namedtuple
from api.actions import Move, Push


world_info = namedtuple('WorldInfo', [
    'positions',
    'walls',
    'pits',
    'alive_mask',
    'turn_count',
    'round_count',
    'ap',
    # when round_priority is empty, round is over.
    'round_remaining_turns',
    ])


class BaseBot:
    NAME = "BaseBot"
    COLOR_INDEX = 0

    def __init__(self, id: int):
        self.id = id

    def get_action(self, world_state):
        return Move(Hex(0, 0))
