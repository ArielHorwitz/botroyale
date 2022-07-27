from util.hexagon import is_hex


class Action:
    ap = 0


class Move(Action):
    ap = 20

    def __init__(self, target_tile):
        assert is_hex(target_tile)
        self.target = target_tile

    def __repr__(self):
        return f'<Move: {self.target.x}, {self.target.y}>'


class Push(Move):
    ap = 30

    def __repr__(self):
        return f'<Push: {self.target.x}, {self.target.y}>'


class Jump(Move):
    ap = 45

    def __repr__(self):
        return f'<Jump: {self.target.x}, {self.target.y}>'


class Idle(Action):

    def __repr__(self):
        return f'<Idle>'


ALL_ACTIONS = (Idle, Move, Push, Jump)
