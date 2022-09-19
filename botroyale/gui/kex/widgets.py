"""Kex widgets."""
from collections import namedtuple, defaultdict
from typing import Callable, Optional, Any, Literal, Mapping
from functools import partial
from . import kivy as kv
from .util import (
    XWindow,
    XWidget,
    ColorType,
    XColor,
    restart_script,
    consume_args,
    ping,
    pong,
)


logger = print
get_app = kv.App.get_running_app


# LAYOUTS


class XBox(XWidget, kv.BoxLayout):
    pass


class XZBox(XWidget, kv.GridLayout):
    """Behaves like a Box where widgets are drawn in reverse order."""

    def __init__(
        self,
        orientation: Literal["horizontal", "vertical"] = "horizontal",
        **kwargs,
    ):
        """Initialize the class."""
        if orientation == "horizontal":
            kwargs["orientation"] = "rl-tb"
            kwargs["rows"] = 1
        elif orientation == "vertical":
            kwargs["orientation"] = "lr-bt"
            kwargs["cols"] = 1
        else:
            raise ValueError(
                'FlipZIndex orientation must be "horizontal" or "vertical"'
            )
        super().__init__(**kwargs)

    def add(self, *children, **kwargs):
        """Overrides base method to insert correctly."""
        for child in children:
            super().add(child, insert_last=True, **kwargs)
        return child


class XDBox(XWidget, kv.GridLayout):
    """Behaves like a Box that will dynamically resize based on children's height."""

    def __init__(self, cols: int = 1, **kwargs):
        """Initialize the class."""
        super().__init__(cols=cols, **kwargs)

    def add(self, w: XWidget, *args, **kwargs):
        """Overrides XWidget `add` in order to bind to size changes."""
        w.bind(size=self._resize)
        r = super().add(w, *args, **kwargs)
        kv.Clock.schedule_once(self._resize, 0)
        return r

    def remove_widget(self, *a, **k):
        """Overrides base class `remove_widget` in order to resize."""
        super().remove_widget(*a, **k)
        self._resize()

    def _resize(self, *a):
        self.set_size(hx=1, y=sum([c.height for c in self.children]))


class XGrid(XWidget, kv.GridLayout):
    pass


class XStack(XWidget, kv.StackLayout):
    pass


class XRelative(XWidget, kv.RelativeLayout):
    pass


class XAnchor(XWidget, kv.AnchorLayout):
    @classmethod
    def from_widget(
        cls,
        widget: Optional[XWidget] = None,
        color: Optional[XColor] = None,
        source: Optional[str] = None,
        **kwargs,
    ) -> "XAnchor":
        anchor = cls(**kwargs)
        if widget:
            anchor.add(widget)
        if color or source:
            anchor.make_bg(color, source)
        return anchor


class XScroll(XWidget, kv.ScrollView):
    def __init__(
        self,
        view: XWidget,
        scroll_dir: Literal["vertical", "horizontal"] = "vertical",
        scroll_amount: float = 50,
        **kwargs,
    ):
        """Initialize the class.

        Args:
            view: A widget to put in the scroll view.
            scroll_dir: Direction of scroll: "horizontal" or "vertical"
            scroll_amount: Resolution of scroll in pixels.
        """
        super().__init__(**kwargs)
        self.scroll_dir = scroll_dir
        self.scroll_amount = scroll_amount
        self.bar_width = 15
        self.scroll_type = ["bars"]
        self.view = self.add(view)
        self.bind(size=self._on_size, on_touch_down=self._on_touch_down)
        self.view.bind(size=self._on_size)

    @property
    def scroll_dir(self):
        return self.__scroll_dir

    @scroll_dir.setter
    def scroll_dir(self, v):
        self.__scroll_dir = v
        self.do_scroll_x = v == "horizontal"
        self.do_scroll_y = v == "vertical"

    def _on_size(self, *a):
        self.do_scroll_x = (
            self.view.size[0] > self.size[0] and self.scroll_dir == "horizontal"
        )
        self.do_scroll_y = (
            self.view.size[1] > self.size[1] and self.scroll_dir == "vertical"
        )
        if self.size[0] >= self.view.size[0]:
            self.scroll_x = 1
        if self.size[1] >= self.view.size[1]:
            self.scroll_y = 1

    def _on_touch_down(self, w, m):
        if m.button not in {"scrollup", "scrolldown"}:
            return False
        if not any((self.do_scroll_x, self.do_scroll_y)):
            return False
        if not self.collide_point(*m.pos):
            return False

        dir = -1 if m.button == "scrollup" else 1
        pixels_x, pixels_y = self.convert_distance_to_scroll(
            self.scroll_amount,
            self.scroll_amount,
        )
        if self.scroll_dir == "horizontal":
            self.scroll_x = min(1, max(0, self.scroll_x + pixels_x * dir))
        elif self.scroll_dir == "vertical":
            self.scroll_y = min(1, max(0, self.scroll_y + pixels_y * dir))
        return True


