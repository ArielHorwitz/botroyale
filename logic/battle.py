

class Battle:
    def next_turn(self):
        pass

    def get_map_state(self):
        return f'{self}.get_map_state() not implemented.'

    @property
    def game_over(self):
        return True
