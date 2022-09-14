"""Maps (initial states for battle).

It is recommended to use `botroyale.logic.maps.get_map_state` in order to "initialize" a
`botroyale.logic.state.State` object.
"""
from typing import Optional
import json
from itertools import chain
from pathlib import Path
from botroyale.util import PACKAGE_DIR
from botroyale.util.file import file_load, file_dump, get_usr_dir
from botroyale.util import settings
from botroyale.util.hexagon import Hexagon, Hex, ORIGIN
from botroyale.logic.state import State
from botroyale.logic.plate import Plate


BUILTIN_MAP_DIR = PACKAGE_DIR / "logic" / "maps"
"""Directory where builtin maps are stored on disk."""
USR_MAP_DIR = get_usr_dir("maps")
"""Directory where custom user maps are stored on disk."""
if not USR_MAP_DIR.is_dir():
    USR_MAP_DIR.mkdir(parents=True, exist_ok=True)


def _find_maps(use_custom: bool = True) -> dict[str, Path]:
    """Return list of map names and their paths as found on disk.

    Setting *use_custom* to True will include the "maps" usr dir. Custom user
    maps override builtin maps.
    """
    map_files = {}
    path_iter = BUILTIN_MAP_DIR.iterdir()
    path_iter = chain(USR_MAP_DIR.iterdir(), path_iter)
    for file in path_iter:
        if not len(file.suffixes) == 1 or file.suffix != ".json":
            continue
        if file.stem == "custom" and not use_custom:
            continue
        if file.stem in map_files:
            continue
        map_files[file.stem] = file
    return map_files


DEFAULT_STATE: State = State(death_radius=12)
"""A `botroyale.logic.state.State` object representing a default, "empty" map.

Should be copied (`botroyale.logic.state.State.copy`) before use.
"""
MAPS: tuple[str, ...] = tuple(sorted(_find_maps().keys()))
"""Tuple of available map names.

Searches the "maps" dir from `botroyale.util.file.get_usr_dir` and builtin maps.
"""
DEFAULT_MAP_NAME: str = settings.get("battle.default_map")
"""Default map name as configured in settings."""
assert DEFAULT_MAP_NAME in MAPS


def get_map_state(map_name: Optional[str] = None) -> State:
    """Return the state based on the map by name.

    Passing None to *map_name* will use `DEFAULT_MAP_NAME`.
    """
    if map_name is None:
        map_name = DEFAULT_MAP_NAME
    return _load_map(map_name)


def _load_map(map_name: Optional[str] = None, use_default: bool = True) -> State:
    """Returns a state based on the map saved on disk by name.

    The default state will be returned if `map_name` is None or if `use_default`
    is true and the map wasn't found.
    """
    if map_name is None:
        return DEFAULT_STATE.copy()
    map_files = _find_maps()
    if map_name not in map_files:
        if use_default:
            print(f"{map_name=} not found in {map_files=}")
            return DEFAULT_STATE.copy()
        raise FileNotFoundError(f'Could not find map: "{map_name}"')
    data = json.loads(file_load(map_files[map_name]))
    return State(
        death_radius=data["death_radius"],
        positions=[Hex(x, y) for x, y in data["positions"]],
        pits={Hex(x, y) for x, y in data["pits"]},
        walls={Hex(x, y) for x, y in data["walls"]},
        plates={Plate.from_exported(p) for p in data.get("plates", [])},
    )


def _save_map(map_name: str, state: State, allow_overwrite: bool = True):
    """Saves the map based on the current state to disk by name.

    The *allow_overwrite* argument will allow overwriting an existing file.
    """
    data = {
        "death_radius": state.death_radius,
        "positions": [p.xy for p in state.positions],
        "pits": [p.xy for p in state.pits],
        "walls": [w.xy for w in state.walls],
        "plates": [p.export() for p in state.plates],
    }
    map_file = USR_MAP_DIR / f"{map_name}.json"
    if not allow_overwrite and map_file.is_file():
        raise FileExistsError(f"Not allowed to overwrite saved map: {map_file}")
    file_dump(map_file, json.dumps(data))


