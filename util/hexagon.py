from collections import namedtuple


Cube = namedtuple('CubeRepr', ['q', 'r', 's'])
Axial = namedtuple('XY', ['x', 'y'])
CUBE_DIRECTIONS = [
    Cube(+1, 0, -1),
    Cube(+1, -1, 0),
    Cube(0, -1, +1),
    Cube(-1, 0, +1),
    Cube(-1, +1, 0),
    Cube(0, +1, -1),
    ]


def get_neighbors(tile): # tile = (x,y) or Axial object
    tile = _convert_to_cube(tile)
    neighbors = []
    for dir in CUBE_DIRECTIONS:
        neighbor = _cube_add(tile, dir)
        neighbors.append(_convert_to_axial(neighbor))
    return neighbors


def get_distance(tile1, tile2):
    tile1 = _convert_to_cube(tile1)
    tile2 = _convert_to_cube(tile2)
    new_tile = _cube_subtract(tile1, tile2)
    return max(abs(new_tile.q), abs(new_tile.s), abs(new_tile.r))


def _cube_add(tile1, tile2):
    return Cube(
        q=tile1.q + tile2.q,
        r=tile1.r + tile2.r,
        s=tile1.s + tile2.s
        )


def _cube_subtract(tile1, tile2):
    return Cube(
        q=tile1.q - tile2.q,
        r=tile1.r - tile2.r,
        s=tile1.s - tile2.s
        )


def _convert_to_cube(axial_tile):
    s = -axial_tile[0] - axial_tile[1]
    return Cube(q=axial_tile[0], r=axial_tile[1], s=s)


def _convert_to_axial(cube_tile):
    return Axial(cube_tile[0], cube_tile[1])


if __name__ == '__main__':
    print(get_distance((3, -3), (-3, 2)))
    for i in get_neighbors((2, 2)):
        print(i)
