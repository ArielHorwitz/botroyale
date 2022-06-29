from util.hexagon import is_hex


class Move:
    ap = 10

    def __init__(self, target_tile):
        assert is_hex(target_tile)
        self.target = target_tile


class Push(Move):
    ap = 30


class IllegalAction:
    ap = 0
