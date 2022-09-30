# flake8: noqa

from hypothesis import given, strategies as st
from tests.hexagon import st_hex
from botroyale.api.gui import Control, InputWidget, Tile, VFX
from botroyale.util.hexagon import Hexagon


st_vfx = st.builds(
    VFX,
    hex=st_hex,
    direction=st_hex,
)


@given(st.builds(Control))
def test_control(control):
    assert isinstance(control.label, str)
    if control.callback is not None:
        assert callable(control.callback)
    if control.hotkeys is not None:
        assert isinstance(control.hotkeys, list)
        for h in control.hotkeys:
            assert isinstance(h, str)


@given(st.builds(
    InputWidget,
    options=st.lists(st.text(), min_size=1),
))
def test_input_widget(iw):
    assert isinstance(iw.label, str)
    assert isinstance(iw.type, str)
    if iw.sendto is not None:
        assert isinstance(iw.sendto, str)
    if iw.options is not None:
        assert isinstance(iw.options, list)
        for o in iw.options:
            assert isinstance(o, str)


@given(st.builds(Tile))
def test_tile(tile):
    if tile.tile is not None:
        assert isinstance(tile.tile, str)
    assert isinstance(tile.bg, tuple)
    assert len(tile.bg) == 3
    if tile.sprite is not None:
        assert isinstance(tile.sprite, str)
    assert isinstance(tile.color, tuple)
    assert len(tile.color) == 3
    if tile.text is not None:
        assert isinstance(tile.text, str)


@given(st_vfx)
def test_vfx(vfx):
    assert isinstance(vfx.name, str)
    assert isinstance(vfx.hex, Hexagon)
    assert isinstance(vfx.direction, Hexagon)
    assert isinstance(vfx.start_step, int) or isinstance(vfx.start_step, float)
    assert isinstance(vfx.expire_step, int) or isinstance(vfx.expire_step, float)
    assert isinstance(vfx.expire_seconds, int) or isinstance(vfx.expire_seconds, float)
    assert isinstance(vfx.asdict(), dict)
