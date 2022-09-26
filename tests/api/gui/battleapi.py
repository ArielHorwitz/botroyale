# flake8: noqa

from hypothesis import given, strategies as st
from tests.hexagon import st_hex
from botroyale.api.gui import BattleAPI, Control, InputWidget, Tile
from botroyale.logic.game import BattleManager


st_api = st.one_of(
    st.builds(BattleAPI),
    st.builds(
        BattleManager,
        enable_logging=st.just(False),
        gui_mode=st.just(False),
    ),
)
st_vfx = dict(
    name=st.text(),
    hex=st_hex,
    direction=st.one_of(
        st.just(None),
        st_hex,
    ),
    steps=st.integers(min_value=1),
    expire_seconds=st.one_of(
        st.just(None),
        st.floats(min_value=0, allow_nan=False),
    )
)


@given(st_api)
def test_update(api):
    api.update()


@given(st_api)
def test_get_time(api):
    time = api.get_time()
    assert isinstance(time, int) or isinstance(time, float)


@given(st_api)
def test_get_controls(api):
    controls = api.get_controls()
    assert isinstance(controls, list)
    for c in controls:
        assert isinstance(c, Control)


@given(st_api)
def test_get_info_panel_text(api):
    text = api.get_info_panel_text()
    assert isinstance(text, str)


@given(st_api)
def test_get_info_panel_color(api):
    text = api.get_info_panel_text()
    assert isinstance(text, str)


@given(st_api, st_hex)
def test_get_gui_tile_info(api, hex):
    tile = api.get_gui_tile_info(hex)
    assert isinstance(tile, Tile)


@given(st_api)
def test_get_map_size_hint(api):
    size_hint = api.get_map_size_hint()
    assert isinstance(size_hint, int) or isinstance(size_hint, float)


@given(
    api=st_api,
    hex=st_hex,
    button=st.sampled_from(
        ["left", "right", "middle", *(f"mouse{i}" for i in range(12))]
    ),
    mods=st.builds(
        lambda x: "".join(_ for _ in x),
        st.sets(st.sampled_from("^!+#")),
    ),
)
def test_handle_hex_click(api, hex, button, mods):
    api.handle_hex_click(hex, button, mods)


@given(api=st_api, **st_vfx)
def test_add_flush_vfx(api, **vfx):
    api.flush_vfx()
    assert len(api.flush_vfx()) == 0
    api.add_vfx(**vfx)
    assert len(api.flush_vfx()) == 1


@given(api=st_api, **st_vfx)
def test_add_clear_vfx(api, **vfx):
    api.flush_vfx()
    api.add_vfx(**vfx)
    api.clear_vfx(flush_queued=True)
    assert len(api.flush_vfx()) == 0


@given(api=st_api)
def test_clear_vfx_flag(api):
    api.clear_vfx_flag()
    assert api.clear_vfx_flag() is False
    api.clear_vfx(clear_existing=True)
    assert api.clear_vfx_flag() is True
    assert api.clear_vfx_flag() is False
