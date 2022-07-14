from util.hexagon import is_hex


class Action:
    ap = 0
    has_effect = True


class Move(Action):
    ap = 10

    def __init__(self, target_tile):
        assert is_hex(target_tile)
        self.target = target_tile

    def __repr__(self):
        return f'<Move action: {self.target.x}, {self.target.y}>'


class Push(Move):
    ap = 30

    def __repr__(self):
        return f'<Push action: {self.target.x}, {self.target.y}>'


class Idle(Action):
    has_effect = False

    def __repr__(self):
        return f'<Idle action>'


class IllegalAction(Action):
    has_effect = False

    def __repr__(self):
        return f'<Illegal action>'
