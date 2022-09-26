# flake8: noqa

from hypothesis import settings, given, note, strategies as st
from tests.hexagon import st_hex, st_rotation, MAX_DIST
from tests.logic.maps import st_map
from botroyale.util.hexagon import Hexagon
from botroyale.api.actions import Idle, Move, Jump, Push
from botroyale.logic.state import State
from botroyale.logic.plate import Plate


st_plate = st.builds(
    Plate,
    cube=st.builds(lambda h: h.cube, st_hex),
    plate_type=...,
    pressure=st.integers(max_value=-1),
    min_pressure=st.integers(max_value=-1),
    pressure_reset=...,
    targets=st.sets(st_hex),
)
st_state = st.builds(
    State,
    death_radius=st.integers(min_value=1, max_value=50),  # TODO assert raises on small radius
    positions=st.lists(st_hex, min_size=2, max_size=10),
    pits=st.sets(st_hex, max_size=10),
    walls=st.sets(st_hex, max_size=10),
    plates=st.sets(st_plate, max_size=2),
)
st_action_type = st.sampled_from([Idle, Move, Jump, Push])
st_action_target = st.integers(min_value=0, max_value=11)


def get_action(state, atype, target):
    pos = state.positions[state.current_unit]
    if atype is Idle:
        return Idle()
    if atype in {Jump}:
        fixed_target = pos.ring(2)[target]
    else:
        fixed_target = pos.neighbors[target % 6]
    return atype(fixed_target)


@given(st_plate)
def test_make_plate(plate):
    assert isinstance(plate, Plate)
    assert isinstance(plate, Hexagon)


@given(st_state)
def test_make_state(state):
    assert isinstance(state, State)
    assert state.round_count == 0
    assert state.end_of_round
    assert not state.game_over
    assert state.num_of_units >= 2
    assert sum(state.alive_mask) >= 2


@given(st_state)
def test_increment_round(state):
    next_state = state.increment_round()
    assert isinstance(next_state, State)
    assert next_state.round_count == state.round_count + 1
    assert next_state.step_count == state.step_count + 1


@given(st_map, st_action_type, st_action_target)
def test_apply_action(initial_state, atype, target):
    state = initial_state.increment_round()
    action = get_action(state, atype, target)
    next_state = state.apply_action(action)
    assert isinstance(next_state, State)
    assert next_state.step_count > state.step_count
    next_state_manual = state.apply_action_manual(action)
    assert isinstance(next_state_manual, State)
    assert next_state_manual.step_count == state.step_count + 1
    assert next_state_manual.last_action is action


@given(st_map, st_action_type, st_action_target)
def test_check_legal_action(initial_state, atype, target):
    state = initial_state.increment_round()
    action = get_action(state, atype, target)
    is_legal = state.check_legal_action(action)
    next_state = state.apply_action_manual(action)
    assert next_state.is_last_action_legal == is_legal


@given(st_map)
def test_apply_kill_unit(initial_state):
    state = initial_state.increment_round()
    uid = state.current_unit
    assert state.alive_mask[uid]
    next_state = state.apply_kill_unit()
    assert isinstance(next_state, State)
    assert next_state.step_count > state.step_count
    assert not next_state.alive_mask[uid]
    next_state_manual = state.apply_kill_unit_manual()
    assert isinstance(next_state_manual, State)
    assert next_state_manual.step_count == state.step_count + 1
    assert not next_state_manual.alive_mask[uid]
