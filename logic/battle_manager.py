"""
Home of `logic.battle_manager.BattleManager`.
"""
from typing import Optional, Union, Sequence, Set
from logic.battle import Battle

from collections import deque
from api.gui import BattleAPI, Tile, VFX, Control, ControlMenu
from util.time import ping, pong
from util.settings import Settings
from util.hexagon import Hex, Hexagon
from logic.state import State


STEP_RATE = Settings.get('logic._step_rate_cap', 2)
STEP_RATES = Settings.get('logic.|step_rates', [1, 2, 3, 5, 60])
LOGIC_DEBUG = Settings.get('logging.battle', True)
MAP_CENTER = Hex(0, 0)


class BattleManager(Battle, BattleAPI):
    """An interface between `logic.battle.Battle` and `api.gui.BattleAPI`.

    Provides methods for parsing, formatting, and displaying information about the battle, as well as GUI-related controls and display getters.

    While it can be used as an extension of `logic.battle.Battle`, this class can behave surprisingly different than the base class. This is because it keeps track of a replay index, allowing to "look at" past states. Therefore it is recommended to be familiar with `BattleManager.set_replay_index`.
    """
    show_coords = False
    """Whether to show coordinates on the tilemap."""
    step_interval_ms = 1000 / STEP_RATE
    """Time between steps for `BattleManager.autoplay` in ms."""
    DEFAULT_CELL_BG = Settings.get('tilemap.|colors._default_tile', (0.25, 0.1, 0))
    """Color of an empty tile."""
    OUT_OF_BOUNDS_CELL_BG = Settings.get('tilemap.|colors._out_of_bounds', (0.05, 0, 0.075))
    """Color of a tile outside the death radius."""
    WALL_COLOR = Settings.get('tilemap.|colors._walls', (0.6, 0.6, 0.6))
    """Color of a wall."""
    PIT_COLOR = Settings.get('tilemap.|colors._pits', (0.05, 0.05, 0.05))
    """Color of a pit."""
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
    """All available colors for unit sprites. 12 colors from red to purple on the rainbow."""

    def __init__(self,
            gui_mode: Optional[bool] = False,
            spoiler_mode: Optional[bool] = False,
            **kwargs,
            ):
        """
        Args:
            kwargs: Keyword arguments for `logic.battle.Battle.__init__`
            gui_mode: If True, will set arguments appropriate for the GUI.
            spoiler_mode: If True, will include information during replays that
                            may spoil the results.
        """
        if gui_mode:
            kwargs['only_bot_turn_states'] = False
            kwargs['enable_logging'] = LOGIC_DEBUG
        Battle.__init__(self, **kwargs)
        BattleAPI.__init__(self)
        self.__replay_index = 0
        self.__spoiler_mode = spoiler_mode
        self.autoplay: bool = False
        """Determines whether to automatically play the game while the `BattleManager.update` method is called."""
        self.__last_step = ping()
        self.unit_colors = [self.UNIT_COLORS[bot.COLOR_INDEX % len(self.UNIT_COLORS)] for bot in self.bots]
        self.unit_sprites = [bot.SPRITE for bot in self.bots]

    @property
    def map_name(self) -> str:
        return self._map_name

    # Replay
    def set_replay_index(self,
            index: Optional[int] = None,
            index_delta: Optional[int] = None,
            apply_vfx: bool = True,
            disable_autoplay: bool = True,
            ):
        """Set the state index of the replay.

        Will play missing states until *index* is reached or the game is over.

        *index* defaults to the index of the last state in history, unless
        *index_delta* is provided in which case it defaults to the current
        replay index.

        Args:
            index: Index of state to go to.
            index_delta: Number to add to index.
            apply_vfx: Queue vfx of the state we are going to.
            disable_autoplay: Disables autoplay.
        """
        if index is None:
            if index_delta is None:
                index = self.history_size - 1
            else:
                index = self.replay_index
        index = index % self.history_size
        if index_delta:
            index += index_delta
        index = max(0, index)
        # Play states until we reach the index (and cap index at last state)
        if self.history_size <= index:
            missing_state_count = index - self.history_size + 1
            self.play_states(missing_state_count)
            index = min(index, self.history_size-1)
        # Set the index
        apply_vfx = apply_vfx and index != self.__replay_index
        self.__replay_index = index
        if apply_vfx:
            self.add_state_vfx(index, redraw_last_steps=True)
        if disable_autoplay:
            self.autoplay = False

    @property
    def replay_mode(self) -> bool:
        """Is `BattleManager.replay_index` set to a past state."""
        return self.replay_index != self.history_size - 1

    @property
    def replay_index(self) -> int:
        """The state in history we are looking at.

        Methods that use state information will look at the state in `BattleManager.replay_index` rather than the last state."""
        return self.__replay_index

    @property
    def replay_state(self) -> State:
        """The state at index of `BattleManager.replay_index`."""
        return self.history[self.replay_index]

    def _is_spoiler_mode(self, state_index: Optional[int] = None) -> bool:
        if state_index is None:
            state_index = self.replay_index
        nothing_to_spoil = state_index == self.history_size - 1
        return self.__spoiler_mode or nothing_to_spoil

    def play_all(self, *args, **kwargs):
        """Overrides the `logic.battle.Battle.play_all` in order to set the `BattleManager.replay_index` to the last state."""
        super().play_all(*args, **kwargs)
        self.set_replay_index()

    def set_to_next_round(self, backwards: bool = False):
        """Set the replay to the next "end of round" state (or game over).

        If backwards is set, it will search for a previous state.

        See: `logic.state.State.end_of_round`.
        """
        delta = 1 if not backwards else -1
        if self.replay_state.end_of_round:
            self.set_replay_index(index_delta=1 if not backwards else -1)
        while not self.replay_state.end_of_round:
            if self.replay_state.game_over and not backwards:
                break
            self.set_replay_index(index_delta=delta)

    def preplay(self):
        """Play the entire battle, then set the `BattleManager.replay_index` to the start."""
        self.play_all()
        self.flush_vfx()
        self.set_replay_index(0)

    # Info strings
    def get_info_str(self, state_index: Optional[int] = None) -> str:
        """A multiline summary string of the current game state."""
        if state_index is None:
            state_index = self.replay_index
        timers = ''
        if self._is_spoiler_mode(state_index):
            timers = f'================= TIMERS =================\n{self.get_timer_str()}'
        return '\n'.join([
            f'{self._get_status_str(state_index)}',
            f'{self._get_units_str(state_index)}',
            timers,
            ])

    def get_timer_str(self) -> str:
        """Multiline string of bot calculation times. Confusing when in replay mode (see: `BattleManager.replay_mode`)."""
        strs = ['___ Bot ______________ ms/t ___ max ___ total ___']
        for bot in self.bots:
            total_block_time = self.bot_timer.total(bot.id)
            mean_block_time = self.bot_timer.mean(bot.id)
            max_block_time = self.bot_timer.max(bot.id)
            strs.append(''.join([
                f'{bot.gui_label:<20}',
                f'{f"{mean_block_time:.1f}":>8}',
                f'{f"{max_block_time:.1f}":>8}',
                f'{f"{total_block_time:.1f}":>10}',
                ]))
        return '\n'.join(strs)

    def _get_status_str(self, state_index: int) -> str:
        state = self.history[state_index]
        spoilers = self._is_spoiler_mode(state_index)
        # Game over results
        if state.game_over:
            winner_str = 'draw!'
            winner_id = state.winner
            if winner_id is not None:
                winner = self.bots[winner_id]
                winner_str = f'{winner.gui_label} won!'
            win_str = f'GAME OVER : {winner_str}'
        else:
            win_str = ''

        # State history
        autoplay = 'Playing' if self.autoplay else 'Paused'
        autoplay_str = f'{autoplay} <= {1000 / self.step_interval_ms:.2f} steps/s'
        end_state_index_str = f' / {self.history_size-1:>4}' if spoilers else ''
        replay_str = f'State #{state_index:>4}{end_state_index_str} : {autoplay_str}'

        # Current turn
        turn_str = self.get_state_str(state)

        # Last action
        if state.step_count == 0:
            last_step_str = '[i]new game[/i]'
            last_action_str = f'[i]started new game[/i]'
        else:
            last_state = self.history[state_index-1]
            last_step_str = f'[i]{self.get_state_str(last_state)}[/i]'
            if last_state.end_of_round:
                last_action_str = f'[i]started new round[/i]'
            else:
                last_bot = self.bots[self.history[state_index-1].current_unit]
                last_action_str = f'{state.last_action}'
                if not state.is_last_action_legal:
                    last_action_str = f'[i]ILLEGAL[/i] {last_action_str}'

        return '\n'.join([
            replay_str,
            win_str,
            '',
            f'Last step: {last_step_str}',
            f'Last action: {last_action_str}',
            '',
            f'Step:  {state.step_count:<5} Turn:  {state.turn_count:<4} Round: {state.round_count:<3}',
            f'Ring of death radius:  {state.death_radius}',
            '',
        ])

    def _get_units_str(self, state_index: int) -> str:
        state = self.history[state_index]
        unit_strs = []
        if state.current_unit is None:
            unit_strs.append(self.get_state_str(state).capitalize())
        else:
            unit_strs.append(self.get_unit_str(state.current_unit, state_index))
        unit_strs.append('___________ Next turns in round __________')
        unit_strs.extend(self.get_unit_str(unit_id, state_index) for unit_id in state.round_remaining_turns[1:])
        unit_strs.append('----------- Awaiting next round ----------')
        unit_strs.extend(self.get_unit_str(unit_id, state_index) for unit_id in state.round_done_turns if unit_id not in state.death_order)
        unit_strs.append('================== Dead ==================')
        unit_strs.extend(self.get_unit_str(unit_id, state_index) for unit_id in reversed(state.death_order))
        return '\n'.join(unit_strs)

    def get_unit_str(self,
            unit_id: int,
            state_index: Optional[int] = None,
            ) -> str:
        """A single line string with info on a unit."""
        state = self.replay_state if state_index is None else self.history[state_index]
        bot = self.bots[unit_id]
        alive = state.alive_mask[unit_id]
        ap = round(state.ap[unit_id])
        ap_spent = round(state.round_ap_spent[unit_id])
        pos = state.positions[unit_id]
        name_label = f'{bot.gui_label[:20]:<20}'
        if not alive:
            name_label = f'[s]{name_label}[/s]'
        unit_str = f'{name_label} {ap:>3} (-{ap_spent:^3}) AP <{pos.x:>3},{pos.y:>3}>'
        if not alive:
            unit_str = f'{unit_str} ; died: {state.casualties[unit_id]:>4}'
        return unit_str

    # Other
    def toggle_autoplay(self, set_to: Optional[bool] = None):
        """Toggles `BattleManager.autoplay`."""
        if self.replay_state.game_over:
            self.autoplay = False
            return
        if set_to is None:
            set_to = not self.autoplay
        self.autoplay = set_to
        self.__last_step = ping()
        self.logger(f'Auto playing...' if self.autoplay else f'Paused autoplay...')

    def set_step_rate(self, step_rate: float):
        """The step_rate determines how many steps to play at most per second
        during autoplay.

        In practice, this will be limited by FPS and blocking time of bots."""
        assert 0 < step_rate
        self.step_interval_ms = 1000 / step_rate
        self.__last_step = ping()

    def add_state_vfx(self, state_index: int, redraw_last_steps: bool = False):
        """Add all vfx of state_index to queue.

        Also clear existing vfx and add vfx from last steps if `redraw_last_steps`.
        """
        if redraw_last_steps:
            self.clear_vfx()
        start_index = max(0, state_index - 1) if redraw_last_steps else state_index
        for index in range(start_index, state_index + 1):
            for effect in self.history[index].effects:
                self.add_vfx(effect.name, effect.origin, effect.target)

    def toggle_spoilers(self, set_to: Optional[bool] = None):
        """Spoiler mode enables showing information that may be spoiler (e.g.
        total step count and calculation times).

        This can happen in case the battle has been played ahead and the
        replay_index is pointing at a past state."""
        if set_to is None:
            set_to = not self.__spoiler_mode
        self.__spoiler_mode = set_to

    def toggle_coords(self, set_to: Optional[bool] = None):
        """Toggle whether to show coordinates on tiles (for `BattleManager.get_gui_tile_info`)."""
        if set_to is None:
            set_to = not self.show_coords
        self.show_coords = set_to

    # GUI API
    def update(self):
        """Performs autoplay.

        Overrides: `api.gui.BattleAPI.update`.
        """
        if self.replay_state.game_over:
            self.autoplay = False
        if not self.autoplay:
            return
        time_delta = pong(self.__last_step)
        if time_delta >= self.step_interval_ms:
            self.set_replay_index(index_delta=1, disable_autoplay=False)
            leftover = time_delta - self.step_interval_ms
            self.__last_step = ping() - leftover

    def get_time(self) -> int:
        """Step count.

        Overrides: `api.gui.BattleAPI.get_time`.
        """
        return self.replay_state.step_count

    def get_controls(self) -> ControlMenu:
        """Returns `api.gui.Control`s for playing, autoplaying, setting replay index, and more.

        Overrides: `api.gui.BattleAPI.get_controls`.
        """
        return {
            'Battle': [
                Control('Autoplay', self.toggle_autoplay, 'spacebar'),
                Control('Preplay <!!!>', self.preplay, '^+ p'),
                *[Control(f'Set speed {r}', lambda r=r: self.set_step_rate(r), f'{i+1}') for i, r in enumerate(STEP_RATES[:5])],
            ],
            'Replay': [
                Control('Battle start', lambda: self.set_replay_index(0), '^+ left'),
                Control('Battle end <!!!>', lambda: self.play_all(), '^+ right'),
                Control('Live', lambda: self.set_replay_index(), '^ l'),
                Control('Next step', lambda: self.set_replay_index(index_delta=1), 'right'),
                Control('Prev step', lambda: self.set_replay_index(index_delta=-1), 'left'),
                Control('+10 steps', lambda: self.set_replay_index(index_delta=10), '+ right'),
                Control('-10 steps', lambda: self.set_replay_index(index_delta=-10), '+ left'),
                Control('Next round', lambda: self.set_to_next_round(), '^ right'),
                Control('Prev round', lambda: self.set_to_next_round(backwards=True), '^ left'),
            ],
            'Debug': [
                Control('Map coordinates', self.toggle_coords, '^+ d'),
                Control('Spoiler mode', self.toggle_spoilers, '^+ o'),
            ],
        }

    # Info panel
    def get_info_panel_text(self) -> str:
        """Multiline summary of the game at the current `BattleManager.replay_index`.

        Overrides: `api.gui.BattleAPI.get_info_panel_text`.
        """
        return self.get_info_str(self.replay_index)

    def get_info_panel_color(self) -> tuple[float, float, float]:
        """Green-ish color when live, blue-ish color when in `BattleManager.replay_mode`.

        Overrides: `api.gui.BattleAPI.get_info_panel_color`.
        """
        if self.replay_mode:
            # Blue-ish
            return 0.1, 0.25, 0.2
        # Green-ish
        return 0.15, 0.3, 0.05

    # Tile map
    def get_gui_tile_info(self, hex: Hexagon) -> Tile:
        """Returns a `api.gui.Tile` for *hex* at the current `BattleManager.replay_state`.

        Overrides: `api.gui.BattleAPI.get_gui_tile_info`.
        """
        state = self.replay_state
        # BG
        if hex.get_distance(MAP_CENTER) >= state.death_radius:
            bg_color = self.OUT_OF_BOUNDS_CELL_BG
        elif hex in state.pits:
            bg_color = self.PIT_COLOR
        else:
            bg_color = self.DEFAULT_CELL_BG
        # FG
        if hex in state.walls:
            fg_text = ''
            fg_color = self.WALL_COLOR
            fg_sprite = 'hex'
        elif hex in state.positions:
            unit_id = state.positions.index(hex)
            if not state.alive_mask[unit_id]:
                fg_color = 0.5, 0.5, 0.5
            else:
                fg_color = self.unit_colors[unit_id]
            fg_text = f'{unit_id}'
            fg_sprite = self.unit_sprites[unit_id]
            current = state.current_unit
            if state.current_unit is not None:
                if hex == state.positions[state.current_unit]:
                    bg_color = 1, 1, 1
        else:
            fg_color = None
            fg_text = ''
            fg_sprite = None
        if self.show_coords:
            fg_text = ', '.join(str(_) for _ in hex.xy)
        return Tile(
            bg=bg_color,
            color=fg_color,
            sprite=fg_sprite,
            text=fg_text,
            )

    def get_map_size_hint(self) -> int:
        """Tracks the `logic.state.State.death_radius` at `BattleManager.replay_index`.

        Overrides: `api.gui.BattleAPI.get_map_size_hint`.
        """
        death_radius = self.replay_state.death_radius
        if self.replay_state.round_count == 0:
            death_radius -= 1
        return max(5, death_radius)

    def handle_hex_click(self, hex: Hexagon, button: str):
        """Handles a tile being clicked on in the tilemap.

        If a unit is positioned at *hex*, will call its `api.bots.BaseBot.gui_click` method with *hex* and *button*. Otherwise will mark *hex* with a color determined by *button* using `api.gui.BattleAPI.add_vfx`.

        Overrides: `api.gui.BattleAPI.handle_hex_click`.
        """
        self.logger(f'Clicked {button} on: {hex}')
        if hex in self.replay_state.positions:
            unit_id = self.replay_state.positions.index(hex)
            vfx_seq = self.bots[unit_id].gui_click(hex, button)
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
