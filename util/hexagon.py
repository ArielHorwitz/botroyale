"""
Home of the `util.hexagon.Hexagon` class and related constants.
"""
from typing import Sequence, Generator
import math
import functools


SQRT3 = math.sqrt(3)
WIDTH_HEIGHT_RATIO = SQRT3 / 2
GRID_OFFSET = -1


class Hexagon:
    """Represents a whole-number point in hex-space, or a whole-number vector from the origin (0, 0, 0) in hex-space."""

    def __init__(self, q: int, r: int, s: int):
        self.__cube: tuple[int, int, int] = (q, r, s)
        assert all(isinstance(c, int) for c in self.__cube)
        self.__offset: tuple[int, int] = convert_cube2offset(q, r, s)

    @functools.cache
    def get_distance(self, hex: 'Hexagon') -> int:
        """Get the number of steps (to a neighbor hex) required to reach hex from self."""
        delta = self - hex
        return max(abs(c) for c in delta.cube)

    def straight_line(self, neighbor: 'Hexagon', max_distance: int = 20) -> Generator['Hexagon', None, None]:
        """Returns a generator that yields the hexes following a straight line,
        starting from self through neighbor. Does not include self or neighbor.

        max_distance        -- The number of hexes to yield.
        """
        assert neighbor in self.neighbors
        dir = neighbor - self
        counter = 0
        while counter < max_distance:
            counter += 1
            neighbor += dir
            yield neighbor

    @functools.cache
    def ring(self, radius: int) -> tuple['Hexagon', ...]:
        """Returns a tuple of hexes that are `radius` distance from self.

        The resulting hexes are always in the same order, with regards to their
        relative position from self.
        """
        if radius < 0:
            raise ValueError(f'Radius must be non-negative, got: {radius}')
        if radius == 0:
            return [self]
        if radius == 1:
            return list(self.neighbors)
        ring = []
        dir_ngbr = self + DIRECTIONS[4]
        hex = list(self.straight_line(dir_ngbr, max_distance=radius-1))[-1]
        for i in range(6):
            for _ in range(radius):
                ring.append(hex)
                hex = hex + DIRECTIONS[i]
        return tuple(ring)

    @functools.cache
    def range(self, distance: int, include_center: bool = True) -> tuple['Hexagon', ...]:
        """Returns a tuple of all the hexes within a distance from self.

        The resulting hexes are always in the same order, with regards to their
        relative position from self.

        include_center      -- include self in the results
        """
        results = []
        for q in range(-distance, distance+1):
            for r in range(max(-distance, -q-distance), min(+distance, -q+distance)+1):
                s = -q-r
                results.append(self + Hexagon(q, r, s))
        if not include_center:
            results.remove(self)
        return tuple(results)

    @functools.cache
    def rotate(self, rotations: int = 1) -> 'Hexagon':
        """Return the hex given by rotating self about `ORIGIN` by 60° per rotation."""
        assert isinstance(rotations, int)
        hex = self
        if rotations > 0:
            while rotations > 0:
                hex = Hexagon(-hex.r, -hex.s, -hex.q)
                rotations -= 1
        elif rotations < 0:
            while rotations < 0:
                hex = Hexagon(-hex.s, -hex.q, -hex.r)
                rotations += 1
        return hex

    # Nearby hexes
    @property
    def neighbors(self) -> tuple['Hexagon', ...]:
        """The 6 adjascent hexes.

        The resulting hexes are always in the same order, with regards to their
        relative position from *self*.
        """
        return _get_neighbors(self)

    @property
    def doubles(self) -> tuple['Hexagon', ...]:
        """The 6 hexes that are 2 distance away and can be found on
        a straight line originating from *self*.

        The resulting hexes are always in the same order, with regards to their
        relative position from *self*.

        Doubles and diagonals are complementary parts of `Hexagon.ring` with `radius=2`.
        """
        return _get_doubles(self)

    @property
    def diagonals(self) -> tuple['Hexagon', ...]:
        """The 6 hexes that are 2 distance away and cannot be found on
        a straight line originating from *self*.

        The resulting hexes are always in the same order, with regards to their
        relative position from *self*.

        Doubles and diagonals are complementary parts of `Hexagon.ring` with `radius=2`.
        """
        return _get_diagonals(self)

    # Operations
    def __add__(self, other: 'Hexagon') -> 'Hexagon':
        """Cube addition of hexagons. Can be used like vectors."""
        assert type(other) is type(self)
        return Hexagon(self.q+other.q, self.r+other.r, self.s+other.s)

    def __sub__(self, other: 'Hexagon') -> 'Hexagon':
        """Cube subtraction of hexagons. Can be used like vectors."""
        assert type(other) is type(self)
        return Hexagon(self.q-other.q, self.r-other.r, self.s-other.s)

    def __eq__(self, other: 'Hexagon') -> bool:
        """Returns if self and other share coordinates."""
        if not type(other) is type(self):
            return False
        return self.cube == other.cube

    @classmethod
    def round_(cls, q: float, r: float, s: float) -> 'Hexagon':
        """Cube rounding. Will take floating point cube coordinates and return
        the nearest hex."""
        q_ = round(q)
        r_ = round(r)
        s_ = round(s)
        qdiff = abs(q_ - q)
        rdiff = abs(r_ - r)
        sdiff = abs(s_ - s)
        if qdiff > rdiff and qdiff > sdiff:
            q_ = -r_ - s_
        elif rdiff > sdiff:
            r = -q_ - s_
        else:
            s = -q_ - r_
        return cls(q_, r_, s_)

    # Position in 2D space
    @functools.cache
    def pixel_position(self, radius: int) -> tuple[int, int]:
        """Position in pixels of self, given the radius of a hexagon in pixels."""
        offset_r = (self.y % 2 == 1) / 2
        x = radius * SQRT3 * (self.x + offset_r)
        y = radius * 3/2 * self.y
        return x, y

    @functools.cache
    def pixel_position_to_hex(self, radius: int, pixel_coords: Sequence[float]) -> 'Hexagon':
        """The hex at position `pixel_coords` given the radius of a hexagon in
        pixels, assuming self is centered at the origin."""
        x, y = pixel_coords[0] / radius, pixel_coords[1] / radius
        q = (SQRT3/3 * x) + (-1/3 * y)
        r = 2/3 * y
        offset = self.round_(q, r, -q-r)
        return offset - self

    # Constructors
    @classmethod
    def from_xy(cls, x: int, y: int) -> 'Hexagon':
        """Return the `Hexagon` given the offset (x, y) coordinates."""
        return cls(*convert_offset2cube(x, y))

    @classmethod
    def from_qr(cls, q: int, r: int) -> 'Hexagon':
        """Return the `Hexagon` given the partial cube coordinates (q, r)."""
        s = -q - r
        return cls(q, r, s)

    @classmethod
    def from_floats(cls, q: float, r: float, s: float) -> 'Hexagon':
        """Return the `Hexagon` nearest to the floating point cube coordinates (q, r, s)."""
        return cls.round_(q, r, s)

    # Representations
    @property
    def x(self) -> int:
        """X component of the offset (x, y) coordiantes."""
        return self.__offset[0]

    @property
    def y(self) -> int:
        """Y component of the offset (x, y) coordiantes."""
        return self.__offset[1]

    @property
    def xy(self) -> tuple[int, int]:
        """Offset coordiantes."""
        return self.__offset

    @property
    def q(self) -> int:
        """Q component of the cube (q, r, s) coordiantes."""
        return self.__cube[0]

    @property
    def r(self) -> int:
        """R component of the cube (q, r, s) coordiantes."""
        return self.__cube[1]

    @property
    def s(self) -> int:
        """S component of the cube (q, r, s) coordiantes."""
        return self.__cube[2]

    @property
    def qr(self) -> tuple[int, int]:
        """Q and R components of the cube (q, r, s) coordiantes."""
        return self.__cube[:2]

    @property
    def cube(self) -> tuple[int, int, int]:
        """Cube (q, r, s) coordiantes."""
        return self.__cube

    def __repr__(self):
        return f'<Hex {self.x}, {self.y}>'

    def __hash__(self):
        return hash(self.cube)


