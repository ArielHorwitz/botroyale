from util.hexagon import _Hex


class Move:
    ap = 10

    def __init__(self, target_tile):
        assert isinstance(target_tile, _Hex)
        self.target = target_tile


class Push(Move):
    ap = 30


