from collections import namedtuple, defaultdict


class _Hex:
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

    @property
    def neighbors(self):
        if self.__neighbors is None:
            self.__neighbors = tuple((self + dir).xy for dir in DIRECTIONS)
        return tuple(Hex(x, y) for x, y in self.__neighbors)

    # Internal calculations
    def __eq__(self, tile):
        return all((self.q==tile.q, self.r==tile.r, self.s==tile.s))

    def __add__(self, tile):
        return self.__class__(self.q+tile.q, self.r+tile.r, self.s+tile.s)

    def __sub__(self, tile):
        return self.__class__(self.q-tile.q, self.r-tile.r, self.s-tile.s)

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

    def __repr__(self):
        return f'<Hex {self.x}, {self.y}>'

    def __hash__(self):
        return hash(self.__cube)


DIRECTIONS = [
    _Hex(+1, 0, -1),
    _Hex(+1, -1, 0),
    _Hex(0, -1, +1),
    _Hex(-1, 0, +1),
    _Hex(-1, +1, 0),
    _Hex(0, +1, -1),
    ]
ALL_HEXES = {}


def Hex(x, y):
    xy = x, y
    if xy in ALL_HEXES:
        return ALL_HEXES[xy]
    q, r, s = _Hex._convert_offset2cube(x, y)
    new_hex = _Hex(q, r, s)
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