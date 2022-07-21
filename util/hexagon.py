import math
from collections import namedtuple, defaultdict


SQRT3 = math.sqrt(3)
WIDTH_HEIGHT_RATIO = SQRT3 / 2


class Hexagon:
    OFFSET = -1

    def __init__(self, q, r, s):
        self.__cube = (q, r, s)
        self.__offset = self._convert_cube2offset(q, r, s)
        self.__neighbors = None

    # API
    def get_distance(self, tile):
        delta = self - tile
        return max(abs(c) for c in delta.cube)

    def straight_line(self, neighbor, max_distance=20):
        assert neighbor in self.neighbors
        counter = 0
        delta = neighbor - self
        while counter < max_distance:
            counter += 1
            neighbor += delta
            yield neighbor

    def ring(self, radius):
        if radius < 0:
            raise ValueError(f'Radius must be non-negative, got: {radius}')
        if radius == 0:
            return [self]
        if radius == 1:
            return list(self.neighbors)
        ring = []
        dir = DIRECTIONS[4]
        hex = list(self.straight_line(self+dir, max_distance=radius-1))[-1]
        for i in range(6):
            for _ in range(radius):
                ring.append(hex)
                hex = hex + DIRECTIONS[i]
        return ring

    def rotate(self, rotations=1):
        """Return the hex given by rotating our position about the origin (0, 0)
        by 60° per rotation."""
        hex = self
        assert isinstance(rotations, int)
        if rotations > 0:
            while rotations > 0:
                hex = Hex(*self._convert_cube2offset(-hex.r, -hex.s, -hex.q))
                rotations -= 1
        elif rotations < 0:
            while rotations < 0:
                hex = Hex(*self._convert_cube2offset(-hex.s, -hex.q, -hex.r))
                rotations += 1
        return hex

    def range(self, distance):
        """Returns all the hexes within distance from our position."""
        results = []
        for q in range(-distance, distance+1):
            for r in range(max(-distance, -q-distance), min(+distance, -q+distance)+1):
                s = -q-r
                results.append(self + Hexagon(q, r, s))
        return results

    @property
    def neighbors(self):
        if self.__neighbors is None:
            self.__neighbors = tuple(self + dir for dir in DIRECTIONS)
        return self.__neighbors

    # Internal calculations
    def __eq__(self, tile):
        return all((self.q==tile.q, self.r==tile.r, self.s==tile.s))

    def __add__(self, tile):
        return Hex(*self._convert_cube2offset(self.q+tile.q, self.r+tile.r, self.s+tile.s))

    def __sub__(self, tile):
        return Hex(*self._convert_cube2offset(self.q-tile.q, self.r-tile.r, self.s-tile.s))

    # Converters
    @classmethod
    def _convert_offset2cube(cls, x, y):
        q = x - (y + cls.OFFSET * (y & 1)) // 2
        r = y
        s = -q - r
        return q, r, s

    @classmethod
    def _convert_cube2offset(cls, q, r, s):
        col = q + (r + cls.OFFSET * (r & 1)) // 2
        row = r
        return col, row

    def pixel_position(self, radius):
        """My position in pixels, given a radius of `radius` pixels."""
        offset_r = (self.y % 2 == 1) / 2
        x = radius * SQRT3 * (self.x + offset_r)
        y = radius * 3/2 * self.y
        return x, y

    def pixel_position_to_hex(self, radius, pixel_coords):
        """
        The hex at position `pixel_coords` assuming self is centered at
        position 0, 0.
        """
        x, y = pixel_coords[0] / radius, pixel_coords[1] / radius
        q = (SQRT3/3 * x) + (-1/3 * y)
        r = 2/3 * y
        offset = self._round(q, r, -q-r)
        return offset - self

    @classmethod
    def _round(cls, q_, r_, s_):
        q = round(q_)
        r = round(r_)
        s = round(s_)
        qdiff = abs(q - q_)
        rdiff = abs(r - r_)
        sdiff = abs(s - s_)
        if qdiff > rdiff and qdiff > sdiff:
            q = -r-s
        elif rdiff > sdiff:
            r = -q-s
        else:
            s = -q-r
        return Hex(*cls._convert_cube2offset(q, r, s))

    # Representations
    @property
    def x(self):
        return self.__offset[0]

    @property
    def y(self):
        return self.__offset[1]

    @property
    def xy(self):
        return self.__offset

    @property
    def q(self):
        return self.__cube[0]

    @property
    def r(self):
        return self.__cube[1]

    @property
    def s(self):
        return self.__cube[2]

    @property
    def cube(self):
        return self.__cube

    def __str__(self):
        return f'<Hex {self.x}, {self.y}>'

    def __repr__(self):
        copy_str = ''
        if self.xy not in ALL_HEXES or self is not Hex(*self.xy):
            copy_str = ' copy'
        return f'<Hex {self.x}, {self.y}{copy_str}>'

    def __hash__(self):
        return hash(self.__cube)


