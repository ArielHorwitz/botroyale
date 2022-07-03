from collections import deque, namedtuple
import numpy as np
from util.settings import Settings
from util.hexagon import Hex


TileGUI = namedtuple('TileGUI', ['bg_color', 'bg_text', 'fg_color', 'fg_text'])

RNG = np.random.default_rng()
MAX_STEPS = 1000
UNIT_COUNT = 20
AXIS_SIZE = 15

EventDeath = namedtuple('EventDeath', ['unit'])
EVENT_TYPES = (EventDeath, )


class BaseLogicAPI:
    debug_mode = False
    turn_count = 0
    alive_mask = np.ones(UNIT_COUNT, dtype=bool)
    positions = [Hex(_, 0) for _ in range(UNIT_COUNT)]
    walls = {Hex(0, 1)}
    pits = {Hex(1, 1)}
    DEFAULT_CELL_BG = Settings.get('default_tile_color', (0.25, 0.1, 0))
    WALL_COLOR = Settings.get('wall_color', (1, 1, 1))
    PIT_COLOR = Settings.get('pit_color', (0.05, 0.05, 0.05))
    UNIT_COLORS = Settings.get('unit_colors', [
        (0.6, 0, 0.1),  # Red
        (0.9, 0.3, 0.4),  # Pink
        (0.8, 0.7, 0.1),  # Yellow
        (0.7, 0.4, 0),  # Orange
        (0.1, 0.4, 0),  # Green
        (0.4, 0.7, 0.1),  # Lime
        (0.1, 0.7, 0.7),  # Teal
        (0.1, 0.4, 0.9),  # Blue
        (0, 0.1, 0.5),  # Navy
        (0.7, 0.1, 0.9),  # Purple
        (0.4, 0, 0.7),  # Violet
        (0.7, 0, 0.5),  # Magenta
    ])
    RAINBOW_COLORS = Settings.get('rainbow_colors', [
        (0, 0, 0),
        (1, 0, 0),
        (1, 0.5, 0),
        (0.5, 0.5, 0),
        (0.25, 0.75, 0),
        (0, 0.5, 0.5),
        (0, 0.5, 1),
        (0, 0, 1),
        (1, 0, 1),
        (1, 0, 0.5),
    ])

    def __init__(self):
        self.__event_queue = deque()
        self.unit_colors = [self.get_color(_) for _ in range(UNIT_COUNT)]

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
        """This method is called when a single step (smallest unit of time) is to be played."""
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
        print(f'Toggling logic debug mode.')
        self.debug_mode = not self.debug_mode

    def get_gui_tile_info(self, hex):
        """This method is called for every hex currently visible on the map,
        and must return a TileGUI namedtuple."""
        has_unit = hex in self.positions
        # BG color
        if hex in self.pits:
            bg_color = self.PIT_COLOR
        elif hex in self.walls:
            bg_color = self.WALL_COLOR
        else:
            bg_color = self.DEFAULT_CELL_BG
        # BG text
        bg_text = ''
        if self.debug_mode:
            bg_text = ', '.join(str(_) for _ in hex.xy)
        # FG color
        if has_unit:
            unit_id = self.positions.index(hex)
            fg_color = self.unit_colors[unit_id]
            fg_text = f'{unit_id}'
        else:
            fg_color = None
            fg_text = ''
        return TileGUI(
            bg_color=bg_color,
            bg_text=bg_text,
            fg_color=fg_color,
            fg_text=fg_text,
            )

    def get_color(self, index):
        return self.UNIT_COLORS[index % len(self.UNIT_COLORS)]
