from typing import Optional, Any
from collections import deque
from util.settings import Settings
from util.hexagon import Hexagon, ORIGIN
from logic.maps import MapCreator
from api.gui import (
    GameAPI as BaseGameAPI, BattleAPI,
    Tile, VFX, InputWidget, Control, ControlMenu,
    )


class MapEditor(MapCreator, BattleAPI):
    """The MapEditor is a wrapper for the MapCreator class that inherits from
    both logic.maps.MapCreator and api.gui.BattleAPI.

    It enables interactive map editing in the GUI."""

    DEFAULT_CELL_BG = Settings.get('tilemap.|colors._default_tile', (0.25, 0.1, 0))
    OUT_OF_BOUNDS_CELL_BG = Settings.get('tilemap.|colors._out_of_bounds', (0.05, 0, 0.075))
    WALL_COLOR = Settings.get('tilemap.|colors._walls', (0.6, 0.6, 0.6))
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
    BRUSH_COLORS = {
        'eraser': (0.25, 0.05, 0.1),
        'pit': (0.1, 0.1, 0.1),
        'wall': (0.3, 0.3, 0.3),
        'spawn': (0.05, 0.25, 0.1),
        }
    HELP_STR = '\n'.join([
        'Left click to use brush, right click to erase.',
        '',
        'Use middle mouse or press "z", "x", and "c"',
        'to switch brushes.',
        '',
        'Mirror Mode mirrors every click, such that the',
        'map may be fair and symmetrical.',
        ])

    def __init__(self):
        BattleAPI.__init__(self)
        MapCreator.__init__(self, mirror_mode=6)
        self.show_coords = False
        self.brush = 'pit'

    def apply_brush(self, hex: Hexagon):
        """Sets the contents of a tile based on the brush."""
        if self.brush == 'eraser':
            self.clear_contents(hex, mirrored=True)
        elif self.brush == 'pit':
            self.add_pit(hex)
        elif self.brush == 'wall':
            self.add_wall(hex)
        elif self.brush == 'spawn':
            self.add_spawn(hex)
        else:
            raise ValueError(f'Unknown brush type: {self.brush}')

    def set_brush(self, set_as):
        assert set_as in ('eraser', 'pit', 'wall', 'spawn')
        self.brush = set_as

    def toggle_brush(self):
        brushes = ['pit', 'wall', 'spawn']
        if self.brush not in brushes:
            self.set_brush(brushes[0])
            return
        idx = brushes.index(self.brush)
        idx = (idx + 1) % len(brushes)
        self.set_brush(brushes[idx])

    def toggle_coords(self):
        self.show_coords = not self.show_coords

    # GUI API
    def get_info_panel_text(self) -> str:
        """Overrides base class method."""
        valid_str = 'Valid map'
        if not self.check_valid():
            valid_str = 'INVALID MAP'
        return '\n'.join([
            '___ Map Editor ___',
            f'{valid_str}¹',
            '\n',
            f'Brush:           {self.brush}  × {self.mirror_mode} mirrors',
            '\n',
            f'Death radius²    {self.state.death_radius-1}',
            f'Map size         {self.state.death_radius-2}',
            f'Spawns (units)   {len(self.state.positions)}',
            f'Pits             {len(self.state.pits)}',
            f'Walls            {len(self.state.walls)}',
            '\n',
            '¹ "Invalid" usually indicates that a spawn',
            '       is unfair. Can still be exported.',
            '² Death radius is shown as on round 1',
            '\n',
            '___ Quick Help ___',
            '',
            self.HELP_STR,
            ])

    def get_info_panel_color(self) -> tuple[float, float, float]:
        """Overrides base class method."""
        return self.BRUSH_COLORS[self.brush]

    def get_gui_tile_info(self, hex: Hexagon) -> Tile:
        """Overrides base class method."""
        state = self.state
        out_of_bounds = hex.get_distance(ORIGIN) >= state.death_radius-1
        # Tile color
        if hex in state.pits:
            bg = self.PIT_COLOR
        elif out_of_bounds:
            bg = self.OUT_OF_BOUNDS_CELL_BG
        else:
            bg = self.DEFAULT_CELL_BG
        # Sprite
        color = None
        sprite = None
        text = ''
        if hex in state.walls:
            color = self.WALL_COLOR
            sprite = 'hex'
            text = ''
        elif hex in state.positions:
            unit_id = state.positions.index(hex)
            if out_of_bounds:
                color = 0.5, 0.5, 0.5
            else:
                color = self.UNIT_COLORS[unit_id % len(self.UNIT_COLORS)]
            sprite = 'bot'
            text = f'{unit_id}'

        if self.show_coords:
            text = f'{hex.x}, {hex.y}'
        return Tile(
            bg=bg,
            color=color,
            sprite=sprite,
            text=text,
            )

    def handle_hex_click(self, hex: Hexagon, button: str):
        """Overrides base class method."""
        if button == 'left':
            self.apply_brush(hex)
        elif button == 'right':
            self.clear_contents(hex, mirrored=True)
        elif button == 'middle':
            self.toggle_brush()

    def get_map_size_hint(self) -> float:
        """Overrides base class method."""
        return self.state.death_radius-1.5

    def get_controls(self) -> ControlMenu:
        """Overrides base class method."""
        return {
            'Editor': [
                Control('Increase death radius', lambda: self.increment_death_radius(1), '+ ='),
                Control('Decrease death radius', lambda: self.increment_death_radius(-1), '+ -'),
                # Clear all shares hotkey with clear vfx to refresh the selected hex vfx
                Control('Clear all', self.clear_all, '^+ c'),
                Control('Save', self.save, '^+ s'),
                Control('Load', self.load, '^+ l'),
                ],
            'Brush': [
                Control('Pit', lambda: self.set_brush('pit'), 'z'),
                Control('Wall', lambda: self.set_brush('wall'), 'x'),
                Control('Spawn', lambda: self.set_brush('spawn'), 'c'),
                Control('Eraser', lambda: self.set_brush('eraser'), 'v'),
                ],
            'Mirror Mode': [
                Control('Mirror off', lambda: self.set_mirror_mode(1), '1'),
                Control('Mirror 2', lambda: self.set_mirror_mode(2), '2'),
                Control('Mirror 3', lambda: self.set_mirror_mode(3), '3'),
                Control('Mirror 6', lambda: self.set_mirror_mode(6), '4'),
                ],
            'Debug': [
                Control('Map coordinates', self.toggle_coords, '^+ d'),
                ],
            }
