"""A collection of classes used by the GUI.

All classes in this module are the object types that the GUI will request when
calling certain methods of `botroyale.api.gui.GameAPI` and
`botroyale.api.gui.BattleAPI`.
"""
from typing import (
    Optional,
    Union,
    Literal,
    Sequence,
    NamedTuple,
    Any,
    Callable,
)
from collections import deque
from itertools import chain
from dataclasses import dataclass, asdict as dataclass_asdict
from botroyale.util.hexagon import Hexagon, ORIGIN
from botroyale.api.logging import logger as glogger


PALETTE = (
    (0.73, 0.97, 0.92),  # bright cyan
    (0.68, 0.85, 0.88),  # dark cyan
    (0.62, 0.63, 0.76),  # purple blue
    (0.24, 0.32, 0.48),  # dark blue
    (0.86, 0.60, 0.35),  # orange
)
PALETTE_BG = tuple(tuple(_ / 2 for _ in c) for c in PALETTE)


class Control(NamedTuple):
    """Represents a control the user may use to invoke a callback.

    Used for buttons and hotkeys.
    """

    label: str
    """Name of the control function (e.g. 'Start new battle')."""
    callback: Callable[[], None]
    """Callback when the control is invoked."""
    hotkey: Optional[str] = None
    """
    Optionally specify to allow invoking this control with the hotkey.

    The hotkey is a string with a simple format:

    `f'{key}'` or `f'{mods} {key}'`

    Where *key* is the keyboard character and *mods* is a string with a
    combination of `'^'` for control, `'+'` for shift, `'!'` for alt, and
    `'#'` for super (winkey).

    E.g.

    `g` - The "g" key

    `spacebar` - The spacebar

    `f1` - The "F1" key

    `^+ a` - Control + Shift + a
    """


# The ControlMenu type is a dictionary of menu names and Control lists
ControlMenu = dict[str, list[Control]]


class ControlMenu_:
    """A type alias for `dict[str, list[Control]]`.

    Represents a dictionary mapping a menu name to a list of `Control` objects
    for that menu.

    See also: `combine_control_menus`.

    ```python
    def get_control_menu() -> ControlMenu:
        return {
            'Actions': [
                Control('Idle', _do_idle, hotkey='^ i'),
                Control('Move', _do_move, hotkey='^ m'),
            ],
            'Cheats': [
                Control('God mode', _cheat_god_mode, hotkey='^+ g'),
                Control('Inifinte AP', _cheat_inf_ap),
            ],
        }
    ```

    .. admonition:: Note
        Documented under `ControlMenu_` instead of `ControlMenu` because assigning
            docstrings to nested type aliases will break the docs.
    """


def combine_control_menus(
    control_menu1: ControlMenu,
    control_menu2: ControlMenu,
) -> ControlMenu:
    """Return a `ControlMenu_` with items from *control_menu1* and *control_menu2*."""
    new_control_menu = {}
    for menu_name, controls in chain(control_menu1.items(), control_menu2.items()):
        if menu_name in new_control_menu:
            new_control_menu[menu_name].extend(controls)
        else:
            new_control_menu[menu_name] = [*controls]
    return new_control_menu


@dataclass
class InputWidget:
    """Represents an input widget in the GUI.

    Widget types include:

    * `spacer` - has a label but no value
    * `toggle` - toggle button (boolean value)
    * `text` - arbitrary text input (string value)
    * `select` - select from list (string value, must supply *options*)
    * `slider` - a slider (float value)
    * `divider` - like `spacer` but creates a new section
    """

    label: str
    """Text to place near the widget."""
    type: Literal["spacer", "toggle", "text", "select", "slider", "divider"]
    """Type of widget."""
    default: Any = None
    """Starting value of the widget (default: None)."""
    sendto: Optional[str] = None
    """
    Name of value (default is to use the same value of *label*).

    This is used by the GUI to map the value of the widget to a key in a
    dictionary. See `GameAPI.get_new_battle`.
    """
    options: Optional[Sequence[str]] = None
    """List of strings, required only by `select` widgets."""

    def __post_init__(self):
        """Initialize the dataclass."""
        if self.type == "select":
            assert self.options

        if self.sendto is None:
            self.sendto = self.label

        if self.default is None:
            if self.type == "toggle":
                self.default = False
            elif self.type == "text":
                self.default = ""
            elif self.type == "select":
                self.default = self.options[0]
            elif self.type == "slider":
                self.default = 0.0


@dataclass
class Tile:
    """Represents how a hex on the tilemap should be drawn."""

    tile: Optional[str] = None
    """Sprite name of the tile itself."""
    bg: tuple[float, float, float] = 0, 0, 0
    """Tile (background) color."""
    sprite: Optional[str] = None
    """Sprite name to draw on top of the tile."""
    color: tuple[float, float, float] = 0.5, 0.5, 0.5
    """Sprite color."""
    text: Optional[str] = None
    """Text to draw on the tile."""


@dataclass
class VFX:
    """Represents a visual effect to be drawn on the tilemap."""

    name: str
    """Name of vfx image (with .png extension)."""
    hex: Hexagon
    """Hex of image center."""
    direction: Hexagon
    """Hex to indicate direction for image rotation."""
    start_step: Union[int, float]
    """In-game time before which the vfx expires."""
    expire_step: Union[int, float]
    """In-game time after which the vfx expires."""
    expire_seconds: float
    """Real-time seconds after which the vfx expires."""

    def asdict(self):
        """Equivalent to passing *self* to `dataclasses.dataclass_asdict`."""
        return dataclass_asdict(self)


