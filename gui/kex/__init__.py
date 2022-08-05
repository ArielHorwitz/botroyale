import logging
logger = logging.getLogger(__name__)


import os, sys
import time
import enum
import random
import numpy as np

# Kivy configuration must be done before importing kivy
# Prevent kivy consuming script arguments
os.environ['KIVY_NO_ARGS'] = '1'
# Prevent kivy spamming console on startup
os.environ['KCFG_KIVY_LOG_LEVEL'] = 'warning'
import kivy
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.config import Config as kvConfig
from kivy.graphics import Color, Rectangle


class KexWidget:
    def make_fg(self, *args, **kwargs):
        return make_fg(self, *args, **kwargs)

    def make_bg(self, *args, **kwargs):
        return make_bg(self, *args, **kwargs)

    def _update_fg(self, *args, **kwargs):
        return _update_fg(self, *args, **kwargs)

    def _update_bg(self, *args, **kwargs):
        return _update_bg(self, *args, **kwargs)

    def add(self, *args, **kwargs):
        if 'index' in kwargs:
            if kwargs['index'] == -1:
                kwargs['index'] = len(self.children)
        return add(self, *args, **kwargs)

    def set_size(self, *args, **kwargs):
        return set_size(self, *args, **kwargs)

    def set_position(self, *args, **kwargs):
        return set_position(self, *args, **kwargs)

    def bind(self, *args, **kwargs):
        super().bind(*args, **kwargs)
        return self

    @property
    def is_root_descendant(self):
        w = self
        while w.parent:
            if self.parent is self.app.root:
                return True
            w = w.parent
        return False

    @property
    def get_root_screen(self):
        w = self
        while not isinstance(self, BaseWidgets.Screen):
            w = w.parent
        return w

    @property
    def bg_color(self):
        return self._bg_color.hsv

    @property
    def app(self):
        return kivy.app.App.get_running_app()


class Config:
    @staticmethod
    def enable_escape_exit(x=True):
        kvConfig.set('kivy', 'exit_on_escape', str(int(x)))

    @staticmethod
    def disable_multitouch():
        kvConfig.set('input', 'mouse', 'mouse,disable_multitouch')

    @staticmethod
    def set_window_resize(x):
        kvConfig.set('graphics', 'resizable', x)

    @staticmethod
    def disable_consolelog():
        os.environ['KIVY_NO_CONSOLELOG'] = '1'


def after_next_frame(f):
    Clock.schedule_once(f, 0)

def schedule(f, t):
    Clock.schedule_once(f, t)

def set_size(widget, x=None, y=None, hx=1, hy=1):
    hx = hx if x is None else None
    hy = hy if y is None else None
    x = widget.width if x is None else x
    y = widget.height if y is None else y

    widget.size_hint = (hx, hy)
    widget.size = (int(x), int(y))
    return widget

def set_position(widget, pos):
    widget.pos = int(pos[0]), int(pos[1])
    return widget

def add(parent, child, *args, reverse_index=None, **kwargs):
    if reverse_index is not None:
        kwargs['index'] = len(parent.children) - reverse_index
    parent.add_widget(child, *args, **kwargs)
    return child

def _update_bg(widget, *args):
    widget._bg.pos = widget.pos
    widget._bg.size = widget.size

def make_bg(widget, color=None, source=None):
    if color is None:
        color = random_color(v=0.3)
    if hasattr(widget, '_bg'):
        if widget._bg_color is None:
            raise RuntimeError(f'widget {widget} has _bg but no _bg_color')
        if not isinstance(widget._bg_color, Color):
            raise RuntimeError(f'widget {widget} _bg_color is not a Color instruction')
        if len(color) == 3:
            color = (*color, 1)
        widget._bg_color.rgba = color
        if source is not None:
            widget._bg.source = source
        return color
    with widget.canvas.before:
        widget._bg_color = Color(*color)
        widget._bg = Rectangle(size=widget.size, pos=widget.pos)
        if source is not None:
            widget._bg.source = source
        widget.bind(pos=widget._update_bg, size=widget._update_bg)
    return color

def _update_fg(widget, *args):
    widget._fg.pos = widget.pos
    widget._fg.size = widget.size

def make_fg(widget, color=None, source=None):
    if color is None:
        color = random_color(v=0.3)
    if hasattr(widget, '_fg'):
        if widget._fg_color is None:
            raise RuntimeError(f'widget {widget} has _fg but no _fg_color')
        if not isinstance(widget._fg_color, Color):
            raise RuntimeError(f'widget {widget} _fg_color is not a Color instruction')
        if len(color) == 3:
            color = (*color, 1)
        widget._fg_color.rgba = color
        if source is not None:
            widget._fg.source = source
        return color
    with widget.canvas.after:
        widget._fg_color = Color(*color)
        widget._fg = Rectangle(size=widget.size, pos=widget.pos)
        if source is not None:
            widget._fg.source = source
        widget.bind(pos=widget._update_fg, size=widget._update_fg)
    return color

def set_focus(w, delay=0.05):
    if delay:
        Clock.schedule_once(lambda w=w: _do_set_focus(w), delay)
    else:
        _do_set_focus(w)

def _do_set_focus(w):
    w.focus = True

def random_color(v=1, a=1):
    return list(np.array(tuple(random.random() for _ in range(3)))*v)+[a]

def modify_color(color, v=1, a=1):
    assert 3 <= len(color) <= 4
    if len(color) == 4:
        a = color[3]*a
        color = color[:3]
    return tuple((*(np.array(color)*v), a))

def alternate_color(color, drift=1/2):
    r = list((_+drift)%1 for _ in color[:3])
    r.append(color[3] if len(color) == 4 else 1) # alpha
    return r

def restart_script():
    logger.info('--- Restarting python script ---')
    os.execl(sys.executable, sys.executable, *sys.argv)

def ping():
    return time.time() * 1000

def pong(ping_):
    return time.time() * 1000 - ping_

def resize_window(new_size):
    old_size = widgets.kvWindow.size
    t, l = widgets.kvWindow.top, widgets.kvWindow.left
    b, r = t + old_size[1], l + old_size[0]
    center = np.asarray([(t+b) / 2, (l+r) / 2])
    center_offset = np.asarray([new_size[1], new_size[0]]) / 2
    new_top_left = tuple(int(_) for _ in (center - center_offset))
    widgets.kvWindow.size = new_size
    widgets.kvWindow.top, widgets.kvWindow.left = new_top_left
