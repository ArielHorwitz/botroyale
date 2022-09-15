"""A game of tetris."""
from typing import Union, Any, Optional
import random
from functools import partial
from botroyale.api.gui import (
    GameAPI,
    BattleAPI,
    Tile,
    Control,
    InputWidget,
)
from botroyale.util.hexagon import Hexagon, Hex, DIRECTIONS
from botroyale.util.time import ping, pong


UP = DIRECTIONS[4]
DOWN = DIRECTIONS[1]
LEFT = DIRECTIONS[3]
RIGHT = DIRECTIONS[0]
TOP_RIGHT = DIRECTIONS[5]
BOT_LEFT = DIRECTIONS[2]
SHAPES = {
    "line": {Hex(-1, 1), Hex(0, -1)},
    "bar": {Hex(-1, 2), Hex(-1, 1), Hex(0, -1), Hex(1, -2)},
    "wings": {Hex(-1, 0), Hex(0, 1)},
    "triangle": {Hex(-1, 0), Hex(-1, 1)},
    "brick": {Hex(-1, 0), Hex(-1, 1), Hex(0, 1)},
    "mesa": {Hex(-1, 0), Hex(-1, 1), Hex(0, 1), Hex(1, 0)},
    "lever left": {Hex(-1, 0), Hex(1, 0), Hex(0, 1)},
    "lever right": {Hex(-1, 0), Hex(1, 0), Hex(0, -1)},
    "bowtie": {Hex(-1, 0), Hex(-1, -1), Hex(0, 1), Hex(1, 0)},
    "snake": {Hex(-2, -1), Hex(-1, 0), Hex(1, 0), Hex(1, 1)},
    "pickaxe": {Hex(-1, 0), Hex(1, 0), Hex(0, 1), Hex(0, -1)},
}
DEFAULT_UNINCLUDE_SHAPES = {"bowtie", "snake", "pickaxe"}
COLOR_EMPTY = (0.1, 0.1, 0.1)
COLOR_SHAPE = (0.7, 0.1, 0.1)
COLOR_SHAPE_BOLD = (0.7, 0.3, 0.1)
COLOR_BLOCK = (0.4, 0.1, 0.8)
COLOR_BORDER = (0.05, 0.4, 0.2)
COLOR_EDGE = (0.3, 0.3, 0.3)


def _get_shape_tiles(shape, pos, rotation):
    tiles = {pos + t.rotate(rotation) for t in SHAPES[shape]}
    tiles.add(pos)
    return tiles


class _Board:
    def __init__(self, width=5, height=5):
        assert height % 2 == 1
        assert height >= 5
        assert width % 2 == 1
        assert width >= 5
        padding = 4
        height_radius = int((height - 1) / 2)
        width_radius = int((width - 1) / 2)
        self.width = width
        self.height = height
        self.size_hint = max(width - 2, height_radius)
        h = height_radius + 1
        w = width_radius + 1
        # top_left = Hexagon(q=-h - w, r=h, s=w)
        bot_left = Hexagon(q=h - w, r=-h, s=w)
        top_right = Hexagon(q=-h + w, r=h, s=-w)
        bot_right = Hexagon(q=h + w, r=-h, s=-w)
        self.top_mid = Hexagon(q=-h + 1, r=h - 1, s=0)
        left_axis = [bot_left + UP] + list(
            bot_left.straight_line(bot_left + UP, height - 1)
        )
        self.hlines = []
        for t in left_axis:
            line = [t + RIGHT] + list(t.straight_line(t + RIGHT, width - 1))
            line = set(line)
            self.hlines.append(line)
        left_axis = set(left_axis)
        right_axis = set(bot_right.straight_line(bot_right + UP, height - 1)) | {
            bot_right + UP
        }
        bot_axis = set((bot_left + LEFT).straight_line(bot_left, width + 2)) | {
            bot_left + LEFT,
            bot_left,
        }
        self.left_border = left_axis
        self.right_border = right_axis
        self.borders = left_axis | right_axis
        self.edge = bot_axis
        for i in range(padding):
            left_axis = {t + LEFT for t in left_axis}
            right_axis = {t + RIGHT for t in right_axis}
            bot_axis = {t + DOWN for t in bot_axis}
            self.borders |= left_axis | right_axis
            self.edge |= bot_axis
        self.display_tile = top_right + RIGHT
        for i in range(3):
            self.display_tile += RIGHT
        for i in range(3):
            self.display_tile += DOWN


