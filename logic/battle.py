from collections import deque, namedtuple
import numpy as np
from api.logging import logger as glogger
from api.gui import TileGUI, VFX, GuiControlMenu, GuiControl
from api.bots import state_to_world_info
from bots import make_bots
from logic.maps import get_map
from logic.state import State
from util.time import ping, pong, pingpong
from util.settings import Settings
from util.hexagon import Hex, is_hex


STEP_RATE = Settings.get('logic._step_rate_cap', 2)
STEP_RATES = Settings.get('logic.|step_rates', [1, 2, 3, 5, 60])
LOGIC_DEBUG = Settings.get('logging.battle', True)
LINEBR = '='*75
MAP_CENTER = Hex(0, 0)


class Battle:
    step_interval_ms = 1000 / STEP_RATE
    debug_mode = False
    DEFAULT_CELL_BG = Settings.get('tilemap.|colors._default_tile', (0.25, 0.1, 0))
    OUT_OF_BOUNDS_CELL_BG = Settings.get('tilemap.|colors._out_of_bounds', (0.05, 0, 0.075))
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

    def __init__(self):
        self.autoplay = False
        self.__last_step = ping()
        self.__vfx_queue = deque()
        map = get_map()
        # Map radius represents the radius in which tiles are part of the map
        self.map_size_hint = map.radius
        # Game state
        # Since we start at the end of round 0, we need to take into account
        # that the initial state should be one round before the first real round.
        # Death radius should be a single tile further out than map radius at
        # the first round, so we start it two tiles out at the 0th round.
        death_radius = map.radius + 2
        # We can add the pits for round 1 otherwise the initial state will
        # be confusing.
        pits = map.pits | set(MAP_CENTER.ring(radius=death_radius-1))
        # State
        initial_state = State(
            death_radius=death_radius,
            positions=map.spawns,
            pits=pits,
            walls=map.walls,
        )
        self.__state = initial_state
        self.__state_history = [initial_state]
        self.state_index = 0
        # Bots
        self.bot_count = len(map.spawns)
        self.bots = make_bots(self.bot_count)
        self.unit_colors = [self.get_color(bot.COLOR_INDEX) for bot in self.bots]
        self.unit_sprites = [bot.SPRITE for bot in self.bots]
        # Bot timers
        self.bot_block_totals = [0 for _ in range(self.bot_count)]
        self.bot_block_rounds = [0 for _ in range(self.bot_count)]
        # Once everything is ready, allow bots to prepare
        for bot in self.bots:
            bot.setup(initial_state)

    # History
    def increment_state_index(self, delta=1):
        if delta > 0:
            self.set_state_index(self.state_index + delta)
        else:
            # Iterate the index several steps in advance to draw relevant vfx
            target = self.state_index + delta
            self.set_state_index(target - 2)
            self.set_state_index(target - 1)
            self.set_state_index(target)
            self.autoplay = False

    def set_state_index(self, index, apply_vfx=True):
        index = max(0, index)
        if len(self.__state_history) <= index:
            self._extend_history(index)
            index = min(index, self.history_size-1)
        self.__state = self.__state_history[index]
        self.state_index = index
        if apply_vfx:
            for effect in self.__state.effects:
                self.add_vfx(effect.name, effect.origin, effect.target)

    @property
    def history_size(self):
        return len(self.__state_history)

    @property
    def state(self):
        return self.__state

    @property
    def last_state(self):
        return self.__state_history[max(0, self.state_index-1)]

    def _extend_history(self, index):
        state = self.__state_history[-1]
        while not state.game_over and self.history_size < index + 1:
            state = self._do_next_state(state)
            self.__state_history.append(state)

    def _do_next_state(self, state):
        if state.end_of_round:
            new_state = state.increment_round()
        else:
            bot_id = state.round_remaining_turns[0]
            self.log_step(bot_id, state)
            action = self._get_bot_action(bot_id, state)
            self.logger(f'Applying: {action}')
            new_state = state.apply_action_no_round_increment(action)
            if not new_state.is_last_action_legal:
                self.logger(f'ILLEGAL: {action}')
        new_state.step_count += 1
        return new_state

    def _get_bot_action(self, bot_id, state):
        state = state.copy()
        bot = self.bots[bot_id]
        pingpong_desc = f'{bot} get_action (step {state.step_count})'
        self.bot_block_rounds[bot_id] = state.round_count
        def add_bot_time(elapsed):
            self.bot_block_totals[bot_id] += elapsed
        with pingpong(pingpong_desc, logger=self.logger, return_elapsed=add_bot_time):
            action = self.bots[bot_id].poll_action(state)
            self.logger(LINEBR)
        self.logger(f'Received action: {action}')
        return action

    # GUI API
    def update(self):
        if self.state.game_over:
            self.autoplay = False
        if not self.autoplay:
            return
        time_delta = pong(self.__last_step)
        if time_delta >= self.step_interval_ms:
            self.increment_state_index()
            leftover = time_delta - self.step_interval_ms
            self.__last_step = ping() - leftover

    def next_step(self):
        """Called when a single step (smallest unit of time) is to be played."""
        self.increment_state_index()

    def flush_vfx(self):
        """Clears and returns the vfx from queue."""
        r = self.__vfx_queue
        self.__vfx_queue = deque()
        return r

    def get_summary_str(self):
        return ''.join([
            f'{self.get_status_str()}',
            f'\n',
            f'{self.get_units_str()}',
            ])

    def get_gui_tile_info(self, hex):
        """This method is called for every hex currently visible on the map,
        and must return a TileGUI namedtuple."""
        # BG
        if hex in self.highlighted_tiles:
            bg_color = 1, 1, 1
        elif hex.get_distance(MAP_CENTER) >= self.state.death_radius:
            bg_color = self.OUT_OF_BOUNDS_CELL_BG
        elif hex in self.state.pits:
            bg_color = self.PIT_COLOR
        else:
            bg_color = self.DEFAULT_CELL_BG
        bg_text = ', '.join(str(_) for _ in hex.xy) if self.debug_mode else ''
        # FG
        if hex in self.state.walls:
            fg_text = ''
            fg_color = self.WALL_COLOR
            fg_sprite = 'hex'
        elif hex in self.state.positions:
            unit_id = self.state.positions.index(hex)
            if not self.state.alive_mask[unit_id]:
                fg_color = 0.5, 0.5, 0.5
            else:
                fg_color = self.unit_colors[unit_id]
            fg_text = f'{unit_id}'
            fg_sprite = self.unit_sprites[unit_id]
        else:
            fg_color = None
            fg_text = ''
            fg_sprite = None
        return TileGUI(
            bg_color=bg_color,
            bg_text=bg_text,
            fg_color=fg_color,
            fg_text=fg_text,
            fg_sprite=fg_sprite,
            )

    def handle_hex_click(self, hex, button):
        self.logger(f'Clicked {button} on: {hex}')
        if hex in self.state.positions:
            bot_id = self.state.positions.index(hex)
            vfx_seq = self.bots[bot_id].gui_click(hex, button)
            if vfx_seq is not None:
                for vfx_kwargs in vfx_seq:
                    vfx_kwargs['steps'] = 1
                    self.add_vfx(**vfx_kwargs)
        else:
            if button == 'left':
                vfx = 'mark-green'
            elif button == 'right':
                vfx = 'mark-red'
            else:
                vfx = 'mark-blue'
            self.add_vfx(vfx, hex, steps=1)

    @property
    def highlighted_tiles(self):
        """A set of hexes to be highlighted."""
        if self.state.round_remaining_turns:
            return {self.state.positions[self.state.round_remaining_turns[0]]}
        return set()

    def get_time(self):
        return self.state.step_count

    def get_controls(self):
        """Return a list of GuiControlMenus of GuiControl objects for buttons/hotkeys in GUI."""
        return [
            GuiControlMenu('Battle', [
                GuiControl('Next step', lambda: self.increment_state_index(1), 'right'),
                GuiControl('Prev step', lambda: self.increment_state_index(-1), 'left'),
                GuiControl('+10 steps', lambda: self.increment_state_index(10), '+ right'),
                GuiControl('-10 steps', lambda: self.increment_state_index(-10), '+ left'),
                GuiControl('+1M steps <!!!>', lambda: self.increment_state_index(1_000_000), '^+ right'),
                GuiControl('-1M steps', lambda: self.increment_state_index(-1_000_000), '^+ left'),
                GuiControl('Preplay <!!!>', self.play_all, '^+ p'),
                GuiControl('Autoplay', self.toggle_autoplay, 'spacebar'),
                *[GuiControl(f'Set step rate {r}', lambda r=r: self.set_step_rate(r), f'{i+1}') for i, r in enumerate(STEP_RATES[:5])]
            ]),
            GuiControlMenu('Debug', [
                GuiControl('Logic debug', self.debug, '^+ d'),
            ]),
        ]

    def play_all(self):
        self.logger('Playing battle to completion...')
        self._extend_history(1_000_000)
        self.flush_vfx()
        self.set_state_index(0)
        self.autoplay = False
        self.logger('Battle played to completion.')

    # GUI formatting
    def get_units_str(self):
        include_timer = self.state.step_count == self.history_size - 1
        unit_strs = [self.get_bot_string(bot_id, include_timer) for bot_id in self.state.round_remaining_turns]
        unit_strs.append('-'*10)
        unit_strs.extend(self.get_bot_string(bot_id, include_timer) for bot_id in self.state.round_done_turns)
        unit_strs.append('='*10)
        unit_strs.extend(self.get_bot_string(bot_id, include_timer) for bot_id in self.state.casualties)
        return '\n'.join(unit_strs)

    def get_status_str(self):
        # Playing/game over
        if self.state.game_over:
            winner_str = 'Draw!'
            if self.state.alive_mask.sum() == 1:
                winner_id = np.arange(self.bot_count)[self.state.alive_mask][0]
                winner = self.bots[winner_id]
                winner_str = f'Winner: {winner.gui_label}'
            win_str = f'GAME OVER\n{winner_str}'
        else:
            autoplay = 'Playing' if self.autoplay else 'Paused'
            win_str = f'{autoplay} <= {1000 / self.step_interval_ms:.2f} steps/second'

        # Current turn
        if self.state.round_remaining_turns:
            bot_id = self.state.round_remaining_turns[0]
            bot = self.bots[bot_id]
            turn_str = f'{bot.gui_label} ({round(self.state.ap[bot_id])} AP)'
        else:
            turn_str = f'starting new round'

        # Last action
        if self.state.step_count == 0:
            last_turn_str = '[i]new game[/i]'
            last_action_str = f'[i]started new game[/i]'
        elif self.last_state.end_of_round:
            last_turn_str = '[i]end of round[/i]'
            last_action_str = f'[i]started new round[/i]'
        else:
            last_bot = self.bots[self.last_state.round_remaining_turns[0]]
            last_turn_str = last_bot.gui_label
            last_action_str = f'{self.state.last_action}'
            if not self.state.is_last_action_legal:
                last_action_str = f'{last_action_str}\n[i]ILLEGAL[/i]'

        return '\n'.join([
            win_str,
            '',
            f'Step:  {self.state.step_count:<5}',
            f'Turn:  {self.state.turn_count:<4}',
            f'Round: {self.state.round_count:<3}',
            f'Ring of death radius:  {self.state.death_radius}',
            f'Currently: {turn_str}',
            '',
            f'Last turn: {last_turn_str}',
            f'Last action: {last_action_str}',
            '\n',
        ])

    def get_bot_string(self, bot_id, include_timer=False):
        bot = self.bots[bot_id]
        ap = round(self.state.ap[bot_id])
        pos = self.state.positions[bot_id]
        name_label = f'{bot.gui_label[:20]:<20}'
        bot_str = f'{name_label} {ap:>3} AP <{pos.x:>3},{pos.y:>3}>'
        if bot_id in self.state.casualties:
            bot_str = f'[s]{bot_str}[/s]'
        if not include_timer:
            return bot_str
        time_str = '  no time spent yet'
        if self.bot_block_rounds[bot_id]:
            time_per_round = round(self.bot_block_totals[bot_id] / self.bot_block_rounds[bot_id], 1)
            time_str = f'{time_per_round:>6} ms/t ({self.bot_block_rounds[bot_id]} turns)'
        bot_str = f'{bot_str} {time_str}'
        return bot_str

    # Autoplay
    def toggle_autoplay(self, set_to=None):
        if self.state.game_over:
            self.autoplay = False
            return
        if set_to is None:
            set_to = not self.autoplay
        self.autoplay = set_to
        self.__last_step = ping()
        self.logger(f'Auto playing...' if self.autoplay else f'Paused autoplay...')

    def set_step_rate(self, step_rate):
        assert 0 <= step_rate
        self.step_interval_ms = 1000 / step_rate
        self.__last_step = ping()

    # Other
    def add_vfx(self, name, hex, neighbor=None, steps=2, expire_seconds=None):
        """Add a single vfx to the queue."""
        assert isinstance(name, str)
        assert is_hex(hex)
        if neighbor is not None:
            assert is_hex(neighbor)
            assert neighbor in hex.neighbors
        start_step = self.state.step_count
        expire_step = start_step + steps
        self.__vfx_queue.append(VFX(
            name, hex, neighbor,
            start_step, expire_step, expire_seconds,
            ))

    def get_color(self, index):
        return self.UNIT_COLORS[index % len(self.UNIT_COLORS)]

    def debug(self):
        self.debug_mode = not self.debug_mode
        self.logger(f'Toggled logic debug mode: {self.debug_mode}')

    # Logging
    def logger(self, text):
        if LOGIC_DEBUG:
            glogger(text)

    def log_step(self, bot_id, state):
        self.logger('\n'.join([
            LINEBR,
            ' '.join([
                f'Step {str(state.step_count):^4}',
                f'Turn: {str(state.turn_count):^4}',
                f'Round: {str(state.round_count):^3}',
                '|',
                f'{self.bots[bot_id]}',
                ]),
            LINEBR,
        ]))
