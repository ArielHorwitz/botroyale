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
    Mapping,
    Any,
    Callable,
    get_args as get_type_args,
)
from collections import deque
from dataclasses import dataclass, asdict as dataclass_asdict
from botroyale.util.hexagon import Hexagon, ORIGIN
from botroyale.api.logging import logger as glogger


@dataclass
class Control:
    """Represents a control the user may use to invoke a callback.

    Used for buttons and hotkeys. The hotkey is a string with a simple format:

    `f"{key}"` or `f"{mods} {key}"`

    Where *key* is the keyboard character and *mods* is a string with a
    combination of `"^"` for control, `"+"` for shift, `"!"` for alt, and
    `"#"` for super (winkey). To inspect key presses, enable hotkey logging in
    settings.

    E.g.

    `"g"` - g key

    `"spacebar"` - Spacebar key

    `"f1"` - F1 key

    `"^+ a"` - Control + Shift + a
    """

    category: str
    """Name of the category of the control (e.g. "App")."""
    label: str
    """Name of the control function (e.g. "Start new battle")."""
    callback: Callable[[], None]
    """Callback when the control is invoked."""
    hotkeys: Optional[Union[str, list[str]]] = None
    """Optionally specify to allow invoking this control with hotkeys."""

    def __post_init__(self):
        """Dataclass post init."""
        if self.hotkeys is None:
            self.hotkeys = []
        if not isinstance(self.hotkeys, list):
            assert isinstance(self.hotkeys, str)
            self.hotkeys = [self.hotkeys]


InputWidgetType = Literal[
    "spacer",
    "toggle",
    "text",
    "select",
    "slider",
    "divider",
]
INPUT_WIDGET_TYPES = get_type_args(InputWidgetType)
WidgetValues = Mapping[str, Any]
"""A dictionary that maps an `InputWidget.sendto` name to a value."""

MenuUpdate = Literal[
    "nothing",
    "values",
    "widgets",
]
MENU_UPDATE_RESPONSES = get_type_args(MenuUpdate)


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
    type: InputWidgetType
    """Type of widget."""
    default: Any = None
    """Starting value of the widget (default depends on *type*)."""
    sendto: Optional[str] = None
    """
    Identifying name for the widget (default is to use *label*).

    This is the widget's key in the `WidgetValues` dictionary.
    """
    options: Optional[Sequence[str]] = None
    """List of strings, required only by `select` widgets."""
    slider_range: tuple[float, float, float] = (0, 100, 1)
    """The (min, max, resolution) for slider. Default: (0, 100, 1)."""

    def __post_init__(self):
        """Initialize the dataclass."""
        assert self.type in INPUT_WIDGET_TYPES

        if self.type == "select":
            assert self.options

        if self.type == "slider":
            self.slider_range = tuple(self.slider_range)
            assert len(self.slider_range) == 3
            assert all(
                isinstance(n, int) or isinstance(n, float) for n in self.slider_range
            )

        if self.sendto is None:
            self.sendto = self.label

        if self.default is None:
            if self.type == "toggle":
                self.default = False
            elif self.type == "text":
                self.default = ""
            elif self.type in {"spacer", "divider"}:
                self.default = self.label
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
    start_step: float
    """In-game time before which the vfx expires."""
    expire_step: float
    """In-game time after which the vfx expires."""
    expire_seconds: float
    """Real-time seconds after which the vfx expires."""

    def asdict(self):
        """Equivalent to passing *self* to `dataclasses.dataclass_asdict`."""
        return dataclass_asdict(self)


@dataclass
class Overlay:
    """Represents a function that should be called while displaying an overlay."""

    func: Callable[[], None]
    """Function to be called."""
    text: str = "Loading..."
    """Text to display on the overlay."""
    after: Optional[Callable[[], None]] = None
    """Function to call when completed."""


class BattleAPI:
    """Base class for the API between the GUI's main menu and the logic.

    Used to draw and control the battle. Battles are created using the
    `GameAPI.get_new_battle` method, which returns a `BattleAPI` object.
    """

    def __init__(self):
        """Initialize the class."""
        self.__overlay_queue = deque()
        self.__vfx_queue = deque()
        self.__clear_vfx_flag = False

    # GUI API
    def update(self):
        """Called continuously (every frame) by the GUI."""
        pass

    def get_time(self) -> Union[int, float]:
        """In-game time. Used by the GUI to determine when vfx need to expire."""
        return 0

    def get_controls(self) -> list[Control]:
        """Returns a list of Controls for buttons and hotkeys in GUI."""
        return [
            Control("Battle", "Foo", lambda: glogger("foo"), "f"),
            Control("Battle", "Bar", lambda: glogger("bar"), ["b", "^ b"]),
        ]

    def set_visible(self, visible: bool):
        """Called when the GUI is shown or hidden from view."""
        pass

    def add_overlay(self, *args, **kwargs):
        """Add an Overlay to the queue."""
        self.__overlay_queue.append(Overlay(*args, **kwargs))

    def flush_overlays(self) -> list[Overlay]:
        """Clears and returns the overlays from queue."""
        r = list(self.__overlay_queue)
        self.__overlay_queue = deque()
        return r

    # Info panel
    def get_info_panel_text(self) -> str:
        """Multiline string to display in the info panel.

        Used for displaying a summary of the current game state.
        """
        return "Panel text placeholder"

    def get_info_panel_color(self) -> str:
        """Color scheme name of the info panel in GUI.

        Return value must be a name in settings "gui.colors".
        """
        return "default"

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

    def get_new_battle(self, menu_values: WidgetValues) -> Union[BattleAPI, None]:
        """Called by the GUI when the user requests to start a new battle.

        Args:
            menu_values: A WidgetValues dictionary. See
                `GameAPI.get_menu_widgets` and `InputWidget`.

        Returns:
            `BattleAPI` (or None if we decide not to start a new battle).
        """
        return BattleAPI()

    def get_new_battle_text(self) -> str:
        """String to be displayed in the button to start a new battle."""
        return "Start new battle"

    def get_info_panel_text(self) -> str:
        """String to be displayed in the menu info panel."""
        return "Main Menu"

    def get_menu_widgets(self) -> list[InputWidget]:
        """Returns a list of InputWidgets to populate the main menu.

        The values of these widgets are passed to get_new_battle.
        """
        return []

    def get_controls(self) -> list[Control]:
        """Returns a list of `Control` for buttons and hotkeys in GUI."""
        return []

    def handle_menu_widget(
        self,
        widgets: list[str],
        menu_values: WidgetValues,
    ) -> MenuUpdate:
        """Called when the user interacts with InputWidgets in the main menu.

        The return value of `MenuUpdate` indicates what should be updated in the
        menu. If `"nothing"` is returned, nothing will happen. Otherwise, the
        menu will be updated.

        ### Updating the menu
        When updating the menu, `GameAPI.get_menu_widgets` will be called:

        - If `"values"` is returned, only widget values will be udpated. The
            *default* of the InputWidget will be used as the value.
        - If `"widgets"` is returned, the existing widgets will be removed and
            the menu will be recreated.

        Other methods may be called when updating the menu.

        Args:
            widgets: The `sendto` names of the widgets that were interacted with.
                Will be an empty list if the user requested to refresh the menu.
            menu_values: A WidgetValues dictionary of all widgets and their values.

        Returns:
            What to update in the menu.
        """
        return "nothing"