class XOverlay(kv.FocusBehavior, XAnchor):
    def __init__(
        self,
        text: str = "",
        alpha: float = 0.5,
        block_input: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.make_bg(XColor(a=alpha))
        self.label = self.add(XLabel(text=text))
        self.label.set_size(x=300, y=75)
        self.label.make_bg(XColor.from_name("red", 0.15))
        if block_input:
            self.bind(
                on_touch_down=self.block_touch,
                on_touch_up=self.block_touch,
                on_touch_move=self.block_touch,
            )
            self.focus = True
            self.keyboard_on_key_down = self.block_touch
            self.keyboard_on_key_up = self.block_touch

    def block_touch(self, *args):
        return True


class XApp(XWidget, kv.App):
    """See module documentation for details."""

    def __init__(
        self,
        escape_exits: bool = False,
        enable_multitouch: bool = False,
        **kwargs,
    ):
        """Initialize the class.

        Args:
            escape_exits: Enable exiting when the escape key is pressed.
            enable_multitouch: Enable multitouch.
        """
        super().__init__(**kwargs)
        self.root = XAnchor()
        XWindow.enable_escape_exit(escape_exits)
        if not enable_multitouch:
            XWindow.disable_multitouch()
            # On my linux machine, this doesn't seem to have an effect, so we
            # manually catch and discard mouse events recognized as multitouch.
            self.root.bind(
                on_touch_down=self._intercept_multitouch,
                on_touch_up=self._intercept_multitouch,
                on_touch_move=self._intercept_multitouch,
            )

    def hook(self, func: Callable[[float], None], fps: float):
        """Hook *func* to be called *fps* times per seconds.

        Args:
            fps: Number of times to be called per second.
            func: The function to call with *delta_time* as a parameter.
        """
        kv.Clock.schedule_once(
            lambda *a: kv.Clock.schedule_interval(func, 1 / fps),
            0,
        )

    def open_settings(self, *args) -> False:
        """Overrides base class method to disable settings."""
        return False

    @property
    def mouse_pos(self):
        """The current position of the mouse."""
        return XWindow.mouse_pos

    @property
    def add(self):
        """Add a widget to the root widget."""
        return self.root.add

    def _intercept_multitouch(self, w, m):
        if not hasattr(m, "multitouch_sim"):
            return False
        if m.multitouch_sim:
            return True
        return False


def frozen_overlay(**overlay_kwargs):
    """Wrapper for creating an overlay for functions that block execution.

    Used for functions that will block code execution for a significant period
    of time, for user feedback. Will create an overlay on the app, call the
    function, and remove the overlay.

    ### Example usage:
    ```python
    @frozen_overlay(text="Sleeping for 2 seconds")
    def do_sleep():
        time.sleep(2)
    ```

    Args:
        overlay_kwargs: Keyword arguments for Overlay.
    """

    def frozen_overlay_inner(func):
        def frozen_overlay_wrapper(*args, **kwargs):
            app = kv.App.get_running_app()
            if app is None:
                func(*args, **kwargs)
                return
            wrapped = partial(func, *args, **kwargs)
            overlay = app.root.add(XOverlay(**overlay_kwargs))
            kv.Clock.schedule_once(
                lambda dt: _call_then_remove(wrapped, overlay),
                0.05,
            )

        return frozen_overlay_wrapper

    return frozen_overlay_inner


def _call_then_remove(func: Callable[[], Any], widget: XWidget):
    func()
    # In order to schedule properly, we must tick or else all the time spent
    # calling func will be counted as time waited for scheduled callback
    kv.Clock.tick()
    kv.Clock.schedule_once(lambda dt: _final_remove(widget), 0.05)


def _final_remove(widget):
    next_focus = widget.get_focus_next()
    if next_focus:
        next_focus.focus = True
    widget.parent.remove_widget(widget)


KeyCalls = namedtuple("KeyCalls", ["keys", "on_press"])


class XInputManager(kv.Widget):
    """Object for handling keyboard presses.

    The characters representing the modifier keys:
    - `^` Control
    - `!` Alt
    - `+` Shift
    - `#` Super

    Todo:
        Refactor, document, type annotate
    """

    MODIFIER_SORT = "^!+#"
    MODIFIERS = {
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
    KEY2MODIFIER = {
        "^": "ctrl",
        "!": "alt",
        "+": "shift",
        "#": "super",
    }

    def __init__(
        self,
        name: str = "Unnamed InputManager",
        active: bool = True,
        app_control_defaults: bool = False,
        logger: Optional[Callable[[str], Any]] = None,
        **kwargs,
    ):
        """Initialize the class.

        Args:
            name: Display name.
            active: Enable the InputManager.
            app_control_defaults: Automatically call
                `InputManager.register_app_control_defaults`.
            logger: Function to call for debug logging.
        """
        self.name = name
        self.active = active
        self.logger = consume_args if logger is None else logger
        self.__all_keys = set()
        self.__actions = defaultdict(lambda: KeyCalls(set(), set()))
        self.__last_key_code = -1
        self.__last_keys_down = ""
        self.__recording_release = None
        self.__recording_press = None
        self.block_repeat = True
        self.repeat_cooldown = 25
        self.__last_key_down_ping = ping() - self.repeat_cooldown
        self._bound_down = None
        self._bound_up = None
        super().__init__(**kwargs)
        self.keyboard = kv.Window.request_keyboard(lambda: None, self)
        if self.active:
            self.activate()
        if app_control_defaults:
            self.register_app_control_defaults()

    @property
    def currently_pressed(self) -> str:
        """The keys that are currently pressed."""
        return self.__last_keys_down

    @property
    def currently_pressed_mods(self) -> str:
        """The modifier keys that are currently pressed."""
        last_keys = self.__last_keys_down
        if " " not in last_keys:
            return ""
        mods = last_keys.split(" ")[0]
        return mods

    @property
    def actions(self):
        """List of registered actions."""
        return list(self.__actions.keys())

    def activate(self):
        """Enable the InputManager."""
        self._bound_down = self.keyboard.fbind("on_key_down", self._on_key_down)
        self._bound_up = self.keyboard.fbind("on_key_up", self._on_key_up)
        self.active = True
        self.logger(f"Activated {self}")

    def deactivate(self):
        """Disable the InputManager."""
        if self._bound_down is not None:
            self.keyboard.unbind_uid("on_key_down", self._bound_down)
        if self._bound_up is not None:
            self.keyboard.unbind_uid("on_key_up", self._bound_up)
        self._bound_down = None
        self._bound_up = None
        self.active = False
        self.logger(f"Deactivated {self}")

    def register(
        self,
        action: str,
        key: Optional[str] = None,
        callback: Optional[Callable[[str], Any]] = None,
    ):
        """Register an action.

        Args:
            action: Name of action.
            key: The key press that will invoke the action.
            callback: The function to be called when invoked. Must take a string
                as an argument (the action name).
        """
        if key is not None:
            self.__actions[action].keys.add(key)
            self._refresh_all_keys()
        if callback is not None:
            self.__actions[action].on_press.add(callback)
        self.logger(f'{self} registering "{action}": {self.__actions[action]}')

    def register_callbacks(self, action: str, callbacks: list[Callable[[str], Any]]):
        """Register callbacks for an action.

        Args:
            action: Name of action.
            callbacks: List of functions to be called when invoked. See
                `InputManager.register.`
        """
        self.__actions[action].on_press.update(callbacks)
        self.logger(f"Input manager registering {action}: {self.__actions[action]}")

    def register_keys(self, action: str, keys: list[str]):
        """Register keys for an action.

        Args:
            action: Name of action.
            keys: List of keys to invoke the action. See `InputManager.register.`
        """
        self.__actions[action].keys.update(keys)
        self.logger(f"Input manager registering {action}: {self.__actions[action]}")
        self._refresh_all_keys()

    def remove_actions(self, actions: list[str]):
        """Unregister a list of actions."""
        for action in actions:
            if action in self.__actions:
                del self.__actions[action]
        self._refresh_all_keys()

    def clear_all(self, app_control_defaults: bool = False):
        """Unregister all actions.

        Will call `InputManager.register_app_control_defaults` if
        *app_control_defaults* is True.
        """
        self.__actions = defaultdict(lambda: KeyCalls(set(), set()))
        self._refresh_all_keys()
        if app_control_defaults:
            self.register_app_control_defaults()

    def record(
        self,
        on_press: Callable[[str], Any] = None,
        on_release: Callable[[str], Any] = None,
    ):
        """Start recording key presses.

        Args:
            on_press: Function to be called to take the key presses as they
                happen.
            on_release: Function to be called to take the key presses when they
                are released.
        """
        self.__recording_release = on_release
        self.__recording_press = on_press

    def stop_record(self):
        """Stop recording keys from `InputManager.record`."""
        self.record()

    @property
    def _debug_summary(self):
        s = []
        for action, kc in self.__actions.items():
            k = ", ".join(_ for _ in kc.keys)
            s.append(f"{action:<20} «{k}» {kc.on_press}")
        return "\n".join(s)

    def register_app_control_defaults(self):
        """Add actions for restarting and quitting the app."""
        self.register(
            "Debug input",
            "^!+ f12",
            lambda *a: self.record(on_release=self.start_debug_record),
        )
        self.register("Restart", "^+ w", lambda *a: restart_script())
        self.register("Quit", "^+ q", lambda *a: quit())

    def _refresh_all_keys(self):
        self.__all_keys = set()
        for action, kc in self.__actions.items():
            self.__all_keys.update(kc.keys)

    def _convert_keys(self, modifiers: str, key_name: str) -> str:
        modifiers = set(self.MODIFIERS[mod] for mod in modifiers)
        if "" in modifiers:
            modifiers.remove("")
        if len(modifiers) == 0:
            return key_name
        sorted_modifiers = sorted(modifiers, key=lambda x: self.MODIFIER_SORT.index(x))
        mod_str = "".join(sorted_modifiers)
        r = f"{mod_str} {key_name}"
        return r

    def _do_calls(self, keys: list[str]):
        all_callbacks = defaultdict(lambda: set())
        for action, kc in self.__actions.items():
            if keys in kc.keys:
                all_callbacks[action].update(kc.on_press)
        for action in all_callbacks:
            self.logger(f"{self} making calls: {all_callbacks[action]}")
            for c in all_callbacks[action]:
                c(action)

    def _on_key_up(self, keyboard, key: str):
        key_code, key_name = key
        if key_code == self.__last_key_code:
            self.__last_key_code = -1
        if self.__recording_release:
            continue_recording = self.__recording_release(self.__last_keys_down)
            if continue_recording is not True:
                self.record(None, None)
            return
        self.__last_keys_down = ""

    def _on_key_down(
        self,
        keyboard,
        key: tuple[str, str],
        key_hex: str,
        modifiers: list[str],
    ):
        key_code, key_name = key
        if key_code == self.__last_key_code:
            if self.block_repeat:
                return
            if pong(self.__last_key_down_ping) < self.repeat_cooldown:
                return
        self.__last_key_down_ping = ping()
        self.__last_key_code = key_code
        self.__last_keys_down = self._convert_keys(modifiers, key_name)
        self.logger(
            f"{self} sees keys pressed: {self.__last_keys_down} "
            f"( {self.humanize_keys(self.__last_keys_down)} )"
        )
        if self.__recording_press:
            stop_recording = self.__recording_press(self.__last_keys_down)
            if stop_recording is True:
                self.record(None, None)
            return
        if self.__last_keys_down in self.__last_keys_down:
            self._do_calls(self.__last_keys_down)

    def start_debug_record(self, *a):
        """Start recording key presses with the logger."""
        m = "InputManager recording input..."
        self.logger(m)
        print(m)
        kv.Clock.schedule_once(lambda *a: self.record(on_release=self._debug_record), 1)

    def _debug_record(self, keys):
        m = f"InputManager recorded input: <{keys}> ({self.humanize_keys(keys)})"
        self.logger(m)
        print(m)

    @classmethod
    def humanize_keys(cls, keys: str) -> str:
        """Return a human-readable repr from an internal repr of keys."""
        if " " not in keys:
            return keys
        mods, key = keys.split(" ")
        ignore_mods = set()
        if key in cls.MODIFIERS:
            if len(mods) == 1:
                return key
            ignore_mods.add(cls.MODIFIERS[key])
        dstr = []
        for mod in mods:
            if mod in ignore_mods:
                continue
            dstr.append(cls.KEY2MODIFIER[mod])
        if key != "":
            dstr.append(key)
        return " + ".join(dstr)

    def __repr__(self):
        """Repr."""
        active_str = "active" if self.active else "inactive"
        return f"<XInputManager {self.name} ({active_str}) {len(self.actions)} actions>"


# BASIC WIDGETS
class XLabel(XWidget, kv.Label):
    def __init__(
        self,
        markup: bool = True,
        halign: str = "center",
        valign: str = "center",
        fixed_width: bool = False,
        **kwargs,
    ):
        super().__init__(markup=markup, halign=halign, valign=valign, **kwargs)
        if fixed_width:
            self.bind(size=self._fix_height, text=self._fix_height)

    def _fix_height(self, *a):
        self.text_size = self.size[0], None
        self.texture_update()
        self.set_size(hx=1, y=self.texture_size[1])

    def on_size(self, *a):
        self.text_size = self.size


class XLabelClick(kv.ButtonBehavior, XLabel):
    pass


class XCheckBox(XWidget, kv.CheckBox):
    def toggle(self, *a):
        self.active = not self.active


class XCheckBoxText(XBox):
    def __init__(self, text: str = "", **kwargs):
        super().__init__(**kwargs)
        self.checkbox = XCheckBox()
        self.label = XLabelClick(
            text=text,
            on_release=self.checkbox.toggle,
        )
        self.checkbox.set_size(y=30)
        checkbox_anchor = XAnchor.from_widget(self.checkbox)
        checkbox_anchor.set_size(x=30)
        self.add(self.label, checkbox_anchor)


class XButton(XWidget, kv.Button):
    def __init__(
        self,
        markup: bool = True,
        halign: str = "center",
        background_color: ColorType = XColor.from_name("blue", 0.5).rgba,
        **kwargs,
    ):
        """Same arguments as kivy Button."""
        super().__init__(markup=markup, halign=halign, **kwargs)
        self.background_color = background_color

    def on_touch_down(self, m):
        """Overrides base class method to only react to left clicks."""
        if m.button != "left":
            return False
        return super().on_touch_down(m)


class XToggleButton(XWidget, kv.ToggleButton):
    def __init__(
        self,
        markup: bool = True,
        **kwargs,
    ):
        """Same arguments as kivy Button."""
        super().__init__(markup=markup, **kwargs)

    def toggle(self):
        """Toggles the active state of the button."""
        self.active = not self.active

    @property
    def active(self):
        """If the button is down."""
        return self.state == "down"

    @active.setter
    def active(self, value: bool):
        self.state = "down" if value else "normal"


class XImageButton(XWidget, kv.ButtonBehavior, kv.Image):
    """Image with ButtonBehavior mixin."""

    pass


class XEntry(XWidget, kv.TextInput):
    """TextInput with sane defaults."""

    def __init__(
        self,
        multiline: bool = False,
        background_color: XColor = XColor(0.2, 0.2, 0.2, 1),
        foreground_color: XColor = XColor(1, 1, 1, 1),
        text_validate_unfocus: bool = True,
        **kwargs,
    ):
        """Initialize the class.

        Args:
            multiline: If should allow multiple lines.
            background_color: Color of the background.
            foreground_color: Color of the foreground.
            text_validate_unfocus: If focus should be removed after validation
                (pressing enter on a single-line widget).
            kwargs: keyword arguments for TextInput.
        """
        super().__init__(
            background_color=background_color.rgba,
            foreground_color=foreground_color.rgba,
            multiline=multiline,
            text_validate_unfocus=text_validate_unfocus,
            **kwargs,
        )
        if not multiline:
            self.set_size(y=35)

    def _on_textinput_focused(self, *args, **kwargs):
        """Overrides base method to select all text when focused."""
        value = args[1]
        super()._on_textinput_focused(*args, **kwargs)
        if value:
            self.select_all()

    def reset_cursor_selection(self, *a):
        """Resets the cursor position and selection."""
        self.cancel_selection()
        self.cursor = 0, 0
        self.scroll_x = 0
        self.scroll_y = 0


class XSlider(XWidget, kv.Slider):
    pass


class XSliderText(XBox):
    def __init__(
        self,
        box_kwargs: Optional[Mapping[str, Any]] = None,
        label_kwargs: Optional[Mapping[str, Any]] = None,
        prefix: str = "",
        rounding: int = 3,
        cursor_size: tuple[int, int] = (25, 25),
        **kwargs,
    ) -> XBox:
        box_kwargs = {} if box_kwargs is None else box_kwargs
        label_kwargs = {} if label_kwargs is None else label_kwargs
        label_kwargs = {"halign": "left"} | label_kwargs
        super().__init__(**box_kwargs)
        self.rounding = rounding
        self.prefix = prefix
        self.label = XLabel(**label_kwargs)
        self.label.set_size(hx=0.2)
        self.slider = XSlider(cursor_size=cursor_size, **kwargs)
        self.add(self.label)
        self.add(self.slider)
        self.slider.bind(value=self._set_text)
        self._set_text(self, self.slider.value)

    def _set_text(self, w, value):
        if isinstance(value, float):
            value = round(value, self.rounding)
        if value == round(value):
            value = int(value)
        self.label.text = str(f"{self.prefix}{value}")


class XSpinner(XWidget, kv.Spinner):
    value = kv.StringProperty("")

    def __init__(self, update_main_text: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.update_main_text = update_main_text
        if update_main_text:
            self.text_autoupdate = True

    def on_select(self, data):
        pass

    def _on_dropdown_select(self, instance, data, *largs):
        if self.update_main_text:
            self.text = data
        self.value = data
        self.is_open = False
        self.on_select(data)


class XDropDown(XWidget, kv.DropDown):
    pass


class XPickColor(XBox):
    color = kv.ObjectProperty(XColor(0.5, 0.5, 0.5, 1))

    def __init__(self, step=0.01, **kwargs):
        super().__init__(orientation="vertical")
        self.set_size(x=300, y=100)
        update_color = self._update_from_sliders
        self.sliders = []
        for i, c in enumerate("RGBA"):
            s = self.add(
                SliderText(
                    range=(0, 1),
                    step=step,
                    value_track=True,
                    value_track_color=XColor(**{c.lower(): 0.75}).rgba,
                    value_track_width="6dp",
                    cursor_size=(0, 0),
                    **kwargs,
                )
            )
            s.slider.bind(value=update_color)
            self.sliders.append(s)
        self.r, self.g, self.b, self.a = self.sliders
        self.set_color(self.color)

    def set_color(self, color: XColor):
        self.r.slider.value = color.r
        self.g.slider.value = color.g
        self.b.slider.value = color.b
        self.a.slider.value = color.a

    def _update_from_sliders(self, *a):
        color = XColor(
            self.r.slider.value,
            self.g.slider.value,
            self.b.slider.value,
            self.a.slider.value,
        )
        is_bright = sum(color.rgb) > 1.5
        for s in self.sliders:
            s.label.color = (0, 0, 0, 1) if is_bright else (1, 1, 1, 1)
        self.make_bg(color)
        self.color = color


class XSelectColor(XLabelClick):
    def __init__(
        self,
        prefix: str = "[u]Color:[/u]\n",
        show_color_text: bool = True,
        **kwargs,
    ):
        self.prefix = prefix
        self.show_color_text = show_color_text
        super().__init__(**kwargs)
        self.picker = XPickColor()
        self.dropdown = XDropDown(auto_width=False, on_dismiss=self.on_color)
        self.dropdown.set_size(*self.picker.size)
        self.dropdown.add(self.picker)
        self.picker.bind(size=lambda w, s: self.dropdown.set_size(*s))
        self.bind(on_release=self.dropdown.open)
        self.on_color()

    def on_color(self, *args):
        color = self.picker.color
        self.make_bg(color)
        text = self.prefix
        if self.show_color_text:
            text += " , ".join(str(round(c, 2)) for c in color.rgba)
        self.text = text


class XScreen(XWidget, kv.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.view = None

    def add(self, *args, **kwargs) -> XWidget:
        self.view = super().add(*args, **kwargs)
        if len(self.children) > 1:
            raise RuntimeError(
                f"Cannot add more than 1 widget to XScreen: {self.children=}"
            )


class XScreenManager(XWidget, kv.ScreenManager):
    def __init__(self, auto_transtion_speed: float = 0.4, **kwargs):
        self.auto_transition = "transition" not in kwargs
        self.auto_transtion_speed = auto_transtion_speed
        super().__init__(**kwargs)

    def add_screen(self, name: str, widget: XWidget) -> XScreen:
        screen = self.add(XScreen(name=name))
        screen.add(widget)
        return screen

    def switch_name(self, name: str):
        if self.mid_transition or name == self.current:
            return False
        if name not in self.screen_names:
            raise ValueError(f'Found no screen by name "{name}" in {self.screen_names}')
        old_transition = self.transition
        if self.auto_transition:
            old_index = self.screen_names.index(self.current)
            new_index = self.screen_names.index(name)
            dir = "left" if old_index < new_index else "right"
            self.transition = kv.SlideTransition(
                direction=dir,
                duration=self.auto_transtion_speed,
            )
        self.current = name
        if self.auto_transition:
            self.transition = old_transition
        return True

    @property
    def mid_transition(self):
        return 0 < self.current_screen.transition_progress < 1

    @classmethod
    def from_widgets(cls, widgets: Mapping[str, XWidget], **kwargs) -> "XScreenManager":
        sm = cls(**kwargs)
        for n, w in widgets.items():
            screen = XScreen(name=n)
            screen.add(w)
            sm.add(screen)
        return sm


Box = XBox
ZBox = XZBox
DBox = XDBox
Grid = XGrid
Stack = XStack
Relative = XRelative
Anchor = XAnchor
Scroll = XScroll
App = XApp
InputManager = XInputManager
Label = XLabel
CheckBox = XCheckBox
CheckBoxText = XCheckBoxText
Button = XButton
ToggleButton = XToggleButton
ImageButton = XImageButton
Entry = XEntry
Slider = XSlider
SliderText = XSliderText
Spinner = XSpinner
DropDown = XDropDown
PickColor = XPickColor
SelectColor = XSelectColor
ScreenManager = XScreenManager
Screen = XScreen
NoTransition = kv.NoTransition
FadeTransition = kv.FadeTransition
CardTransition = kv.CardTransition
SlideTransition = kv.SlideTransition
SwapTransition = kv.SwapTransition
WipeTransition = kv.WipeTransition
ShaderTransition = kv.ShaderTransition
InstructionGroup = kv.InstructionGroup
Color = kv.Color
Rectangle = kv.Rectangle
Rotate = kv.Rotate
PushMatrix = kv.PushMatrix
PopMatrix = kv.PopMatrix
__all__ = [
    "Box",
    "ZBox",
    "DBox",
    "Grid",
    "Stack",
    "Relative",
    "Anchor",
    "Scroll",
    "App",
    "frozen_overlay",
    "InputManager",
    "Label",
    "CheckBox",
    "CheckBoxText",
    "Button",
    "ToggleButton",
    "ImageButton",
    "Entry",
    "Slider",
    "SliderText",
    "Spinner",
    "DropDown",
    "PickColor",
    "SelectColor",
    "ScreenManager",
    "Screen",
    "NoTransition",
    "FadeTransition",
    "CardTransition",
    "SlideTransition",
    "SwapTransition",
    "WipeTransition",
    "ShaderTransition",
    "InstructionGroup",
    "Color",
    "Rectangle",
    "Rotate",
    "PushMatrix",
    "PopMatrix",
]
