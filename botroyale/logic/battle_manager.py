"""Home of `botroyale.logic.battle_manager.BattleManager`."""
from typing import Optional, Literal
from botroyale.logic.battle import Battle
from botroyale.api.gui import BattleAPI, Tile, Control, ControlMenu
from botroyale.util.time import ping, pong
from botroyale.util import settings
from botroyale.util.hexagon import Hex, Hexagon
from botroyale.logic.state import State
from botroyale.logic import UNIT_COLORS, get_tile_info, get_tile_info_unit


STEP_RATE = settings.get("battle.default_step_rate")
STEP_RATES = settings.get("battle.toggle_step_rates")
LOGIC_DEBUG = settings.get("logging.battle")
MAP_CENTER = Hex(0, 0)


PanelMode = Literal["turns", "timers"]


class BattleManager(Battle, BattleAPI):
    """A GUI interface for `botroyale.logic.battle.Battle`.

    Provides methods for parsing, formatting, and displaying information about
    the battle, as well as GUI-related controls and display getters.

    While it can be used as an extension of `botroyale.logic.battle.Battle`, this class
    can behave surprisingly different than the base class. This is because it
    keeps track of a replay index, allowing to "look at" past states. Therefore
    it is recommended to be familiar with `BattleManager.set_replay_index`.
    """

    show_coords = False
    step_interval_ms = 1000 / STEP_RATE

    def __init__(self, gui_mode: Optional[bool] = False, **kwargs):
        """Initialize the class.

        Args:
            kwargs: Keyword arguments for `botroyale.logic.battle.Battle.__init__`
            gui_mode: If True, will set arguments appropriate for the GUI.
        """
        if gui_mode:
            kwargs["only_bot_turn_states"] = False
            kwargs["enable_logging"] = LOGIC_DEBUG
        Battle.__init__(self, **kwargs)
        BattleAPI.__init__(self)
        self.__replay_index = 0
        self.autoplay: bool = False
        self.__last_step = ping()
        self.unit_colors = [
            UNIT_COLORS[bot.COLOR_INDEX % len(UNIT_COLORS)] for bot in self.bots
        ]
        self.unit_sprites = [bot.SPRITE for bot in self.bots]
        self.__panel_mode: PanelMode = "turns"

    # Replay
    def set_replay_index(
        self,
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
            index = min(index, self.history_size - 1)
        # Set the index
        apply_vfx = apply_vfx and index != self.__replay_index
        self.__replay_index = index
        if apply_vfx:
            self.add_state_vfx(index, redraw_last_steps=True)
            self._highlight_current_unit()
        if disable_autoplay:
            self.autoplay = False

    @property
    def replay_mode(self) -> bool:
        """Is `BattleManager.replay_index` set to a past state."""
        return self.replay_index != self.history_size - 1

    @property
    def replay_index(self) -> int:
        """The state in history we are looking at.

        Methods that use state information will look at the state in
        `BattleManager.replay_index` rather than the last state.
        """
        return self.__replay_index

    @property
    def replay_state(self) -> State:
        """The state at index of `BattleManager.replay_index`."""
        return self.history[self.replay_index]

    def play_all(self, *args, **kwargs):
        """Overrides the parent method in order to set the replay_index.

        See: `BattleManager.replay_index`.
        """
        super().play_all(*args, **kwargs)
        self.set_replay_index()

    def set_to_next_round(self, backwards: bool = False):
        """Set the replay to the next "end of round" state (or game over).

        If backwards is set, it will search for a previous state.

        See: `botroyale.logic.state.State.end_of_round`.
        """
        delta = 1 if not backwards else -1
        if self.replay_state.end_of_round:
            self.set_replay_index(index_delta=1 if not backwards else -1)
        while not self.replay_state.end_of_round:
            if self.replay_state.game_over and not backwards:
                break
            self.set_replay_index(index_delta=delta)

    def preplay(self):
        """Play the entire battle, then set the replay index to the start.

        See: `BattleManager.replay_index`.
        """
        self.play_all()
        self.flush_vfx()
        self.set_replay_index(0)

    # Info strings
    def get_info_str(self, state_index: Optional[int] = None) -> str:
        """A multiline summary string of the current game state."""
        if state_index is None:
            state_index = self.replay_index

        strs = [
            f"{self._get_status_str(state_index)}",
            "",
        ]
        if self.__panel_mode == "turns":
            strs.extend(
                [
                    f"{self._get_turn_order_str(state_index)}",
                    "",
                    f"{self._get_last_action_str(state_index)}",
                ]
            )
        elif self.__panel_mode == "timers":
            strs.append(f"{self.get_timer_str()}")
        else:
            raise ValueError(f"Unknown panel mode: {self.__panel_mode}")
        return "\n".join(strs)

    def get_timer_str(self) -> str:
        """Multiline string of bot calculation times.

        Unlike other methods in this class, the result of this method does not
        consider `BattleManager.replay_mode`. The times shown are updated to the
        latest state in the battle. This is because
        `botroyale.logic.battle.Battle.bot_timer` is updated in place on each
        new state.
        """
        strs = [
            "      Bot Calculation Times (ms)",
            "--------------------------------------",
            "       Bot             Mean      Max",
            "",
        ]
        if self.replay_mode:
            strs.insert(0, "Times are not live!\n\n")
        for bot in self.bots:
            mean_block_time = self.bot_timer.mean(bot.id)
            max_block_time = self.bot_timer.max(bot.id)
            strs.append(
                "".join(
                    [
                        f"{bot.gui_label:<20}",
                        f'{f"{mean_block_time:,.1f}":>8} ',
                        f'{f"{max_block_time:,.1f}":>8}',
                    ]
                )
            )
        return "\n".join(strs)

    def _get_status_str(self, state_index: int) -> str:
        state = self.history[state_index]
        autoplay = "Playing" if self.autoplay else "Paused"
        status = f"{autoplay} <= {1000 / self.step_interval_ms:.2f} steps/s"
        if state.game_over:
            winner_str = "draw!"
            winner_id = state.winner
            if winner_id is not None:
                winner = self.bots[winner_id]
                winner_str = f"{winner.gui_label} won!"
            status = f"GAME OVER : {winner_str}"
        return "\n".join(
            [
                status,
                "",
                f"Step:{state.step_count:^5}Turn:{state.turn_count:^4}"
                f"Round:{state.round_count:^3}RoD: {state.death_radius:>2}",
            ]
        )

    def _get_last_action_str(self, state_index: int) -> str:
        state = self.history[state_index]
        if state.step_count == 0:
            last_step_str = "[i]New game[/i]"
            last_action_str = "[i]Started new game[/i]"
        else:
            last_state = self.history[state_index - 1]
            last_step_str = f"[i]{self.get_state_str(last_state).capitalize()}[/i]"
            if last_state.end_of_round:
                last_action_str = f"[i]Started round {state.round_count}[/i]"
            else:
                last_action_str = f"{state.last_action}"
                if not state.is_last_action_legal:
                    last_action_str = f"[i]ILLEGAL[/i] {last_action_str}"
        return "\n".join(
            [
                f"Last step:   {last_step_str}",
                f"Last action: {last_action_str}",
            ]
        )

    def _get_turn_order_str(self, state_index: int) -> str:
        state = self.history[state_index]
        unit_strs = [
            "____________ Current turn ____________",
        ]
        if state.current_unit is None:
            r = f"{state.round_count:>2} -> {state.round_count+1:>2}"
            unit_strs.append(f"            NEW ROUND {r}")
        else:
            unit_strs.append(f"{self.get_unit_str(state.current_unit, state_index)}")
            unit_strs.append("\n________ Next turns in round _________")
        unit_strs.extend(
            self.get_unit_str(unit_id, state_index)
            for unit_id in state.round_remaining_turns[1:]
        )
        unit_strs.append("\n________ Awaiting next round _________")
        unit_strs.extend(
            self.get_unit_str(unit_id, state_index)
            for unit_id in state.next_round_order
            if unit_id in state.round_done_turns
        )
        unit_strs.append("\n______________ Dead __________________")
        unit_strs.extend(
            self.get_unit_str(unit_id, state_index)
            for unit_id in reversed(state.death_order)
        )
        return "\n".join(unit_strs)

    def get_unit_str(self, unit_id: int, state_index: Optional[int] = None) -> str:
        """A single line string with info on a unit."""
        state = self.replay_state if state_index is None else self.history[state_index]
        bot = self.bots[unit_id]
        name_label = f"{bot.gui_label[:20]:<20}"
        alive = state.alive_mask[unit_id]
        if not alive:
            return f"[s]{name_label}[/s] died @ step #{state.casualties[unit_id]:^4}"
        ap = round(state.ap[unit_id])
        ap_spent = round(state.round_ap_spent[unit_id])
        return f"{name_label}  {ap:>3} AP {ap_spent:>3} used"

    # Other
    def toggle_autoplay(self, set_to: Optional[bool] = None):
        """Toggles autoplay."""
        if self.replay_state.game_over:
            self.autoplay = False
            return
        if set_to is None:
            set_to = not self.autoplay
        self.autoplay = set_to
        self.__last_step = ping()
        self.logger("Auto playing..." if self.autoplay else "Paused autoplay...")

    def set_step_rate(self, step_rate: float):
        """Determines how many steps to play at most per second during autoplay.

        In practice, this will be limited by FPS and blocking time of bots.
        """
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

    def _highlight_current_unit(self):
        current_uid = self.replay_state.current_unit
        if current_uid is not None:
            pos = self.replay_state.positions[current_uid]
            self.add_vfx("highlight", pos, steps=1)

    def toggle_coords(self, set_to: Optional[bool] = None):
        """Toggle whether to show coordinates on tiles."""
        if set_to is None:
            set_to = not self.show_coords
        self.show_coords = set_to

    def set_panel_mode(self, set_to: Optional[PanelMode] = None):
        """Sets the info panel mode. One of: 'turns', 'timers'. Default: 'turns'."""
        if set_to is None:
            set_to = "turns"
        assert set_to in ["turns", "timers"]
        self.__panel_mode = set_to

    # GUI API
    def update(self):
        """Performs autoplay.

        Overrides: `botroyale.api.gui.BattleAPI.update`.
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

        Overrides: `botroyale.api.gui.BattleAPI.get_time`.
        """
        return self.replay_state.step_count

    def get_controls(self) -> ControlMenu:
        """Return controls for playing, autoplaying, replay index, and more.

        Overrides: `botroyale.api.gui.BattleAPI.get_controls`.
        """
        return {
            "Battle": [
                Control("Autoplay", self.toggle_autoplay, "spacebar"),
                Control("Preplay <!!!>", self.preplay, "^+ p"),
                *[
                    Control(
                        f"Set speed {r}", lambda r=r: self.set_step_rate(r), f"{i + 1}"
                    )
                    for i, r in enumerate(STEP_RATES[:5])
                ],
            ],
            "Replay": [
                Control("Battle start", lambda: self.set_replay_index(0), "^+ left"),
                Control("Battle end <!!!>", lambda: self.play_all(), "^+ right"),
                Control("Live", lambda: self.set_replay_index(), "^ l"),
                Control(
                    "Next step", lambda: self.set_replay_index(index_delta=1), "right"
                ),
                Control(
                    "Prev step", lambda: self.set_replay_index(index_delta=-1), "left"
                ),
                Control(
                    "+10 steps",
                    lambda: self.set_replay_index(index_delta=10),
                    "+ right",
                ),
                Control(
                    "-10 steps",
                    lambda: self.set_replay_index(index_delta=-10),
                    "+ left",
                ),
                Control("Next round", lambda: self.set_to_next_round(), "^ right"),
                Control(
                    "Prev round",
                    lambda: self.set_to_next_round(backwards=True),
                    "^ left",
                ),
            ],
            "Display": [
                Control("Turn order", lambda: self.set_panel_mode("turns"), "^ o"),
                Control(
                    "Calculation timers", lambda: self.set_panel_mode("timers"), "^ p"
                ),
                Control("Map coordinates", self.toggle_coords, "^+ d"),
            ],
        }

    # Info panel
    def get_info_panel_text(self) -> str:
        """Multiline summary of the game at the current `BattleManager.replay_index`.

        Overrides: `botroyale.api.gui.BattleAPI.get_info_panel_text`.

        Returns:
            Return value of `BattleManager.get_info_str`.
        """
        return self.get_info_str(self.replay_index)

    def get_info_panel_color(self) -> tuple[float, float, float]:
        """Green-ish color when live, blue-ish color when in replay mode.

        See: `BattleManager.replay_mode`.

        Overrides: `botroyale.api.gui.BattleAPI.get_info_panel_color`.
        """
        if self.replay_mode:
            # Blue-ish
            return 0.1, 0.25, 0.2
        # Green-ish
        return 0.15, 0.3, 0.05

    # Tile map
    def get_gui_tile_info(self, hex: Hexagon) -> Tile:
        """Return a `botroyale.api.gui.Tile` for *hex* at the current replay state.

        See: `BattleManager.replay_state`

        Overrides: `botroyale.api.gui.BattleAPI.get_gui_tile_info`.
        """
        state = self.replay_state

        tile, bg = get_tile_info(hex, state)
        sprite, color, text = get_tile_info_unit(
            hex,
            state,
            self.unit_sprites,
            self.unit_colors,
        )

        if self.show_coords:
            text = f"{hex.x},{hex.y}"

        return Tile(
            tile=tile,
            bg=bg,
            color=color,
            sprite=sprite,
            text=text,
        )

    def get_map_size_hint(self) -> int:
        """Tracks `botroyale.logic.state.State.death_radius`.

        Overrides: `botroyale.api.gui.BattleAPI.get_map_size_hint`.
        """
        death_radius = self.replay_state.death_radius
        if self.replay_state.round_count == 0:
            death_radius -= 1
        return max(5, death_radius)

    def handle_hex_click(self, hex: Hexagon, button: str, mods: str):
        """Handles a tile being clicked on in the tilemap.

        Overrides: `botroyale.api.gui.BattleAPI.handle_hex_click`.
        """
        click = f"{mods} {button}"
        self.logger(f"Clicked {click} on: {hex}")
        # Normal click and Control click: info
        if mods == "" or mods == "^":
            if button == "left":
                # Show targets of a plate
                p = self.replay_state.get_plate(hex)
                if p:
                    for t in p.targets:
                        self.add_vfx("highlight", t, steps=1)
        # Shift click: mark
        elif mods == "+":
            vfx = {"left": "green", "right": "red"}.get(button, "blue")
            self.add_vfx(f"mark-{vfx}", hex, steps=1)
        # Alt click: bot debug
        elif mods == "!":
            if hex in self.replay_state.positions:
                unit_id = self.replay_state.positions.index(hex)
                vfx_seq = self.bots[unit_id].gui_click(hex, button, mods)
                if vfx_seq is not None:
                    for vfx_kwargs in vfx_seq:
                        vfx_kwargs["steps"] = 1
                        self.add_vfx(**vfx_kwargs)
