# flake8: noqa

from hypothesis import given, strategies as st
from botroyale.api.gui import GameAPI, BattleAPI, Control, InputWidget
from botroyale.logic.game import StandardGameAPI


APIS = [
    GameAPI,
    StandardGameAPI,
]
st_api = st.sampled_from(APIS)


@given(st_api)
def test_info_panel(api_cls):
    api = api_cls()
    ipanel_text = api.get_info_panel_text()
    assert isinstance(ipanel_text, str)


@given(st_api)
def test_get_controls(api_cls):
    api = api_cls()
    controls = api.get_controls()
    assert isinstance(controls, list)
    for c in controls:
        assert isinstance(c, Control)


@given(st_api)
def test_menu_widgets(api_cls):
    api = api_cls()
    menu_widgets = api.get_menu_widgets()
    assert isinstance(menu_widgets, list)
    for w in menu_widgets:
        assert isinstance(w, InputWidget)
    menu_values = {w.sendto: w.default for w in menu_widgets}

    @given(st.sampled_from(menu_widgets))
    def test_handle(w):
        api.handle_menu_widget(w.sendto, menu_values)


@given(st_api)
def test_new_battle(api_cls):
    api = api_cls()
    menu_widgets = api.get_menu_widgets()
    menu_values = {w.sendto: w.default for w in menu_widgets}
    new_battle = api.get_new_battle(menu_values)
    assert isinstance(new_battle, BattleAPI) or new_battle is None
