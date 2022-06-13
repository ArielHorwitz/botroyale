from logic.battle import Battle


def run_battle():
    b = Battle()
    while not b.game_over:
        print(b.get_map_state())
        b.next_turn()
    print(b.get_map_state())
    print('Game over!')


if __name__ == '__main__':
    run_battle()
