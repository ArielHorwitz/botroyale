"""The classic game of snake, but in hex-space."""
from typing import Union, Any
import random
from functools import partial
from collections import deque
from botroyale.api.gui import (
    GameAPI,
    BattleAPI,
    Tile,
    Control,
    InputWidget,
)
from botroyale.util.hexagon import Hexagon, ORIGIN, DIRECTIONS
from botroyale.util.time import ping, pong


MOVE_KEYS = [
    "dxzawe",
    "l,mjio",
    "631479",
    ["numpad6", "numpad3", "numpad1", "numpad4", "numpad7", "numpad9"],
]
FOOD_COLOR = (0.7, 0.3, 0.4)


class SnakeBattleAPI(BattleAPI):
    """An implementation of `api.gui.GameAPI` for the classic game of snake."""

    def __init__(
        self,
        map_size=10,
        food_count=2,
        move_feedback=False,
        enable_wraparound=False,
        frame_ms=300,
    ):
        """See module documentation for details.

        Args:
            map_size: Size of map radius
            food_count: Amount of food available at any given moment
            move_feedback: Flash the hexagons when we click to move
            enable_wraparound: Allow wrapping the map hex-wise
            frame_ms: Number of miliseconds between in-game "frames".
        """
        super().__init__()
        self.time = 0
        self.dead = False
        self.frame_ms = frame_ms
        self.map_size = map_size
        self.move_feedback = move_feedback
        self.map_tiles = ORIGIN.range(map_size)
        self.enable_wraparound = enable_wraparound
        self.wraparound_tiles = {}
        for tile in self.map_tiles:
            self.wraparound_tiles[tile] = tile
            n = map_size
            origin_offset = Hexagon(2 * n + 1, -n, -n - 1)
            for r in range(6):
                morigin = origin_offset.rotate(r)
                self.wraparound_tiles[morigin + tile] = tile
        self.snake = deque()
        self.snake.appendleft(ORIGIN)
        self.snake.appendleft(ORIGIN.neighbors[3])
        self.snake_direction = DIRECTIONS[0]
        self.food = set()
        self._last_frame = ping()
        for i in range(food_count):
            self._add_food()

    def _do_tick(self):
        self.time += 1
        next_tile = self.snake_head + self.snake_direction
        if self.enable_wraparound:
            next_tile = self.wraparound_tiles[next_tile]
        if next_tile in self.snake or ORIGIN.get_distance(next_tile) > self.map_size:
            self.snake.popleft()
            self.dead = True
        elif next_tile in self.food:
            self._add_food()
            self.food.remove(next_tile)
        else:
            self.snake.popleft()
        self.snake.append(next_tile)

    def _snake_move(self, direction_index):
        new_dir = DIRECTIONS[direction_index]
        next_tile = self.snake_head + new_dir
        if self.enable_wraparound:
            next_tile = self.wraparound_tiles[next_tile]
        if next_tile == self.snake_neck:
            return
        self.snake_direction = new_dir
        if self.move_feedback:
            self.add_vfx(
                "mark-blue", next_tile, steps=5, expire_seconds=self.frame_ms / 2000
            )

    def _add_food(self):
        next_choice = random.choice(self.map_tiles)
        while next_choice in self.snake or next_choice in self.food:
            next_choice = random.choice(self.map_tiles)
        self.food.add(next_choice)

    @property
    def snake_head(self):
        """Location of the snake's head."""
        return self.snake[-1]

    @property
    def snake_neck(self):
        """Location of the snake's neck (one segment before head)."""
        return self.snake[-2]

    # GUI API
    def update(self):
        """Called continuously (every frame) by the GUI."""
        if self.dead:
            return
        dt_ms = pong(self._last_frame)
        if dt_ms > self.frame_ms:
            self._last_frame = ping()
            self._do_tick()

    def get_time(self) -> Union[int, float]:
        """In-game time. Used by the GUI to determine when vfx need to expire."""
        return self.time

    def get_controls(self) -> list[Control]:
        """Overrides `botroyale.api.gui.BattleAPI.get_controls`."""
        controls = []
        for i in range(6):
            controls.append(Control(
                "Snake",
                f"Move {i+1}",
                partial(self._snake_move, i),
                [_[i] for _ in MOVE_KEYS],
            ))
        return controls

    # Info panel
    def get_info_panel_text(self) -> str:
        """Overrides `botroyale.api.gui.BattleAPI.get_info_panel_text`."""
        dead_str = "GAME OVER" if self.dead else ""
        return "\n".join(
            [
                dead_str,
                "",
                f"Score:      {len(self.snake)-1}",
                f"Time:       {self.time}",
                f"Speed:      {1000 / self.frame_ms:.2f} fps",
                f"Map size:   {self.map_size}",
                f"Food count: {len(self.food)}",
            ]
        )

    # Tile map
    def get_gui_tile_info(self, hex: Hexagon) -> Tile:
        """Overrides `botroyale.api.gui.BattleAPI.get_gui_tile_info`."""
        bg = (0.3, 0.3, 0.3)
        if ORIGIN.get_distance(hex) > self.map_size:
            bg = (0.1, 0.1, 0.1)

        color = None
        sprite = None
        text = None

        if self.enable_wraparound:
            if hex not in self.wraparound_tiles:
                return Tile(bg=(0, 0, 0), color=color, sprite=sprite, text=text)
            hex = self.wraparound_tiles[hex]

        if hex in self.snake:
            sprite = "hex"
            snake_index = self.snake.index(hex)
            index_ratio = snake_index / len(self.snake)
            color = (0.25, index_ratio, 1 - index_ratio)
            if self.dead and hex == self.snake_head:
                color = 1, 0, 0
                bg = 1, 0, 0

        if hex in self.food:
            sprite = "ellipse"
            color = FOOD_COLOR

        return Tile(
            bg=bg,
            color=color,
            sprite=sprite,
            text=text,
        )

    def get_map_size_hint(self) -> Union[int, float]:
        """The radius of the map size for the GUI to display."""
        s = self.map_size + 0.2
        if self.enable_wraparound:
            s = self.map_size * 1.75
        return s