# Common Hexagon getters
@functools.cache
def _get_neighbors(hex: Hexagon) -> tuple[Hexagon, ...]:
    return tuple(hex + dir for dir in DIRECTIONS)


@functools.cache
def _get_doubles(hex: Hexagon) -> tuple[Hexagon, ...]:
    return tuple(hex + doub for doub in DOUBLES)


@functools.cache
def _get_diagonals(hex: Hexagon) -> tuple[Hexagon, ...]:
    return tuple(hex + diag for diag in DIAGONALS)


# Coordinate conversion (cube and offset)
@functools.cache
def convert_offset2cube(x: int, y: int) -> Hexagon:
    """Convert offset coordinates (x, y) to cube coordinates (q, r, s)."""
    q = x - (y + GRID_OFFSET * (y & 1)) // 2
    r = y
    s = -q - r
    return q, r, s


@functools.cache
def convert_cube2offset(q: int, r: int, s: int) -> tuple[int, int]:
    """Convert cube coordinates (q, r, s) to offset coordinates (x, y)."""
    col = q + (r + GRID_OFFSET * (r & 1)) // 2
    row = r
    return col, row


# Order of directions, doubles, and diagonals are expected to be constant
ORIGIN: Hexagon = Hexagon(0, 0, 0)
"""The origin of the coordiante system. (0, 0, 0) in cube and (0, 0) in offset coordinates."""
DIRECTIONS: tuple[Hexagon, ...] = (
    Hexagon(1, 0, -1),
    Hexagon(1, -1, 0),
    Hexagon(0, -1, 1),
    Hexagon(-1, 0, 1),
    Hexagon(-1, 1, 0),
    Hexagon(0, 1, -1),
    )
