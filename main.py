
from logic.battle import Battle


def run_battle():
    b = Battle()
    while not b.game_over:
        b.next_turn()
        print(b.get_map_state())
    print(b.get_map_state())
    print('Game over!')


if __name__ == '__main__':
    run_battle()