# Do not change the order of Directions!
DIRECTIONS = (
    Hexagon(+1, 0, -1),
    Hexagon(+1, -1, 0),
    Hexagon(0, -1, +1),
    Hexagon(-1, 0, +1),
    Hexagon(-1, +1, 0),
    Hexagon(0, +1, -1),
    )
DIAGONALS = (
    Hexagon(2, -1, -1),
    Hexagon(1, -2, 1),
    Hexagon(-1, -1, 2),
    Hexagon(-2, 1, 1),
    Hexagon(-1, 2, -1),
    Hexagon(1, 1, -2),
)
ALL_HEXES = {}


def is_hex(h):
    """
    Checks that an object is one of the Hexagon singletons (ALL_HEXES).
    This should work as long as the object was retrieved normally.

    To ensure objects pass this check, they must be retrieved using the Hex()
    function, or using the methods and operations available normally in the
    Hexagon class.

    Hexagons created manually (initializing the class directly) or using
    deepcopy will fail this check.
    """
    if not isinstance(h, Hexagon):
        return False
    if h is not ALL_HEXES[h.xy]:
        raise ValueError(f'Found a Hexagon object that is not the singleton. Consult hexagon.is_hex().')
    return True


def Hex(x, y):
    xy = x, y
    if xy in ALL_HEXES:
        return ALL_HEXES[xy]
    q, r, s = Hexagon._convert_offset2cube(x, y)
    new_hex = Hexagon(q, r, s)
    ALL_HEXES[xy] = new_hex
    return new_hex


# Hex example usage
if __name__ == '__main__':
    tile1 = Hex(1, 1)
    tile2 = Hex(1, 2)
    tile3 = Hex(1, 2)
    print('=== Coordinates')
    print(f'{tile1} xy: {tile1.xy}')
    print(f'{tile2} x, y: {tile2.x}, {tile2.y}')
    print('=== Neighbors')
    print(f'{tile1} neighbors: {tile1.neighbors}')
    print('=== Operations')
    print(f'{tile2} in {tile1} neighbors: {tile2 in tile1.neighbors}')
    print(f'{tile1} is {tile2}: {tile1 is tile2}')
    print(f'{tile2} == {tile3}: {tile2 == tile3}')
    print(f'{tile2} is {tile3}: {tile2 is tile3}')
    print('=== Distances')
    print(f'Distance {tile1} -> {tile2}: {tile1.get_distance(tile2)}')
    print('=== Straight lines')
    dir = tile2 - tile1
    tile4 = tile2 + dir
    print(f'Straight line from {tile1} -> {tile2} : {tile4}')
    hex_set = {tile1, tile2, tile3, tile4}
    print('=== Sets and containment')
    print(f'Set: {hex_set}')
    print(f'{tile1} in {hex_set} : {tile1 in hex_set}')
    print('=== Pixel offset')
    print(f'{tile2} pixels w/ 50 radius: {tile1.pixels(radius=50)}')
    print(f'{tile1} pixels w/ 22 radius: {tile1.pixels(radius=22)}')
    print(f'{tile4} pixels w/ 80 radius: {tile1.pixels(radius=80)}')
