"""InputManager.

Characters representing the modifier keys:

- `^` Control
- `!` Alt
- `+` Shift
- `#` Super
"""
from typing import Callable, Union, TypeVar
from collections import defaultdict
from dataclasses import dataclass, field
from .. import kivy as kv
from ..util import (
    XWidget,
    restart_script,
    _ping,
    _pong,
)

KEYCODE_TEXT = {v: k for k, v in kv.Keyboard.keycodes.items()}
KeysFormat = TypeVar("KeysFormat", bound=str)
"""A type alias for a string formatted as either: `f'{modifiers} {key}'` or `key`."""
MODIFIER_SORT = "^!+#"
MOD2KEY = {
    "ctrl": "^",
    "alt-gr": "!",
    "alt": "!",
    "shift": "+",
    "super": "#",
    "meta": "#",
    "control": "^",
    "lctrl": "^",
    "rctrl": "^",
    "lalt": "!",
    "ralt": "!",
    "lshift": "+",
    "rshift": "+",
    "numlock": "",
    "capslock": "",
}
KEY2MOD = {
    "^": "ctrl",
    "!": "alt",
    "+": "shift",
    "#": "super",
}


@dataclass(frozen=True, eq=True)
class KeyControl:
    """Represents a control for the `XInputManager`."""

    name: str
    """The name of this control (to be used for filtering)."""
    callback: Callable[[], None] = field(compare=False, repr=False)
    """Function to call when this control is invoked."""
    keys: list[KeysFormat] = field(compare=False)
    """The keybind of this control."""
    allow_repeat: bool = field(default=False, compare=False, repr=True)
    """Allow this control to be repeatedly invoked while holding down the keys."""


def _format_keys(
    modifiers: list[str],
    key_name: str,
    honor_numlock: bool = True,
) -> KeysFormat:
    """Convert a combination of keys to a standard string format."""
    if (
        honor_numlock
        and "numlock" in modifiers
        and key_name.startswith("numpad")
        and len(key_name) == 7
    ):
        key_name = key_name[-1]
    # Remove duplicate modifiers
    modifiers = set(MOD2KEY[mod] for mod in modifiers)
    modifiers -= {""}
    # Remove modifier if it is the main key being pressed
    # e.g. when key_name == "lctrl", "ctrl" will be in modifiers
    if key_name in MOD2KEY:
        modifiers -= {MOD2KEY[key_name]}
    # No space required if no modifiers
    if len(modifiers) == 0:
        return key_name
    # Order of modifiers should be consistent
    sorted_modifiers = sorted(modifiers, key=lambda x: MODIFIER_SORT.index(x))
    # Return the KeysFormat
    mod_str = "".join(sorted_modifiers)
    return f"{mod_str} {key_name}"


def humanize_keys(keys: KeysFormat) -> str:
    """Return a more human-readable string from a KeysFormat."""
    mods, key = keys.split(" ") if " " in keys else ([], keys)
    dstr = [KEY2MOD[mod] for mod in mods]
    dstr.append(key)
    return " + ".join(dstr)


