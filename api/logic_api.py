import numpy as np

RNG = np.random.default_rng()
MAX_TURNS = 1000
UNIT_COUNT = 10
AXIS_SIZE = 15


class BaseLogicAPI:
    # map_size is a 2-tuple of integers (width, height)
    map_size = AXIS_SIZE, AXIS_SIZE

    # This
    turn_count = 0

    # Positions is a sequence of 2D coordinates (a 2-sequence)
    positions = [[0, 0], [1, 1]]
    walls = RNG.integers(low=0, high=AXIS_SIZE, size=(20, 2))
    pits = RNG.integers(low=0, high=AXIS_SIZE, size=(20, 2))

    def next_turn(self):
        """This method is called when a single turn is to be played."""
        self.turn_count += 1
        self.positions = RNG.integers(low=0, high=AXIS_SIZE, size=(UNIT_COUNT, 2))

    @property
    def game_over(self):
        """This property returns a boolean if there are any more turns to play."""
        return self.turn_count >= MAX_TURNS

    def get_map_state(self):
        """This method returns an arbritrary string to be displayed in the GUI."""
        game_over = 'GAME OVER' if self.game_over else ''
        return f'Turn: {self.turn_count}\n{game_over}'
