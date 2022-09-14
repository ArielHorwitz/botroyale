"""Home of the `botroyale.util.hexagon.Hexagon` class.

The Hexagon represents a whole-number point in hex-space. It can also be
thought of as a whole-number vector from the `ORIGIN` (0, 0, 0) in hex-space.

### Coordinates
See the offset (x, y) coordinates with `Hexagon.xy` and the cube (q, r, s)
coordinates with `Hexagon.cube`.

Hexagons are normally not created manually, rather are returned from methods of
existing hexagons. To create a new Hexagon instance, see `Hexagon.from_xy`,
`Hexagon.from_qr` and `Hexagon.from_floats`.

### Neighboring hexagons
`Hexagon.neighbors` will return a hexagon's 6 nearest neighbors:

```python
import botroyale as br

hex = br.CENTER  # Hexagon(0, 0, 0)
neighbors = hex.neighbors  # tuple of the 6 nearest hexagons
assert hex.neighbors == hex.ring(1)
```

`Hexagon.doubles` and `Hexagon.diagonals` together make up the second ring:
```python
import botroyale as br

hex = br.CENTER  # Hexagon(0, 0, 0)
assert set(hex.ring(2)) == set(hex.doubles) | set(hex.diagonals)
```

### Distance
To find the hex-wise distance between two hexagons, use `Hexagon.get_distance`:
```python
import botroyale as br

hex = br.Hexagon.from_xy(5, -6)
distance_from_center = hex.get_distance(br.CENTER)  # 8 tiles distance
```

### Range
To find all hexagons *within* a certain distance, use `Hexagon.range`:
```python
import botroyale as br

hex = br.CENTER  # Hexagon(0, 0, 0)
tiles_in_range = hex.range(3)  # tuple of the 37 hexagons within 3 distance
```

### Ring
To find all hexagon *at exactly* a certain distance, use `Hexagon.ring`:
```python
import botroyale as br

hex = br.CENTER  # Hexagon(0, 0, 0)
tiles_in_ring = hex.ring(3)  # tuple of the 18 hexagons at exactly 3 distance
```

### Straight line
To find hexagons in a straight line, use `Hexagon.straight_line`:
```python
import botroyale as br

hex = br.CENTER  # Hexagon(0, 0, 0)
neighbor = hex.neighbors[0]  # A neighbor of hex

# The first hex that continues the line from hex to neighbor
next_in_line = next(hex.straight_line(neighbor))

# Iterating through hexagons in a straight line
for hex_in_line in hex.straight_line(neighbor):
    ...
```

### Rotation
To find a hexagon from rotation, use `Hexagon.rotate`:
```python
import botroyale as br

hex = br.Hexagon.from_xy(-2, 18)
mirrored_hex = hex.rotate(3)  # the hex on the opposite side of the origin
```

### Operators
Hexagons are also vectors, and can be added and subtracted:
```python
import botroyale as br

hex1 = br.Hexagon.from_qr(1, 2)
hex2 = br.Hexagon.from_qr(-1, -2)
center = hex1 - hex2  # equivalent to br.CENTER
```
"""
from typing import Sequence, Generator
import math
import functools


SQRT3 = math.sqrt(3)
WIDTH_HEIGHT_RATIO = SQRT3 / 2
GRID_OFFSET = -1