class TetrisBattleAPI(BattleAPI):
    """An implementation of `api.gui.GameAPI` for the classic game of tetris."""

    def __init__(
        self,
        width: int = 11,
        height: int = 21,
        frame_ms: int = 500,
        include_shapes: Optional[list[str]] = None,
    ):
        """See module documentation for details.

        Args:
            widget: Board width.
            height: Board height.
            frame_ms: Number of miliseconds between each in-game tick.
            include_shapes: List of shapes to include. Default: all.
        """  # noqa: D417
        super().__init__()
        if include_shapes is None:
            include_shapes = list(SHAPES.keys())
        self.including_shapes = include_shapes
        self.time = 0
        self.score = 0
        self.frame_ms = frame_ms
        self.game_over = False
        self.autoplay = False
        self.debug_mode = 0
        self._last_frame = ping()
        self.board = _Board(width, height)
        self.shape_name = None
        self.shape_rotation = 0
        self.shape_pos = None
        self.next_shape_name = random.choice(self.including_shapes)
        self.next_shape_rotation = random.randint(0, 5)
        self.premoved = False
        self.blocks = set()
        self._spawn_shape()

    def _do_tick(self):
        self.time += 1
        if self.premoved:
            self.premoved = False
            return
        new_pos = self.shape_pos + DOWN
        new_tiles = _get_shape_tiles(self.shape_name, new_pos, self.shape_rotation)
        collision = self.check_shape_collision(new_tiles)
        if collision:
            self._spawn_shape()
        else:
            self.shape_pos = new_pos

    def shape_move(self, direction):
        """User requested to move the shape."""
        if not self.autoplay or self.game_over:
            return
        new_pos = self.shape_pos + direction
        new_tiles = _get_shape_tiles(self.shape_name, new_pos, self.shape_rotation)
        collision = self.check_shape_collision(new_tiles)
        if collision and direction != DOWN:
            new_pos += DOWN
            new_tiles = _get_shape_tiles(self.shape_name, new_pos, self.shape_rotation)
            collision = self.check_shape_collision(new_tiles)
            if not collision:
                self.premoved = True
        if not collision:
            self.shape_pos = new_pos
        return not collision

    def shape_rotate(self, dr):
        """User requested to rotate the shape."""
        if not self.autoplay or self.game_over:
            return
        new_rot = self.shape_rotation + dr
        new_shape_tiles = _get_shape_tiles(self.shape_name, self.shape_pos, new_rot)
        collision = self.check_shape_collision(new_shape_tiles)
        if not collision:
            self.shape_rotation = new_rot

    def shape_drop(self):
        """User requested to drop the shape until frozen."""
        while self.shape_move(DOWN):
            pass

    # Utility methods
    @property
    def shape_tiles(self):
        """All hexes of the current shape."""
        return _get_shape_tiles(self.shape_name, self.shape_pos, self.shape_rotation)

    def check_shape_collision(self, shape_tiles):
        """If the shape tiles touch something that the shape should not."""
        return (
            shape_tiles & self.blocks
            or shape_tiles & self.board.edge
            or shape_tiles & self.board.borders
        )

    def _spawn_shape(self):
        self._freeze_shape()
        # Spawn new shape
        self.shape_name = self.next_shape_name
        self.shape_rotation = self.next_shape_rotation
        self.shape_pos = self.board.top_mid
        if self.blocks & self.shape_tiles:
            self.game_over = True
        # Prepare next shape
        self.next_shape_name = random.choice(self.including_shapes)
        self.next_shape_rotation = random.randint(0, 5)
        self.next_shape_display_tiles = _get_shape_tiles(
            self.next_shape_name, self.board.display_tile, self.next_shape_rotation
        )

    def _freeze_shape(self):
        if self.shape_name is None:
            return
        self.blocks |= self.shape_tiles
        lines_scored = 0
        for i, line in reversed(list(enumerate(self.board.hlines))):
            full_line = len(line - self.blocks) == 0
            if full_line:
                lines_scored += 1
                for t in line:
                    self.add_vfx("highlight", t)
                self.blocks -= line
                self._lower_blocks(i)
        self.score += lines_scored**2

    def _lower_blocks(self, from_line):
        for line_above in self.board.hlines[from_line:]:
            line_blocks = self.blocks & line_above
            self.blocks -= line_above
            self.blocks |= {t + DOWN for t in line_blocks}

    # Misc
    def toggle_autoplay(self):
        """Toggles autoplay."""
        self.autoplay = not self.autoplay
        self._last_frame = ping()
        if self.game_over:
            self.autoplay = False

    def _toggle_debug_mode(self):
        self.debug_mode = (self.debug_mode + 1) % 5

    # GUI API
    def update(self):
        """Called continuously (every frame) by the GUI."""
        if not self.autoplay or self.game_over:
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
        return [
            Control("Tetris", "Toggle pause", self.toggle_autoplay, "spacebar"),
            Control("Tetris", "Toggle numbers", self._toggle_debug_mode, "^+ d"),
            Control("Tetris", "Rotate CCW", partial(self.shape_rotate, 1), "q"),
            Control("Tetris", "Rotate CW", partial(self.shape_rotate, -1), "e"),
            Control("Tetris", "Left", partial(self.shape_move, LEFT), "a"),
            Control("Tetris", "Right", partial(self.shape_move, RIGHT), "d"),
            Control("Tetris", "Down", partial(self.shape_move, DOWN), "s"),
            Control("Tetris", "Drop", partial(self.shape_drop), "x"),
            Control("Tetris", "Left (alt)", partial(self.shape_move, LEFT), "left"),
            Control("Tetris", "Right (alt)", partial(self.shape_move, RIGHT), "right"),
            Control("Tetris", "Down (alt)", partial(self.shape_move, DOWN), "down"),
            Control("Tetris", "Spawn shape", self._spawn_shape, "enter"),
        ]

    # Info panel
    def get_info_panel_text(self) -> str:
        """Overrides `botroyale.api.gui.BattleAPI.get_info_panel_text`."""
        autoplay_str = "Playing" if self.autoplay else "Paused"
        if self.game_over:
            autoplay_str = "GAME OVER!"
        return "\n".join(
            [
                autoplay_str,
                "",
                f"Score:      {self.score}",
                f"Time:       {self.time}",
                "",
                f"Speed:      {1000 / self.frame_ms:.2f} fps",
                f"Width:      {self.board.width}",
                f"Height:     {self.board.height}",
                "",
                f"Shape:      {self.shape_name}",
                f"Shape pos:  {self.shape_pos}",
                f"Shape rot:  {self.shape_rotation}",
                f"Debug mode: {self.debug_mode}",
            ]
        )

    # Tile map
    def get_gui_tile_info(self, hex: Hexagon) -> Tile:  # noqa: C901
        """Overrides `botroyale.api.gui.BattleAPI.get_gui_tile_info`."""
        bg = COLOR_EMPTY
        color = None
        sprite = None
        text = None
        # BG
        if hex in self.board.left_border or hex in self.board.right_border:
            bg = COLOR_BORDER
        elif hex in self.board.edge:
            bg = COLOR_EDGE
        # Sprite
        if hex == self.shape_pos:
            sprite = "hex"
            color = COLOR_SHAPE_BOLD
        elif hex in self.shape_tiles:
            sprite = "hex"
            color = COLOR_SHAPE
        elif hex in self.blocks:
            sprite = "hex"
            color = COLOR_BLOCK
        elif hex in self.next_shape_display_tiles:
            sprite = "hex"
            color = COLOR_SHAPE
        # Text
        if self.debug_mode == 1:
            text = f"{hex.q}"
        elif self.debug_mode == 2:
            text = f"{hex.r}"
        elif self.debug_mode == 3:
            text = f"{hex.s}"
        elif self.debug_mode == 4:
            text = f"{hex.x},{hex.y}"
        # Fade
        if not self.autoplay:
            if bg is not None:
                bg = tuple(c * 0.5 for c in bg)
        if self.game_over:
            if color is not None:
                color = tuple(c * 0.5 for c in color)

        return Tile(
            bg=bg,
            color=color,
            sprite=sprite,
            text=text,
        )

    def get_map_size_hint(self) -> Union[int, float]:
        """The radius of the map size for the GUI to display."""
        return self.board.size_hint


