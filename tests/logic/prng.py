# flake8: noqa
from hypothesis import settings, note, given, strategies as st
from botroyale.logic.prng import PRNG


st_prng = st.builds(PRNG, st.integers(min_value=0, max_value=PRNG.MAX_SEED_VALUE))


@given(st_prng)
def test_copy_next(rng):
    """Test that a copy has the same value."""
    rng_copy = rng.copy()
    rng_copy2 = PRNG(rng.seed)
    assert rng.value == rng_copy.value == rng_copy2.value
    assert next(rng) == next(rng_copy) == next(rng_copy2)


@given(st_prng)
def test_iteration(rng):
    """Test that `generate_list`, `iterate` and `next` produce the same values."""
    rng_copy = rng.copy()
    rng_copy2 = rng.copy()
    a, b = rng.generate_list(2)
    b_ = rng_copy.iterate(2)
    a__ = next(rng_copy2)
    b__ = next(rng_copy2)
    assert b == b_ == b__


@given(st_prng, st.integers(min_value=1, max_value=20))
def test_list(rng, size):
    """Test that `generate_list` reproduces the same values."""
    rng_copy = rng.copy()
    list1 = rng.generate_list(size)
    list2 = rng_copy.generate_list(size)
    assert list1 == list2
