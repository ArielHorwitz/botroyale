from util.hexagon import Hex
from collections import namedtuple
from api.actions import Move, Push


world_info = namedtuple('WorldInfo', [
    'positions',  # list of tiles
    'walls',  # set of tiles
    'pits',  # set of tiles
    'ring_radius',  # int
    'alive_mask',  # ndarray mask
    'turn_count',  # int
    'round_count',  # int
    'ap',  # ndarray
    'round_ap_spent',  # ndarray
    # when round_priority is empty, round is over.
    'round_remaining_turns',  # list
    ])


class BaseBot:
    NAME = "BaseBot"
    COLOR_INDEX = 0

    def __init__(self, id: int):
        self.id = id

    def get_action(self, world_state):
        return Move(Hex(0, 0))
