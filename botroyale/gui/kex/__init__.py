"""The Kex library.

An interface to the [Kivy](https://kivy.org/) library with extended widgets for
convenience. It focuses on making it easier (and maybe a little more intuitive)
to write kivy apps programmatically.

## KexMixin
The `KexMixin` class is a mixin class for kivy widgets with convenience methods.
"""
import os as __os

# Kivy configuration must be done before importing kivy
__os.environ["KIVY_NO_ARGS"] = "1"  # no consuming script arguments
__os.environ["KCFG_KIVY_LOG_LEVEL"] = "warning"  # no spamming console on startup


from .kivy import (  # noqa: E402,F401
    NoTransition,
    FadeTransition,
    CardTransition,
    SlideTransition,
    SwapTransition,
    WipeTransition,
    ShaderTransition,
    InstructionGroup,
    Color,
    Rectangle,
    Rotate,
    PushMatrix,
    PopMatrix,
)
from .util import (  # noqa: E402,F401
    XWindow as Window,
    XColor,
    get_color,
    random_color,
    center_sprite,
    text_texture,
    restart_script,
    placeholder,
    consume_args,
    schedule_once,
    schedule_interval,
    queue_around_frame,
)
from .widgets.layouts import (  # noqa: E402,F401
    XBox as Box,
    XZBox as ZBox,
    XDBox as DBox,
    XGrid as Grid,
    XRelative as Relative,
    XStack as Stack,
    XAnchor as Anchor,
    XScroll as Scroll,
)
from .widgets.uix import (  # noqa: E402,F401
    XLabel as Label,
    XCheckBox as CheckBox,
    XCheckBoxText as CheckBoxText,
    XButton as Button,
    XToggleButton as ToggleButton,
    XImageButton as ImageButton,
    XEntry as Entry,
    XSlider as Slider,
    XSliderText as SliderText,
    XSpinner as Spinner,
    XDropDown as DropDown,
    XPickColor as PickColor,
    XSelectColor as SelectColor,
    XScreenManager as ScreenManager,
    XScreen as Screen,
)
from .widgets.input_manager import XInputManager as InputManager  # noqa: E402,F401,F402
from .widgets.app import XApp as App  # noqa: E402,F401,F402


__all__ = []
__pdoc__ = {
    "kivy": False,
}
