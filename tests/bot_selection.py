# flake8: noqa

from collections import Counter
from hypothesis import (
    settings,
    note,
    given,
    strategies as st,
    Verbosity
)
from botroyale.api.bots import BotSelection, BOTS
from botroyale.logic.battle import Battle


NORMAL_BOTS = list(set(BOTS.keys()) - {"dummy"})


# Custom strategies
st_name = st.sampled_from(NORMAL_BOTS)
st_names = st.sets(st_name, min_size=1)
st_slots = st.integers(min_value=2, max_value=1000)
st_selection = st.builds(BotSelection, st_names)
st_selection_full = st.builds(
    BotSelection,
    selection=st_names,
    ignore=st_names,
    keep_fair=...,
    no_dummies=...,
    all_play=...,
    max_repeat=...,
)


def do_select_counter(*args, **kwargs):
    bot_list = do_select(*args, **kwargs)
    counter = Counter(bot_list)
    note(f"{counter=}")
    return counter

def do_select(slots, *args, filter_dummies=False, **kwargs):
    selection = BotSelection(*args, **kwargs)
    note(f"{selection.selection=}")
    return [
        b.NAME for b in selection.get_bots(slots)
        if not filter_dummies or b.NAME != "dummy"
    ]


@given(st_selection, st_slots)
def test_get_bots_simple(selection, slots):
    note(f"{selection.selection=}")
    note(f"{slots=}")
    selection.get_bots(slots)


@given(st_slots, st_names)
def test_keep_fair(slots, names):
    counter = do_select_counter(slots, names, filter_dummies=True, keep_fair=True)
    counts = list(counter.values())
    count = counts[0]
    assert all(c == count for c in counts)


@given(st_slots, st_names, st_slots)
def test_max_repeat(slots, names, max_repeat):
    counter = do_select_counter(
        slots,
        names,
        max_repeat=max_repeat,
        filter_dummies=True,
    )
    assert all(c <= max_repeat for c in list(counter.values()))
