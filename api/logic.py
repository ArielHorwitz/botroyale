from collections import deque, namedtuple
import numpy as np
from util import ping, pong
from util.settings import Settings
from util.hexagon import Hex, is_hex


TileGUI = namedtuple('TileGUI', ['bg_color', 'bg_text', 'fg_color', 'fg_text'])
VFX = namedtuple('VFX', ['name', 'hex', 'neighbor', 'time'])

STEP_RATE = Settings.get('logic._step_rate_cap', 20)
STEP_INTERVAL_MS = 1000 / STEP_RATE
LOGIC_DEBUG = Settings.get('logic.battle_debug', True)

RNG = np.random.default_rng()
MAX_STEPS = 1000
UNIT_COUNT = 20
AXIS_SIZE = 15



class BaseLogicAPI:
    debug_mode = False
    step_count = 0
    alive_mask = np.ones(UNIT_COUNT, dtype=bool)
    positions = [Hex(_, 0) for _ in range(UNIT_COUNT)]
    walls = {Hex(0, 1)}
    pits = {Hex(1, 1)}
    DEFAULT_CELL_BG = Settings.get('tilemap.|colors._default_tile', (0.25, 0.1, 0))
    WALL_COLOR = Settings.get('tilemap.|colors._walls', (1, 1, 1))
    PIT_COLOR = Settings.get('tilemap.|colors._pits', (0.05, 0.05, 0.05))
    UNIT_COLORS = Settings.get('tilemap.|colors.|units', [
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
    RAINBOW_COLORS = Settings.get('tilemap.|colors.||rainbow', [
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
        self.autoplay = False
        self.__last_step = ping()
        self.__vfx_queue = deque()
        self.unit_colors = [self.get_color(_) for _ in range(UNIT_COUNT)]

    def add_vfx(self, name, hex, neighbor=None, steps=2):
        """Add a single vfx to the queue."""
        assert isinstance(name, str)
        assert is_hex(hex)
        if neighbor is not None:
            assert is_hex(neighbor)
            assert neighbor in hex.neighbors
        time = steps * STEP_INTERVAL_MS / 1000
        self.__vfx_queue.append(VFX(name, hex, neighbor, time))

    def flush_vfx(self):
        """This method clears and returns the vfx from queue."""
        r = self.__vfx_queue
        self.__vfx_queue = deque()
        return r

    def update(self):
        if self.game_over:
            self.autoplay = False
        if not self.autoplay:
            return
        time_delta = pong(self.__last_step)
        if time_delta >= STEP_INTERVAL_MS:
            self.next_step()
            leftover = time_delta - STEP_INTERVAL_MS
            self.__last_step = ping() - leftover

    def next_step(self):
        """This method is called when a single step (smallest unit of time) is to be played."""
        self.step_count += 1

    @property
    def game_over(self):
        return self.step_count >= MAX_STEPS

    def get_match_state(self):
        """This method returns an arbritrary string to be displayed in the GUI."""
        turn = f'Step: {self.step_count} {self.autoplay}'
        game_over = 'GAME OVER' if self.game_over else ''
        return '\n'.join((turn, game_over))

    def debug(self):
        print(f'Toggling logic debug mode.')
        self.debug_mode = not self.debug_mode

    def get_gui_tile_info(self, hex):
        """This method is called for every hex currently visible on the map,
        and must return a TileGUI namedtuple."""
        # BG
        if hex in self.pits:
            bg_color = self.PIT_COLOR
        else:
            bg_color = self.DEFAULT_CELL_BG
        bg_text = ', '.join(str(_) for _ in hex.xy) if self.debug_mode else ''
        # FG
        if hex in self.walls:
            fg_text = ''
            fg_color = self.WALL_COLOR
        elif hex in self.positions:
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

    def get_control_buttons(self):
        return (
            ('Logic debug', self.debug),
            ('Play all', self.play_all),
            ('Next step ([i]n[/i])', self.next_step),
            ('Autoplay ([i]spacebar[/i])', self.toggle_autoplay),
        )

    def get_hotekys(self):
        return (
            ('autoplay', 'spacebar', self.toggle_autoplay),
            ('next_step', 'n', self.next_step),
        )

    def play_all(self, *args):
        print('Playing battle to completion...')
        count = 0
        while not self.game_over:
            count += 1
            self.next_step()
        # Clear the vfx else they will all be drawn at once at the end
        self.flush_vfx()

    def toggle_autoplay(self, set_to=None):
        if self.game_over:
            return
        if set_to is None:
            set_to = not self.autoplay
        self.autoplay = set_to
        self.__last_step = ping()
        self.logger(f'Auto playing...' if self.autoplay else f'Paused autoplay...')

    @staticmethod
    def logger(m):
        if LOGIC_DEBUG:
            print(m)
