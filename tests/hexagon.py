# flake8: noqa

from hypothesis import (
    settings,
    note,
    given,
    strategies as st,
)
from datetime import timedelta
import botroyale.util.hexagon
from botroyale.util.hexagon import Hexagon, ORIGIN


MAX_DIST = 100
st_hex = st.builds(
    Hexagon.from_qr,
    st.integers(min_value=-MAX_DIST, max_value=MAX_DIST),
    st.integers(min_value=-MAX_DIST, max_value=MAX_DIST),
)
st_rotation = st.integers(min_value=0, max_value=5)
st_floats = st.floats(allow_nan=False, allow_infinity=False)


@given(st.builds(Hexagon.from_qr))
def test_from_qr(h):
    assert sum(h.cube) == 0


@given(st_hex, st_rotation)
def test_geometry(hex, n):
    neighbor = hex.neighbors[n]
    assert neighbor in hex.ring(1)


@given(st_hex, st_rotation, st_rotation)
def test_geometry_double(hex, n, d):
    neighbor = hex.neighbors[n]
    double = next(hex.straight_line(neighbor))
    assert double in hex.doubles
    assert double in hex.ring(2)
    d0 = hex.doubles[d]
    d1 = hex.doubles[d - 1]
    shared_neighbor = set(d0.neighbors) & set(d1.neighbors)
    assert len(shared_neighbor) == 1
    diagonal = shared_neighbor.pop()
    assert diagonal in hex.diagonals
    assert diagonal in hex.ring(2)


@given(st_floats, st_floats, st_floats)
def test_rounding(q, r, s):
    h = Hexagon.from_floats(q, r, s)
    assert sum(h.cube) == 0


@given(st_hex)
def test_ring2(hex):
    dbl_set = set(hex.doubles)
    diag_set = set(hex.diagonals)
    ring_set = set(hex.ring(2))
    assert diag_set | dbl_set == ring_set
    assert len(diag_set & dbl_set) == 0
    assert ring_set - dbl_set == diag_set
    assert ring_set - diag_set == dbl_set
    assert dbl_set | diag_set == ring_set


@given(st_hex)
def test_rotate(hex):
    d = ORIGIN.get_distance(hex)
    ring = ORIGIN.ring(d)
    for rot in range(6):
        rotated_hex = hex.rotate(rot)
        assert rotated_hex in ring


@given(st_hex)
def test_cache(hex):
    """The Hexagon class functools.cache works as expected."""
    hex2 = Hexagon(*hex.cube)
    neighbor = hex.neighbors[0]
    _get_neighbors_method = botroyale.util.hexagon._get_neighbors
    _get_neighbors_method.cache_clear()
    assert neighbor in hex.neighbors  # Call the cache
    assert _get_neighbors_method.cache_info().misses == 1
    assert _get_neighbors_method.cache_info().hits == 0
    assert neighbor in set(hex2.neighbors)  # Call the cache
    assert _get_neighbors_method.cache_info().misses == 1
    assert _get_neighbors_method.cache_info().hits == 1


@given(st_hex)
def test_cache_instances(hex):
    """The Hexagon class functools.cache works as expected on instance methods."""
    hex2 = Hexagon(*hex.cube)
    neighbor = hex.neighbors[0]
    Hexagon.ring.cache_clear()
    assert neighbor in hex.ring(1)  # Call the cache
    assert Hexagon.ring.cache_info().misses == 1
    assert Hexagon.ring.cache_info().hits == 0
    assert neighbor in set(hex2.ring(1))  # Call the cache
    assert Hexagon.ring.cache_info().misses == 1
    assert Hexagon.ring.cache_info().hits == 1


@given(
    st_hex,
    st.floats(
        min_value=0,
        allow_infinity=False,
        allow_nan=False,
        exclude_min=True,
    ),
)
def _test_pixel_position(hex, radius):
    xy = hex.pixel_position(radius)
    assert hex == ORIGIN.pixel_position_to_hex(radius, xy)


@given(st_hex, st_hex)
def test_eq(hex1, hex2):
    new_hex = hex1 + hex2
    orig_hex = new_hex - hex2
    assert hex1 == orig_hex


@given(st_hex, st_rotation, st.integers(min_value=3, max_value=20))
@settings(deadline=timedelta(milliseconds=500))  # Hexagon method results are cached, and so are "flaky" in deadline
def test_ring_range(hex, neighbor_index, distance):
    neighbor = hex.neighbors[neighbor_index]
    target_line = [hex, neighbor, *hex.straight_line(neighbor, distance-2)]
    hex_range = hex.range(distance)
    for i, target in enumerate(target_line):
        assert target in hex.ring(i)
        assert target in hex_range