class XInputManager(XWidget, kv.Widget):
    """See module documentation for details."""

    # Set negative min_cooldown to disable repeated invoking
    active = kv.BooleanProperty(True)
    """If the InputManager is active."""
    log_press = kv.BooleanProperty(False)
    """If key presses should be logged."""
    log_release = kv.BooleanProperty(False)
    """If key released should be logged."""
    log_callback = kv.BooleanProperty(False)
    """If invocations should be logged."""
    pressed = kv.StringProperty(" ")
    """Last keys that were pressed."""
    released = kv.StringProperty(" ")
    """Last keys that were released."""
    min_cooldown = kv.NumericProperty(0)
    """Minimum cooldown in milliseconds between invocations.

    This will ultimately be limited by the system's "repeat rate" of the
    keyboard. Setting a negative value will disable repeating.
    """
    honor_numlock = kv.BooleanProperty(True)
    """Consider numpad keys as different than number keys when numlock is disabled."""
    allow_overwrite = kv.BooleanProperty(False)
    """Allow overwriting existing controls."""
    humanize = humanize_keys
    """Alias for `humanize_keys`."""

    def __init__(
        self,
        name: str = "Unnamed",
        default_controls: bool = True,
        logger: Callable[[str], None] = print,
        **kwargs,
    ):
        """Class for managing key press bindings and hotkeys.

        Args:
            name: Arbitrary name of the object. Used for debugging.
            default_controls: If True, will call `XInputManager.register_defaults`.
            logger: Function to be used for logging.
        """
        self.name = name
        self.controls = {}
        self.control_keys = defaultdict(set)
        super().__init__(**kwargs)
        self.__last_down_ping = _ping() - self.min_cooldown
        self.logger = logger
        kv.Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)
        if default_controls:
            self.register_defaults()

    # Control management
    def register(
        self,
        name: str,
        callback: Callable[[], None],
        keys: Union[KeysFormat, list[KeysFormat]],
        allow_repeat: bool = False,
    ):
        """Register or modify a control.

        Args:
            name: Control name.
            callback: Function to call when the control is invoked.
            keys: Keypresses that will invoke the control.
            allow_repeat: Allow this control to be repeatedly invoked if the
                keys have not been released.
        """
        keys = [keys] if isinstance(keys, str) else keys
        kc = KeyControl(name, callback, keys, allow_repeat)
        if kc.name in self.controls:
            if not self.allow_overwrite:
                raise ValueError(
                    f"{kc.name} already exists, enable allow_overwrite "
                    "or use a unique name."
                )
            old_kc = self.controls[kc.name]
            self.logger(f"Replacing {old_kc} -> {kc}")
            self._remove_kc(old_kc)
        else:
            self.logger(f"Registering {kc}")
        self._register_kc(kc)

    def remove(self, name: str):
        """Remove a control by *name*."""
        if name not in self.controls:
            self.logger(f"{self} cannot remove non-existant control: {name}")
            return
        kc = self.controls[name]
        self.logger(f"Removing {kc}")
        self._remove_kc(kc)

    def remove_all(self):
        """Remove all controls."""
        self.controls = {}
        self.control_keys = defaultdict(set)

    def _register_kc(self, kc: KeyControl):
        self.controls[kc.name] = kc
        for kf in kc.keys:
            self.control_keys[kf].add(kc)

    def _remove_kc(self, kc: KeyControl):
        for kf in kc.keys:
            self.control_keys[kf].remove(kc)
        del self.controls[kc.name]

    def register_defaults(self):
        """Register default controls (quit and restart)."""
        self.register("app.quit", lambda: quit(), "^+ q")
        self.register("app.restart", restart_script, "^+ w")

    # Properties
    @property
    def humanized(self) -> str:
        """Return a more human-readable string of last pressed keys."""
        return humanize_keys(self.pressed)

    @property
    def on_cooldown(self) -> bool:
        """Check if we are on cooldown for repeating a key down event."""
        if self.min_cooldown < 0:
            return True
        return _pong(self.__last_down_ping) < self.min_cooldown

    @property
    def pressed_key(self) -> str:
        """The last pressed key."""
        return self.pressed.split(" ")[1] if " " in self.pressed else self.pressed

    @property
    def pressed_mods(self) -> str:
        """The last pressed modifiers."""
        kf = self.pressed
        if " " in kf:
            mods, key = kf.split(" ")
            mods = list(mods)
        else:
            mods, key = [], kf
        if key in MOD2KEY:
            extra_mod = MOD2KEY[key]
            if extra_mod not in mods:
                mods.append(extra_mod)
        sorted_mods = sorted(mods, key=lambda x: MODIFIER_SORT.index(x))
        return "".join(sorted_mods)

    def __repr__(self):
        """Repr."""
        cooldown = (
            f" {self.min_cooldown}ms cd" if self.min_cooldown >= 0 else " no repeat"
        )
        active = "" if self.active else " INACTIVE"
        return (
            f"<{self.name} InputManager, {len(self.controls)} controls "
            f"on {len(self.control_keys)} hotkeys{cooldown} {active}>"
        )

    @property
    def _debug_str(self):
        strs = [
            f"{self}",
            "Keys:",
        ]
        for kf, kcs in self.control_keys.items():
            strs.extend(f"{kf:>15} : {kc}" for kc in kcs)
        strs.extend(
            [
                "Controls:",
                *(f"  {kc}" for kc in self.controls.values()),
            ]
        )
        return "\n".join(strs)

    # Kivy key press management
    def _on_key_down(
        self,
        window,
        key: int,
        scancode: int,
        codepoint: str,
        modifiers: list[str],
    ):
        if not self.active or self._app_blocked:
            return
        key_name = KEYCODE_TEXT.get(key, "")
        kf = _format_keys(modifiers, key_name, self.honor_numlock)
        is_repeat = kf == self.pressed
        if is_repeat and self.on_cooldown:
            return
        self.__last_down_ping = _ping()
        if not is_repeat and self.log_press:
            self.logger(f"Pressed:  |{kf}| {self}")
        if kf in self.control_keys:
            for kc in self.control_keys[kf]:
                if is_repeat and not kc.allow_repeat:
                    continue
                self._invoke_kc(kc)
        self.pressed = kf

    def _on_key_up(self, window, key: int, scancode: int):
        self.released = self.pressed
        self.pressed = " "
        if not self.active or self._app_blocked:
            return
        if self.log_release:
            key_name = KEYCODE_TEXT.get(key, "")
            self.logger(f"Released: |{key_name}| {self}")

    def _invoke_kc(self, kc: KeyControl):
        callback = kc.callback
        if self.log_callback:
            self.logger(f"Invoking {kc} {callback=}")
        callback()

    @property
    def _app_blocked(self):
        if self.app is not None:
            return self.app.block_input
        return False