class MapCreator:
    """The MapCreator object is used to interactively create maps.

    Most use cases do not require the MapCreator, see the `get_map_state`
    function.
    """

    def __init__(
        self,
        initial_state: Optional[State] = None,
        mirror_mode: int = 1,
    ):
        """Initialize the class."""
        self.set_mirror_mode(mirror_mode)
        if initial_state is None:
            initial_state = _load_map()
        self.state = initial_state

    def set_mirror_mode(self, mode: int = 1):
        """Sets the mirror mode. Must be one of: 1, 2, 3, 6."""
        assert mode in (1, 2, 3, 6)
        self.mirror_mode = mode
        self.mirror_rot = int(6 / mode)

    def save(self, file_name: Optional[str] = None):
        """Save the map to file."""
        if file_name is None:
            file_name = "custom"
        _save_map(file_name, self.state)

    def load(self, file_name: Optional[str] = None):
        """Load the map from file."""
        if file_name is None:
            file_name = "custom"
        self.state = _load_map(file_name)

    def increment_death_radius(self, delta: int):
        """Increase the death radius by a delta. Can be negative.

        Will not set a value lower than 3.
        """
        new_val = self.state.death_radius + delta
        self.state.death_radius = max(3, new_val)

    def add_spawn(self, hex: Hexagon):
        """Clear contents and add a spawn at hex."""
        for h in self._get_mirrored(hex):
            self.clear_contents(h)
            self.state.positions.append(h)
        self._refresh_state()

    def add_pit(self, hex: Hexagon):
        """Clear contents and add a pit at hex."""
        for h in self._get_mirrored(hex):
            self.clear_contents(h)
            self.state.pits.add(h)

    def add_wall(self, hex: Hexagon):
        """Clear contents and add a wall at hex."""
        for h in self._get_mirrored(hex):
            self.clear_contents(h)
            self.state.walls.add(h)

    def add_plate(self, plate: Plate):
        """Clear contents and add a plate at hex."""
        assert isinstance(plate, Plate)
        for p in self._get_mirrored_plate(plate):
            self.clear_contents(p)
            self.state.plates.add(p)

    def clear_contents(self, hex: Hexagon, mirrored: bool = False):
        """Clear the contents of hex: clears spawns, walls, and pits.

        Passing True to the *mirrored* argument will clear mirrored hexes based
        on the mirror mode.
        """
        hexes = [hex]
        if mirrored:
            hexes = self._get_mirrored(hex)
        for h in hexes:
            if h in self.state.positions:
                self.state.positions.remove(h)
                self._refresh_state()
            if h in self.state.pits:
                self.state.pits.remove(h)
            if h in self.state.walls:
                self.state.walls.remove(h)
            if h in self.state.plates:
                self.state.plates.remove(h)

    def clear_all(self):
        """Resets the map to the default state."""
        self.state = DEFAULT_STATE.copy()

    def check_valid(self, check_spawn: bool = True, check_overlap: bool = True) -> bool:
        """Checks that the map is valid.

        Args:
            check_spawn: Assert that spawns won't instantly die.
            check_overlap: Assert that walls and pits don't overlap.
        """
        if self.state.death_radius < 3:
            return False
        if set(self.state.positions) & self.state.walls:
            return False
        if len(self.state.positions) == 0:
            return False
        if check_spawn:
            if set(self.state.positions) & self.state.pits:
                return False
            for spawn in self.state.positions:
                if spawn.get_distance(ORIGIN) >= self.state.death_radius - 1:
                    return False
        if check_overlap:
            if self.state.pits & self.state.walls:
                return False
        return True

    def _get_mirrored(self, hex: Hexagon) -> list[Hexagon]:
        """Returns a list of hexes that are mirrors of hex, based on the mirror mode."""
        return [hex.rotate(-self.mirror_rot * rot) for rot in range(self.mirror_mode)]

    def _get_mirrored_plate(self, plate: Plate) -> list[Plate]:
        """Returns a list of plates mirrors, based on the mirror mode."""
        new_plates = []
        for r in range(self.mirror_mode):
            rot = -self.mirror_rot * r
            h = plate.rotate(rot)
            p = plate.with_new_hex(h)
            new_targets = {t.rotate(rot) for t in plate.targets}
            p.targets = new_targets
            new_plates.append(p)
        return new_plates

    def _refresh_state(self):
        """Recreates the state.

        This is used to refresh the state when adding or removing spawns.
        """
        self.state = State(
            death_radius=self.state.death_radius,
            positions=self.state.positions,
            pits=self.state.pits,
            walls=self.state.walls,
            plates=self.state.plates,
        )
