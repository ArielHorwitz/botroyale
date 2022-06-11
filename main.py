from logic.battle import Battle, RandomBot


NUM_OF_BOTS = 2
TURN_CAP = 10


def run_battle():
    bots = make_bots(NUM_OF_BOTS)
    b = Battle(bots)
    for i in range(TURN_CAP):
        print(b.get_map_state())
        b.next_turn()
    print(b.get_map_state())
    print('Game over!')


def make_bots(num_of_bots):
    bots = []
    for i in range(num_of_bots):
        bots.append(RandomBot(i))
    return bots


if __name__ == '__main__':
    run_battle()
