# flake8: noqa

from hypothesis import settings, given, note, strategies as st
from tests.logic.maps import st_map
from botroyale.api.bots import BotSelection, BaseBot
from botroyale.logic.maps import get_map_state
from botroyale.logic.battle import Battle
from botroyale.logic.state import State


BOT_SELECTION = BotSelection()
BOT_SELECTION_BASIC = BotSelection(["basic"])


@given(st_map)
def test_make_battle_with_maps(initial_state):
    Battle(
        initial_state=initial_state,
        bots=BOT_SELECTION_BASIC,
        enable_logging=False,
    )


# hypothesis will only try True/False but we are explicit since this plays
# a full battle.
@settings(max_examples=2)
@given(only_bot_turn_states=st.booleans())
def test_play_full_battle(only_bot_turn_states):
    b = Battle(
        initial_state=get_map_state("basic"),
        bots=BOT_SELECTION_BASIC,
        only_bot_turn_states=only_bot_turn_states,
        enable_logging=False,
    )
    if only_bot_turn_states:
        assert isinstance(b.previous_state, State)
    else:
        assert b.previous_state is None
    b.play_all()
    assert b.state.game_over is True
    assert b.history_size > 1
    assert len(b.history) == b.history_size
    assert len(b.losers) > 0
    # This part on winner is flaky: sometimes there may be a draw and sometimes
    # there may be a win.
    if b.winner is None:
        assert isinstance(b.winner, int)
        assert len(b.losers) == len(b.bots)
    else:
        assert len(b.losers) == len(b.bots) - 1


@given(st_map, st.booleans())
def test_play_states(initial_state, only_bot_turn_states):
    b = Battle(
        initial_state=initial_state,
        bots=BOT_SELECTION_BASIC,
        only_bot_turn_states=only_bot_turn_states,
        enable_logging=False,
    )
    b.play_state()
    b.play_states(3)


@given(st_map, st.booleans())
def test_attributes(initial_state, only_bot_turn_states):
    b = Battle(
        initial_state=initial_state,
        bots=BOT_SELECTION_BASIC,
        only_bot_turn_states=only_bot_turn_states,
        enable_logging=False,
    )
    assert isinstance(b.description, str)
    for uid in range(len(b.bots)):
        assert isinstance(b.get_unit_str(uid), str)
    for bot in b.bots:
        assert isinstance(bot, BaseBot)
    b.play_state()
    assert b.state.step_count > b.previous_state.step_count
    assert isinstance(b.get_state_str(b.state), str)
    assert isinstance(b.get_state_str(b.previous_state), str)
