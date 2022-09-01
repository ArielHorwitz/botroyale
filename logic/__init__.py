"""
Game mechanics.
"""
from typing import Optional
from enum import IntEnum, auto as enum_auto
from util.settings import Settings

__all__ = [
    'UNIT_COLORS',
    'DEFAULT_CELL_BG',
    'OUT_OF_BOUNDS_CELL_BG',
    'WALL_COLOR',
    'PIT_COLOR',
    'PLATE_COLORS',
]


class PlateType(IntEnum):
    """Enumerator for types of pressure plates. See: `logic.plate.Plate`"""

    DEATH_RADIUS_TRAP = enum_auto()
    """Contracts the death radius."""
    PIT_TRAP = enum_auto()
    """Turns tiles into pits."""
    WALL_TRAP = enum_auto()


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
DEFAULT_CELL_BG = Settings.get('tilemap.|colors._default_tile', (0.16, 0.16, 0.2))
"""Color of an empty tile."""
OUT_OF_BOUNDS_CELL_BG = Settings.get('tilemap.|colors._out_of_bounds', (0.06, 0.05, 0.04))
"""Color of a tile outside the death radius."""
WALL_COLOR = Settings.get('tilemap.|colors._walls', (0.6, 0.65, 0.6))
"""Color of a wall."""
PIT_COLOR = Settings.get('tilemap.|colors._pits', (0.25, 0.25, 0.25))
"""Color of a pit."""
PLATE_COLORS: dict[PlateType, tuple[float, float, float]] = {
    PlateType.DEATH_RADIUS_TRAP: Settings.get('tilemap.|colors._death_radius_trap', (0.05, 0.3, 0.05)),
    PlateType.PIT_TRAP: Settings.get('tilemap.|colors._pit_trap', (0.3, 0.05, 0.05)),
    PlateType.WALL_TRAP: Settings.get('tilemap.|colors._wall_trap', (0.05, 0.05, 0.3)),
}
"""Colors of all plates."""

# Make sure we are not missing plate colors
assert all([p in PLATE_COLORS for p in PlateType])
