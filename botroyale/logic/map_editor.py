"""Home of `botroyale.logic.map_editor.MapEditor`."""
from enum import IntEnum
from typing import Optional
from botroyale.logic.plate import Plate, PlateType
from botroyale.util.hexagon import Hexagon
from botroyale.logic.maps import MapCreator
from botroyale.api.gui import (
    BattleAPI,
    Tile,
    Control,
    ControlMenu,
)
from botroyale.logic import get_tile_info, get_tile_info_unit, PLATE_RESET_COLOR


__pdoc__ = {}
BrushType = IntEnum(
    "BrushType",
    [
        "SPAWN",
        "PIT",
        "WALL",
        *[p.name for p in PlateType],
    ],
)
__pdoc__["BrushType"] = False
BRUSH_HOTKEYS = "qweasdzxc"
BRUSH_COLORS = {
    BrushType.PIT: (0.1, 0.1, 0.1),
    BrushType.WALL: (0.3, 0.3, 0.3),
    BrushType.SPAWN: (0.05, 0.25, 0.1),
    **{getattr(BrushType, p.name): PLATE_RESET_COLOR for p in PlateType},
}
DEFAULT_PRESSURE = -2
MIN_PRESSURE = -5


class MapEditor(MapCreator, BattleAPI):
    """A GUI interface for `botroyale.logic.maps.MapCreator`.

    Enables interactive map editing in the GUI.
    """

    HELP_STR = "\n".join(
        [
            "Left click to use brush, right click to erase.",
            "",
            'Use middle mouse or press "z", "x", and "c"',
            "to switch brushes.",
            "",
            "Mirror Mode mirrors every click, such that the",
            "map may be fair and symmetrical.",
        ]
    )

    def __init__(self, load_map: Optional[str] = None):
        """Initialize the class."""
        BattleAPI.__init__(self)
        MapCreator.__init__(self, mirror_mode=6)
        if load_map is not None:
            self.load(load_map)
        self.show_coords = False
        self.selected_tiles: set[Hexagon] = set()
        self.brush: BrushType = BrushType.SPAWN
        self.plate_pressure: int = DEFAULT_PRESSURE
        self.plate_pressure_reset: bool = False

    def _apply_brush(self, hex: Hexagon):
        if self.brush == BrushType.PIT:
            self.add_pit(hex)
        elif self.brush == BrushType.WALL:
            self.add_wall(hex)
        elif self.brush == BrushType.SPAWN:
            self.add_spawn(hex)
        elif self.brush == BrushType.DEATH_RADIUS_TRAP:
            self.add_plate(
                Plate(
                    hex.cube,
                    plate_type=PlateType.DEATH_RADIUS_TRAP,
                    pressure=self.plate_pressure,
                    pressure_reset=self.plate_pressure_reset,
                    targets=self.selected_tiles,
                )
            )
        elif self.brush == BrushType.PIT_TRAP:
            self.add_plate(
                Plate(
                    hex.cube,
                    plate_type=PlateType.PIT_TRAP,
                    pressure=self.plate_pressure,
                    pressure_reset=self.plate_pressure_reset,
                    targets=self.selected_tiles
                    if len(self.selected_tiles) > 0
                    else {hex},
                )
            )
        elif self.brush == BrushType.WALL_TRAP:
            self.add_plate(
                Plate(
                    hex.cube,
                    plate_type=PlateType.WALL_TRAP,
                    pressure=self.plate_pressure,
                    pressure_reset=self.plate_pressure_reset,
                    targets=self.selected_tiles,
                )
            )
        else:
            raise ValueError(f"Unknown brush type: {self.brush}")
        self._clear_selected()

    def _set_brush(self, set_as: BrushType):
        self.brush = set_as

    def _toggle_brush(self):
        brushes = list(BrushType)
        if self.brush not in brushes:
            self._set_brush(brushes[0])
            return
        idx = brushes.index(self.brush)
        idx = (idx + 1) % len(brushes)
        self._set_brush(brushes[idx])

    def _toggle_selected(self, hex: Hexagon):
        if hex in self.selected_tiles:
            self.selected_tiles.remove(hex)
        else:
            self.selected_tiles.add(hex)
        self._reset_selected_vfx()

    def _clear_selected(self):
        self.selected_tiles = set()
        self._reset_selected_vfx()

    def _reset_selected_vfx(self):
        self.clear_vfx()
        for h in self.selected_tiles:
            self.add_vfx("highlight", h)

    def _add_pressure(self, delta=1):
        self.plate_pressure += delta
        self.plate_pressure = min(-1, max(MIN_PRESSURE, self.plate_pressure))

    def _toggle_pressure_reset(self, set_as: Optional[bool] = None):
        if set_as is None:
            set_as = not self.plate_pressure_reset
        self.plate_pressure_reset = set_as

    def _toggle_coords(self):
        self.show_coords = not self.show_coords

    def clear_all(self):
        """Overrides parent method to clear selected tiles as well."""
        super().clear_all()
        self._clear_selected()

    # GUI API
    def update(self):
        """Called by the GUI every frame."""
        assert self.state.round_count == 0
        assert self.state.end_of_round
        if self.state.game_over:
            self.first_round_state = self.state.copy()
            self.first_round_state.death_radius -= 1
        else:
            self.first_round_state = self.state.increment_round()

    def get_controls(self) -> ControlMenu:
        """Returns `botroyale.api.gui.Control`s for map editing tools.

        Overrides: `botroyale.api.gui.BattleAPI.get_controls`.
        """
        return {
            "Editor": [
                Control(
                    "Increase death radius",
                    lambda: self.increment_death_radius(1),
                    "+ =",
                ),
                Control(
                    "Decrease death radius",
                    lambda: self.increment_death_radius(-1),
                    "+ -",
                ),
                Control("Clear selected", self._clear_selected, "^ c"),
                Control("Clear all", self.clear_all, "^+ c"),
                Control("Save", self.save, "^+ s"),
                Control("Load", self.load, "^+ l"),
            ],
            "Brush": [
                *[
                    Control(
                        bt.name.capitalize(),
                        lambda bt=bt: self._set_brush(bt),
                        BRUSH_HOTKEYS[i],
                    )
                    for i, bt in enumerate(BrushType)
                ],
                Control("Toggle brush", lambda: self._toggle_brush(), "tab"),
                Control("Add pressure", lambda: self._add_pressure(), "r"),
                Control("Reduce pressure", lambda: self._add_pressure(-1), "f"),
                Control(
                    "Toggle pressure reset", lambda: self._toggle_pressure_reset(), "v"
                ),
            ],
            "Mirror Mode": [
                Control("Mirror off", lambda: self.set_mirror_mode(1), "1"),
                Control("Mirror 2", lambda: self.set_mirror_mode(2), "2"),
                Control("Mirror 3", lambda: self.set_mirror_mode(3), "3"),
                Control("Mirror 6", lambda: self.set_mirror_mode(6), "4"),
            ],
            "Debug": [
                Control("Map coordinates", self._toggle_coords, "^+ d"),
            ],
        }

    def get_info_panel_text(self) -> str:
        """Multiline summary of the map at the current state.

        Overrides: `botroyale.api.gui.BattleAPI.get_info_panel_text`.
        """
        valid_str = "Valid map"
        if not self.check_valid():
            valid_str = "INVALID MAP"
        return "\n".join(
            [
                "___ Map Editor ___",
                f"{valid_str}¹",
                "\n",
                f"Brush:           {self.brush.name.capitalize()}  × "
                f"{self.mirror_mode} mirrors",
                f"Selected tiles:  {len(self.selected_tiles)}",
                "\n",
                f"Plate pressure:  {self.plate_pressure}",
                f"Pressure reset:  {self.plate_pressure_reset}",
                "\n",
                f"Death radius²    {self.state.death_radius-1}",
                f"Map size         {self.state.death_radius-2}",
                f"Spawns (units)   {len(self.state.positions)}",
                f"Pits             {len(self.state.pits)}",
                f"Walls            {len(self.state.walls)}",
                f"Plates           {len(self.state.plates)}",
                "\n",
                '¹ "Invalid" usually indicates that a spawn',
                "       is unfair. Can still be exported.",
                "² Death radius is shown as on round 1",
                "\n",
                "___ Quick Help ___",
                "",
                self.HELP_STR,
            ]
        )

    def get_info_panel_color(self) -> tuple[float, float, float]:
        """Color based on the current `MapCreator.brush`.

        Overrides: `botroyale.api.gui.BattleAPI.get_info_panel_color`.
        """
        color = BRUSH_COLORS[self.brush]
        if hasattr(PlateType, self.brush.name):
            intensity = 1 / (-self.plate_pressure + 1)
            color = tuple(c * intensity for c in color)
        return color

    def get_gui_tile_info(self, hex: Hexagon) -> Tile:
        """Returns a `botroyale.api.gui.Tile` for *hex*.

        Overrides: `botroyale.api.gui.BattleAPI.get_gui_tile_info`.
        """
        state = self.first_round_state
        tile, bg = get_tile_info(hex, state)
        sprite, color, text = get_tile_info_unit(hex, state)

        if self.show_coords:
            text = f"{hex.x},{hex.y}"

        return Tile(
            tile=tile,
            bg=bg,
            color=color,
            sprite=sprite,
            text=text,
        )

    def get_map_size_hint(self) -> float:
        """Tracks the `botroyale.logic.state.State.death_radius`.

        The death radius is subtracted by one (and a bit) to "skip" the 0th
        round and show it as it is in round 1.

        Overrides: `botroyale.api.gui.BattleAPI.get_map_size_hint`.
        """
        return self.state.death_radius - 1.5

    def handle_hex_click(self, hex: Hexagon, button: str, mods: str):
        """Handles a tile being clicked on in the tilemap.

        Overrides: `botroyale.api.gui.BattleAPI.handle_hex_click`.
        """
        # Normal click: modify
        if mods == "":
            if button == "left":
                self._apply_brush(hex)
            elif button == "right":
                self.clear_contents(hex, mirrored=True)
        # Control click: info
        elif mods == "^":
            if button == "left":
                # Show targets of a plate
                p = self.state.get_plate(hex)
                if p:
                    for t in p.targets:
                        self.add_vfx("highlight", t, steps=1)
        # Shift click: select
        elif mods == "+":
            if button == "left":
                self._toggle_selected(hex)
