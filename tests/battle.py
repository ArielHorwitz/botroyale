# flake8: noqa

from hypothesis import settings, given, strategies as st
from botroyale.logic.maps import get_map_state
from botroyale.api.bots import BotSelection
from botroyale.logic.battle import Battle
from tests.maps import st_map


BOT_SELECTION_BASIC = BotSelection(["basic"])


def new_battle(map):
    return Battle(
        initial_state=get_map_state(map),
        bots=BOT_SELECTION_BASIC,
        enable_logging=False,
    )


@given(st_map)
@settings(deadline=None)
def test_make_battle(map):
    new_battle(map)


def test_play_battle():
    b = new_battle("basic")
    b.play_all()