class BattleAPI:
    """Base class for the API between the GUI's main menu and the logic.

    Used to draw and control the battle. Battles are created using the
    `GameAPI.get_new_battle` method, which returns a `BattleAPI` object.
    """

    def __init__(self):
        """Initialize the class."""
        self.__vfx_queue = deque()
        self.__clear_vfx_flag = False

    # GUI API
    def update(self):
        """Called continuously (every frame) by the GUI."""
        pass

    def get_time(self) -> Union[int, float]:
        """In-game time. Used by the GUI to determine when vfx need to expire."""
        return 0

    def get_controls(self) -> ControlMenu:
        """Returns a `ControlMenu_` for buttons and hotkeys in GUI."""
        return {
            "Battle": [
                Control("Foo", lambda: glogger("foo"), "f"),
                Control("Bar", lambda: glogger("bar"), "b"),
            ]
        }

    # Info panel
    def get_info_panel_text(self) -> str:
        """Multiline string to display in the info panel.

        Used for displaying a summary of the current game state.
        """
        return "Panel text placeholder"

    def get_info_panel_color(self) -> tuple[float, float, float]:
        """Color of the info panel in GUI."""
        return (0.1, 0.1, 0.1)

    # Tile map
    def get_gui_tile_info(self, hex: Hexagon) -> Tile:
        """Returns a `Tile` representing how to display *hex* in the GUI.

        Called by the GUI for every hex currently visible on the map.
        """
        return Tile(
            bg=(0.1, 0.1, 0.1),
            color=(0.25, 0.25, 0.25),
            sprite="hex",
            text="" if hex != ORIGIN else "Origin",
        )

    def get_map_size_hint(self) -> Union[int, float]:
        """The radius of the map size for the GUI to display."""
        return 5

    def handle_hex_click(self, hex: Hexagon, button: str, mods: str):
        """Called when a tile is clicked on in the GUI.

        Args:
            hex: The hex that was clicked.
            button: One of "left", "right", "middle", "mouse1", "mouse2", etc.
            mods: A string of keyboard modifiers that were pressed when the
                mouse was clicked.

                - `^` control
                - `+` shift
                - `!` alt
                - `#` meta ("win" key)
                - `^+` control + shift
        """
        glogger(f"Clicked {button} on: {hex}")
        if button == "left":
            vfx = "mark-green"
        elif button == "right":
            vfx = "mark-red"
        else:
            vfx = "mark-blue"
        self.add_vfx(vfx, hex)

    # VFX
    def add_vfx(
        self,
        name: str,
        hex: Hexagon,
        direction: Optional[Hexagon] = None,
        steps: int = 1,
        expire_seconds: Optional[float] = None,
    ):
        """Add a single vfx to the queue.

        See `VFX` for details on the arguments.
        """
        assert isinstance(name, str)
        assert isinstance(hex, Hexagon)
        if direction is not None:
            assert isinstance(direction, Hexagon)
        start_step = self.get_time()
        expire_step = start_step + steps
        self.__vfx_queue.append(
            VFX(
                name,
                hex,
                direction,
                start_step,
                expire_step,
                expire_seconds,
            )
        )

    def clear_vfx_flag(self) -> bool:
        """Called by the GUI to check if existing VFX need to be cleared.

        Returns:
            False, unless the flag has been raised (by calling
                `BattleAPI.clear_vfx` with `clear_existing=True`) -- in which
                case this method will drop the flag and return True.
        """
        if self.__clear_vfx_flag:
            self.__clear_vfx_flag = False
            return True
        return False

    def clear_vfx(self, flush_queued: bool = True, clear_existing: bool = True):
        """Clears vfx that are queued or already drawn.

        Args:
            flush_queued: Clears VFX that have been queued but not yet drawn.
            clear_existing: Clears VFX that have already been drawn.
        """
        if flush_queued:
            self.flush_vfx()
        if clear_existing:
            self.__clear_vfx_flag = True

    def flush_vfx(self) -> Sequence[VFX]:
        """Clears and returns the vfx from queue."""
        r = self.__vfx_queue
        self.__vfx_queue = deque()
        return r


class GameAPI:
    """Base class for the API between the GUI's main menu and the logic.

    Used to populate the main menu and start battles. Battles are created using
    the `GameAPI.get_new_battle` method, which returns a `BattleAPI` object.
    """

    def get_new_battle(self, menu_values: dict[str, Any]) -> Union[BattleAPI, None]:
        """Called by the GUI when the user requests to start a new battle.

        Args:
            menu_values: Dictionary that maps each InputWidget's `sendto` name
                to the widget's value. See `GameAPI.get_menu_widgets` and
                `InputWidget`.

        Returns:
            `BattleAPI` (or None if we decide not to start a new battle).
        """
        return BattleAPI()

    def get_info_panel_text(self) -> str:
        """Returns the string to be displayed in the menu info panel."""
        return "Main Menu"

    def get_menu_widgets(self) -> list[InputWidget]:
        """Returns a list of InputWidgets to populate the main menu.

        The values of these widgets are passed to get_new_battle.
        """
        return []

    def get_controls(self) -> ControlMenu:
        """Returns a `ControlMenu_` for buttons and hotkeys in GUI."""
        return {}

    def handle_menu_widget(
        self,
        widgets: list[str],
        menu_values: dict[str, Any],
    ) -> bool:
        """Called by the GUI when the user interacts with `InputWidget`s.

        This will be called without arguments if the user refreshes the menu.

        Args:
            widgets: The `sendto` names of the widgets that were interacted with.
            menu_values: Dictionary that maps each InputWidget's `sendto` name
                to the widget's value. See `GameAPI.get_menu_widgets` and
                `InputWidget`.

        Returns:
            True if we wish the GUI to reset the main menu, by calling
                `GameAPI.get_info_panel_text` and `GameAPI.get_menu_widgets`.
        """
        return False
