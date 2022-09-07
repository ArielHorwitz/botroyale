"""Game mechanics."""
from typing import Optional
from enum import IntEnum, auto as enum_auto
from botroyale.util.settings import Settings
from botroyale.util.hexagon import ORIGIN, Hexagon


class PlateType(IntEnum):
    """Enumerator for types of pressure plates. See: `botroyale.logic.plate.Plate`."""

    DEATH_RADIUS_TRAP = enum_auto()
    """Contracts the death radius."""
    PIT_TRAP = enum_auto()
    """Turns tiles into pits."""
    WALL_TRAP = enum_auto()
    """Turns tiles into walls."""
    ERASE_TRAP = enum_auto()


UNIT_COLORS = Settings.get(
    "tilemap.|colors.|units",
    [
        (0.6, 0, 0.1),  # Red
        (0.9, 0.3, 0.4),  # Pink
        (0.8, 0.7, 0.1),  # Yellow
        (0.7, 0.4, 0),  # Orange
        (0.1, 0.4, 0),  # Green
        (0.4, 0.7, 0.1),  # Lime
        (0.1, 0.7, 0.7),  # Teal
        (0.1, 0.4, 0.9),  # Blue
        (0, 0.1, 0.5),  # Navy
        (0.4, 0, 0.7),  # Violet
        (0.7, 0.1, 0.9),  # Purple
        (0.7, 0, 0.5),  # Magenta
    ],
)
"""All available colors for unit sprites. 12 colors in rainbow order."""
DEFAULT_CELL_BG = Settings.get("tilemap.|colors._default_tile", (0.16, 0.16, 0.2))
"""Color of an empty tile."""
OUT_OF_BOUNDS_CELL_BG = Settings.get(
    "tilemap.|colors._out_of_bounds", (0.06, 0.05, 0.04)
)
"""Color of a tile outside the death radius."""
WALL_COLOR = Settings.get("tilemap.|colors._walls", (0.6, 0.65, 0.6))
"""Color of a wall."""
PIT_COLOR = Settings.get("tilemap.|colors._pits", (0.25, 0.25, 0.25))
"""Color of a pit."""
PLATE_NO_RESET_COLOR = Settings.get("tilemap.|colors._plate_no_reset", (0.4, 0.45, 0.6))
"""Color of a plate that will not reset its pressure."""
PLATE_RESET_COLOR = Settings.get("tilemap.|colors._plate_reset", (0.4, 0.4, 0.65))
"""Color of a plate that will reset its pressure."""


def get_tile_info(
    hex: Hexagon,
    state: "logic.state.State",  # noqa  (get F821 error for undefined name)
    disallow_double: bool = True,
) -> tuple[str, tuple[float, float, float]]:
    """Get a tile's background sprite and color.

    Args:
        hex: The tile.
        state: The state.
        disallow_double: If true, will show a special sprite/color when more
            than one solution was found. E.g. show the "error" sprite if the
            tile contains both a pit and a wall.

    Returns:
        A (sprite, color) tuple.
    """
    found = 0
    color = DEFAULT_CELL_BG
    sprite = "hex"
    if hex.get_distance(ORIGIN) >= state.death_radius:
        color = OUT_OF_BOUNDS_CELL_BG
    if hex in state.pits:
        found += 1
        color = PIT_COLOR
        sprite = "pit"
    if hex in state.walls:
        found += 1
        color = WALL_COLOR
        sprite = "wall"
    if hex in state.plates:
        found += 1
        plate = state.get_plate(hex)
        start_color = (
            PLATE_RESET_COLOR if plate.pressure_reset else PLATE_NO_RESET_COLOR
        )
        intensity = -1 / min(plate.pressure, -1)
        color = tuple(c * intensity for c in start_color)
        sprite = f"plate_{plate.plate_type.name.lower()}"
    if found > 1 and disallow_double:
        color = 1, 1, 1
        sprite = "error"
    return sprite, color


def get_tile_info_unit(
    hex: Hexagon,
    state: "logic.state.State",  # noqa  (get F821 error for undefined name)
    unit_sprites: Optional[list[str]] = None,
    unit_colors: Optional[list[tuple[float, float, float]]] = None,
    disallow_double: bool = True,
) -> tuple[str, tuple[float, float, float], str]:
    """Get a tile's foreground (unit) sprite, color, and text.

    Args:
        hex: The tile.
        state: The state.
        unit_sprites: A list of sprites for the units by uid.
        unit_colors: A list of colors for the units by uid.
        disallow_double: If true, will show a special sprite/color if more than
            one unit was found. I.e. show the "error" sprite if the tile
            contains more than one unit.

    Returns:
        A (sprite, color, text) tuple.
    """
    sprite = None
    color = None
    text = None
    unit_count = state.positions.count(hex)
    if unit_count > 1 and disallow_double:
        sprite = "error"
        color = 1, 1, 1
    elif unit_count == 1:
        if unit_colors is None:
            unit_colors = UNIT_COLORS
        uid = state.positions.index(hex)
        alive = state.alive_mask[uid]
        color = unit_colors[uid % len(unit_colors)] if alive else (0.5, 0.5, 0.5)
        if unit_sprites is None:
            sprite = "bot"
        else:
            sprite = unit_sprites[uid % len(unit_sprites)]
        text = str(uid)
    return sprite, color, text
