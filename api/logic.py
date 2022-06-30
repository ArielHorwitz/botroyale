from collections import deque, namedtuple
import numpy as np
from util.hexagon import Hex

RNG = np.random.default_rng()
MAX_STEPS = 1000
UNIT_COUNT = 10
AXIS_SIZE = 15


EventDeath = namedtuple('EventDeath', ['unit'])
EVENT_TYPES = (EventDeath, )


class BaseLogicAPI:
    # map_size is a 2-tuple of integers (width, height)
    map_size = AXIS_SIZE, AXIS_SIZE
    turn_count = 0

    alive_mask = np.ones(UNIT_COUNT, dtype=bool)
    positions = [Hex(0, 0), Hex(0, 1)]
    walls = {Hex(1, 0)}
    pits = {Hex(1, 1)}

    def __init__(self):
        self.__event_queue = deque()

    def add_event(self, event):
        """Add an event to the queue."""
        assert type(event) in EVENT_TYPES
        self.__event_queue.append(event)

    def flush_events(self):
        """This method clears and returns the events from queue."""
        r = self.__event_queue
        self.__event_queue = deque()
        return r

    def next_step(self):
        """This method is called when a single turn is to be played."""
        self.turn_count += 1

    @property
    def game_over(self):
        """This property returns a boolean if there are any more turns to play."""
        return self.turn_count >= MAX_STEPS

    def get_match_state(self):
        """This method returns an arbritrary string to be displayed in the GUI."""
        game_over = 'GAME OVER' if self.game_over else ''
        return f'Turn: {self.turn_count}\n{game_over}'

    def debug(self):
        print(f'Override the method BaseLogicAPI.debug() to use this feature.')

    @property
    def unit_colors(self):
        return [b.COLOR_INDEX for b in self.bots]
