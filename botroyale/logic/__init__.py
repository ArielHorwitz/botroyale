"""Game mechanics.

The relevant modules for bot developers include `botroyale.logic.state` and
`botroyale.logic.battle`.
"""
from typing import Optional
from enum import IntEnum, auto as enum_auto
from botroyale.util import settings
from botroyale.util.hexagon import ORIGIN, Hexagon


class PlateType(IntEnum):
    """Enumerator for types of pressure plates. See: `botroyale.logic.plate.Plate`."""

    DEATH_RADIUS_TRAP = enum_auto()
    """Contracts the death radius."""
    PIT_TRAP = enum_auto()
    """Turns tiles into pits."""
    WALL_TRAP = enum_auto()
    """Turns tiles into walls."""


UNIT_COLORS = settings.get("gui.tilemap.colors.units")
"""All available colors for unit sprites. 12 colors in rainbow order."""
DEFAULT_CELL_BG = settings.get("gui.tilemap.colors.default_tile")
"""Color of an empty tile."""
OUT_OF_BOUNDS_CELL_BG = settings.get("gui.tilemap.colors.out_of_bounds")
"""Color of a tile outside the death radius."""
WALL_COLOR = settings.get("gui.tilemap.colors.walls")
"""Color of a wall."""
PIT_COLOR = settings.get("gui.tilemap.colors.pits")
"""Color of a pit."""
PLATE_NO_RESET_COLOR = settings.get("gui.tilemap.colors.plate_no_reset")
"""Color of a plate that will not reset its pressure."""
PLATE_RESET_COLOR = settings.get("gui.tilemap.colors.plate_reset")
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
