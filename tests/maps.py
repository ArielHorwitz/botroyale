# flake8: noqa

from hypothesis import given, strategies as st
from botroyale.logic.maps import get_map_state, _find_maps
from botroyale.logic.state import State


MAPS = tuple(_find_maps(use_custom=False).keys())
st_map = st.sampled_from(MAPS)


@given(st_map)
def test_get_map_state(map):
    state = get_map_state(map)
    assert isinstance(state, State)
    assert not state.game_over
    assert state.end_of_round
    assert state.round_count == 0
    assert state.current_unit is None
    state = state.increment_round()
    assert not state.game_over
    assert not state.end_of_round
    assert state.round_count == 1
    assert state.current_unit is not None
