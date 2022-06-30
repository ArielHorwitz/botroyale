from util.hexagon import is_hex


class Action:
    ap = 0
    has_effect = True


class Move(Action):
    ap = 10

    def __init__(self, target_tile):
        assert is_hex(target_tile)
        self.target = target_tile


class Push(Move):
    ap = 30


class Idle(Action):
    has_effect = False


class IllegalAction(Action):
    has_effect = False