class SnakeGameAPI(GameAPI):
    """An implementation of `api.gui.GameAPI` to spin up `SnakeBattleAPI`."""

    def get_new_battle(self, menu_values: dict[str, Any]) -> Union[BattleAPI, None]:
        """Overrides `botroyale.api.gui.GameAPI.get_new_battle`."""
        frame_ms = self._get_frame_ms(menu_values["game_speed"])
        map_size = menu_values["map_size"]
        food_count = menu_values["food_count"]
        enable_wraparound = menu_values["enable_wraparound"]
        move_feedback = menu_values["move_feedback"]
        return SnakeBattleAPI(
            frame_ms=frame_ms,
            map_size=map_size,
            food_count=food_count,
            enable_wraparound=enable_wraparound,
            move_feedback=move_feedback,
        )

    def _get_frame_ms(self, widget_value):
        inverted_game_speed = 1 - (widget_value / 10)
        frame_ms = 50 ** (1 + 0.75 * inverted_game_speed)
        return frame_ms

    def get_menu_widgets(self) -> list[InputWidget]:
        """Overrides `botroyale.api.gui.GameAPI.get_menu_widgets`."""
        return [
            InputWidget(
                "Game speed",
                "slider",
                default=5,
                sendto="game_speed",
                slider_range=(1, 10, 1),
            ),
            InputWidget(
                "Map size",
                "slider",
                default=10,
                sendto="map_size",
                slider_range=(3, 20, 1),
            ),
            InputWidget(
                "Food count",
                "slider",
                default=2,
                sendto="food_count",
                slider_range=(1, 10, 1),
            ),
            InputWidget("Wraparound", "toggle", sendto="enable_wraparound"),
            InputWidget("Feedback", "toggle", sendto="move_feedback"),
        ]

    def get_menu_title(self) -> str:
        """Overrides `botroyale.api.gui.GameAPI.get_menu_title`."""
        return "Snake. Press space to begin."


def entry_point_snake(args):
    """Entry point for snake."""
    from botroyale.gui.app import App

    app = App(game_api=SnakeGameAPI())
    app.run()