class Hexagon:
    """See module documentation for details."""

    def __init__(self, q: int, r: int, s: int):
        """Initialize the class.

        The arguments "q", "r", and "s" are components of the cube coordinates.
        """
        self.__cube: tuple[int, int, int] = (q, r, s)
        assert all(isinstance(c, int) for c in self.__cube)
        assert sum(self.__cube) == 0
        self.__offset: tuple[int, int] = convert_cube2offset(q, r, s)

    @functools.cache
    def get_distance(self, hex: "Hexagon") -> int:
        """Number of steps (to a neighbor hex) required to reach hex from self."""
        delta = self - hex
        return max(abs(c) for c in delta.cube)

    def straight_line(
        self, neighbor: "Hexagon", max_distance: int = 20
    ) -> Generator["Hexagon", None, None]:
        """Returns a generator that yields the hexes following a straight line.

        The line intersects self and neighbor. Generator values do not include
        self or neighbor. *max_distance* determines how many values to generate.
        """
        assert neighbor in self.neighbors
        dir = neighbor - self
        counter = 0
        while counter < max_distance:
            counter += 1
            neighbor += dir
            yield neighbor

    @functools.cache
    def ring(self, radius: int) -> tuple["Hexagon", ...]:
        """Returns a tuple of hexes that are `radius` distance from self.

        The resulting hexes are always in the same order, with regards to their
        relative position from self.
        """
        if radius < 0:
            raise ValueError(f"Radius must be non-negative, got: {radius}")
        if radius == 0:
            return (self,)
        if radius == 1:
            return self.neighbors
        ring = []
        dir_ngbr = self + DIRECTIONS[4]
        hex = list(self.straight_line(dir_ngbr, max_distance=radius - 1))[-1]
        for i in range(6):
            for _ in range(radius):
                ring.append(hex)
                hex = hex + DIRECTIONS[i]
        return tuple(ring)

    @functools.cache
    def range(
        self, distance: int, include_center: bool = True
    ) -> tuple["Hexagon", ...]:
        """Returns a tuple of all the hexes within a distance from self.

        The resulting hexes are always in the same order, with regards to their
        relative position from self.

        include_center      -- include self in the results
        """
        results = []
        for q in range(-distance, distance + 1):
            for r in range(
                max(-distance, -q - distance), min(+distance, -q + distance) + 1
            ):
                s = -q - r
                results.append(self + Hexagon(q, r, s))
        if not include_center:
            results.remove(self)
        return tuple(results)

    @functools.cache
    def rotate(self, rotations: int = 1) -> "Hexagon":
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
    def neighbors(self) -> tuple["Hexagon", ...]:
        """The 6 adjascent hexes.

        The resulting hexes are always in the same order, with regards to their
        relative position from *self*.
        """
        return _get_neighbors(self)

    @property
    def doubles(self) -> tuple["Hexagon", ...]:
        """The 6 hexes that are 2 distance away and not diagonals.

        These resulting hexes can be found on a straight line originating from
        *self*, and are always in the same order with regards to their relative
        position from *self*.

        Doubles and diagonals are complementary parts of `Hexagon.ring` with
        `radius=2`.
        """
        return _get_doubles(self)

    @property
    def diagonals(self) -> tuple["Hexagon", ...]:
        """The 6 hexes that are 2 distance away and are diagonals.

        These resulting hexes cannot be found on a straight line originating
        from *self*, and are always in the same order with regards to their
        relative position from *self*.

        Doubles and diagonals are complementary parts of `Hexagon.ring` with
        `radius=2`.
        """
        return _get_diagonals(self)

    # Operations
    def __add__(self, other: "Hexagon") -> "Hexagon":
        """Cube addition of hexagons. Can be used like vectors."""
        if not isinstance(other, type(self)):
            raise ValueError(f"Cannot add {type(other)} with {type(self)}")
        return Hexagon(self.q + other.q, self.r + other.r, self.s + other.s)

    def __sub__(self, other: "Hexagon") -> "Hexagon":
        """Cube subtraction of hexagons. Can be used like vectors."""
        if not isinstance(other, type(self)):
            raise ValueError(f"Cannot subtract {type(other)} with {type(self)}")
        return Hexagon(self.q - other.q, self.r - other.r, self.s - other.s)

    def __eq__(self, other: "Hexagon") -> bool:
        """Returns if self and other share coordinates."""
        if not isinstance(other, type(self)):
            return False
        return self.cube == other.cube

    @classmethod
    def round_(cls, fq: float, fr: float, fs: float) -> "Hexagon":
        """Takes floating point cube coordinates and returns the nearest hex."""
        q = round(fq)
        r = round(fr)
        s = round(fs)
        dq = abs(q - fq)
        dr = abs(r - fr)
        ds = abs(s - fs)
        if dq > dr and dq > ds:
            q = -r - s
        elif dr > ds:
            r = -q - s
        else:
            s = -q - r
        return cls(q, r, s)

    # Position in 2D space
    @functools.cache
    def pixel_position(self, radius: int) -> tuple[int, int]:
        """Position in pixels of self, given the radius of a hexagon in pixels."""
        offset_r = (self.y % 2 == 1) / 2
        x = radius * SQRT3 * (self.x + offset_r)
        y = radius * 3 / 2 * self.y
        return x, y

    @functools.cache
    def pixel_position_to_hex(
        self, radius: int, pixel_coords: Sequence[float]
    ) -> "Hexagon":
        """The hex at position `pixel_coords` offset from self."""
        x, y = pixel_coords[0] / radius, pixel_coords[1] / radius
        q = (SQRT3 / 3 * x) + (-1 / 3 * y)
        r = 2 / 3 * y
        offset = self.round_(q, r, -q - r)
        return offset - self

    # Constructors
    @classmethod
    def from_xy(cls, x: int, y: int) -> "Hexagon":
        """Return the `Hexagon` given the offset (x, y) coordinates."""
        return cls(*convert_offset2cube(x, y))

    @classmethod
    def from_qr(cls, q: int, r: int) -> "Hexagon":
        """Return the `Hexagon` given the partial cube coordinates (q, r)."""
        s = -q - r
        return cls(q, r, s)

    @classmethod
    def from_floats(cls, q: float, r: float, s: float) -> "Hexagon":
        """Alias for `Hexagon.round_`."""
        return cls.round_(q, r, s)

    # Representations
    @property
    def x(self) -> int:
        """X component of the offset (x, y) coordinates."""
        return self.__offset[0]

    @property
    def y(self) -> int:
        """Y component of the offset (x, y) coordinates."""
        return self.__offset[1]

    @property
    def xy(self) -> tuple[int, int]:
        """Offset coordinates."""
        return self.__offset

    @property
    def q(self) -> int:
        """Q component of the cube (q, r, s) coordinates."""
        return self.__cube[0]

    @property
    def r(self) -> int:
        """R component of the cube (q, r, s) coordinates."""
        return self.__cube[1]

    @property
    def s(self) -> int:
        """S component of the cube (q, r, s) coordinates."""
        return self.__cube[2]

    @property
    def qr(self) -> tuple[int, int]:
        """Q and R components of the cube (q, r, s) coordinates."""
        return self.__cube[:2]

    @property
    def cube(self) -> tuple[int, int, int]:
        """Cube (q, r, s) coordinates."""
        return self.__cube

    def __repr__(self):
        """Repr."""
        return f"<Hex {self.x}, {self.y}>"

    def __hash__(self):
        """Hash."""
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
"""The origin of the coordinate system.

(0, 0, 0) in cube coordinates and (0, 0) in offset coordinates."""
DIRECTIONS: tuple[Hexagon, ...] = (
    Hexagon(1, 0, -1),
    Hexagon(1, -1, 0),
    Hexagon(0, -1, 1),
    Hexagon(-1, 0, 1),
    Hexagon(-1, 1, 0),
    Hexagon(0, 1, -1),
)
"""The 6 adjascent hexes to `ORIGIN`.

Can be considered the 6 directional normal vectors in hex-space."""
DOUBLES: tuple[Hexagon, ...] = (
    Hexagon(2, 0, -2),
    Hexagon(2, -2, 0),
    Hexagon(0, -2, 2),
    Hexagon(-2, 0, 2),
    Hexagon(-2, 2, 0),
    Hexagon(0, 2, -2),
)
"""The doubles.

6 hexes that are 2 distance away and can be found on a straight line originating
from `ORIGIN`."""
DIAGONALS: tuple[Hexagon, ...] = (
    Hexagon(2, -1, -1),
    Hexagon(1, -2, 1),
    Hexagon(-1, -1, 2),
    Hexagon(-2, 1, 1),
    Hexagon(-1, 2, -1),
    Hexagon(1, 1, -2),
)
"""The diagonals.

6 hexes that are 2 distance away and cannot be found on a straight line
originating from `ORIGIN`."""


# Alias for xy constructor
Hex = Hexagon.from_xy


__all__ = [
    "Hexagon",
    "Hex",
    "ORIGIN",
    "DIRECTIONS",
    "DOUBLES",
    "DIAGONALS",
]