"""The 6 adjascent hexes to `ORIGIN`. Can be considered the 6 directional normal vectors in hex-space."""
DOUBLES: tuple[Hexagon, ...] = (
    Hexagon(2, 0, -2),
    Hexagon(2, -2, 0),
    Hexagon(0, -2, 2),
    Hexagon(-2, 0, 2),
    Hexagon(-2, 2, 0),
    Hexagon(0, 2, -2),
    )
"""The 6 hexes that are 2 distance away and can be found on a straight line originating from `ORIGIN`."""
DIAGONALS: tuple[Hexagon, ...] = (
    Hexagon(2, -1, -1),
    Hexagon(1, -2, 1),
    Hexagon(-1, -1, 2),
    Hexagon(-2, 1, 1),
    Hexagon(-1, 2, -1),
    Hexagon(1, 1, -2),
    )
"""The 6 hexes that are 2 distance away and cannot be found on a straight line originating from `ORIGIN`."""


# Alias for xy constructor
Hex = Hexagon.from_xy


def test():
    origin = Hexagon(0, 0, 0)
    origin_copy = Hexagon(0, 0, 0)
    assert not origin is origin_copy
    assert origin == origin_copy
    neighbor = Hex(1, 0)

    # Test the cache
    _get_neighbors.cache_clear()
    assert neighbor in origin.neighbors
    assert _get_neighbors.cache_info().misses == 1
    assert _get_neighbors.cache_info().hits == 0
    assert neighbor in set(origin_copy.neighbors)
    assert _get_neighbors.cache_info().misses == 1
    assert _get_neighbors.cache_info().hits == 1

    # Test the cache for instance methods
    Hexagon.ring.cache_clear()
    assert neighbor in origin.ring(1)
    assert Hexagon.ring.cache_info().misses == 1
    assert Hexagon.ring.cache_info().hits == 0
    assert neighbor in set(origin_copy.ring(1))
    assert Hexagon.ring.cache_info().misses == 1
    assert Hexagon.ring.cache_info().hits == 1

    Hexagon.ring.cache_clear()
    assert neighbor in origin.ring(1)
    assert Hexagon.ring.cache_info().misses == 1
    assert Hexagon.ring.cache_info().hits == 0
    assert origin in neighbor.ring(1)
    assert Hexagon.ring.cache_info().misses == 2
    assert Hexagon.ring.cache_info().hits == 0

    # Assert geometry
    assert origin.neighbors == origin_copy.neighbors
    assert neighbor in origin.ring(1)
    assert neighbor in set(origin_copy.ring(1))
    assert neighbor in origin_copy.range(1)
    assert neighbor in set(origin.range(1))

    double = next(origin.straight_line(neighbor))
    assert double in origin.doubles
    d0 = origin.doubles[0]
    d1 = origin.doubles[1]
    shared_neighbor = set(d0.neighbors) & set(d1.neighbors)
    assert len(shared_neighbor) == 1
    diagonal = shared_neighbor.pop()
    assert diagonal in origin.diagonals

    dbl_set = set(origin.doubles)
    diag_set = set(origin.diagonals)
    ring_set = set(origin.ring(2))
    assert diag_set | dbl_set == ring_set
    assert len(diag_set & dbl_set) == 0
    assert ring_set - dbl_set == diag_set
    assert ring_set - diag_set == dbl_set
    assert dbl_set | diag_set == ring_set


try:
    test()
except Exception as e:
    raise Exception(f'{e}\nHexagon module tests FAILED. See previous traceback (above "During handling of the above exception...")')


__all__ = [
    'Hexagon',
    'Hex',
    'ORIGIN',
    'DIRECTIONS',
    'DOUBLES',
    'DIAGONALS',
]