class TetrisGameAPI(GameAPI):
    """An implementation of `api.gui.GameAPI` to spin up `TetrisBattleAPI`."""

    def get_new_battle(self, menu_values: dict[str, Any]) -> Union[BattleAPI, None]:
        """Overrides `botroyale.api.gui.GameAPI.get_new_battle`."""
        frame_ms = self._get_frame_ms(menu_values["game_speed"])
        width = menu_values["width"]
        height = menu_values["height"]
        width += width % 2 == 0
        height += height % 2 == 0
        include_shapes = []
        for k, v in menu_values.items():
            if k.startswith("shape-") and v:
                include_shapes.append(k[6:])
        return TetrisBattleAPI(
            frame_ms=frame_ms, include_shapes=include_shapes, width=width, height=height
        )

    def _get_frame_ms(self, widget_value):
        inverted_game_speed = 1 - (widget_value / 10)
        frame_ms = 150 ** (1 + 0.5 * inverted_game_speed)
        print(f"{frame_ms=}")
        return frame_ms

    def get_menu_widgets(self) -> list[InputWidget]:
        """Overrides `botroyale.api.gui.GameAPI.get_menu_widgets`."""
        shape_toggles = []
        for shape in SHAPES.keys():
            include = shape not in DEFAULT_UNINCLUDE_SHAPES
            shape_toggles.append(
                InputWidget(
                    shape.capitalize(),
                    "toggle",
                    default=include,
                    sendto=f"shape-{shape}",
                )
            )
        return [
            InputWidget("Shapes", "divider"),
            *shape_toggles,
            InputWidget("Game settings", "divider"),
            InputWidget(
                "Game speed",
                "slider",
                default=5,
                sendto="game_speed",
                slider_range=(1, 10, 1),
            ),
            InputWidget(
                "Width",
                "slider",
                default=10,
                sendto="width",
                slider_range=(5, 20, 1),
            ),
            InputWidget(
                "Height",
                "slider",
                default=20,
                sendto="height",
                slider_range=(5, 35, 1),
            ),
        ]

    def get_info_panel_text(self) -> str:
        """Overrides `botroyale.api.gui.GameAPI.get_menu_title`."""
        return "Tetris. Press space to begin."


def entry_point_tetris(args):
    """Entry point for tetris."""
    from botroyale.gui.app import App

    app = App(game_api=TetrisGameAPI())
    app.run()
