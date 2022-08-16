from collections import Counter
from api.time_test import timing_test
from logic.maps import MAPS, get_map_state
from logic.battle_manager import BattleManager
from bots import BOTS, bot_getter


# Thresholds of bot calculation times for the competitive timing test
COMP_SAMPLE_SIZE = 10
COMP_MAX_MS = 10_000
COMP_MEAN_MS = 5_000
COMP_FAIL_CONDITIONS = f'Fail conditions: mean > {COMP_MEAN_MS:,} ms ; max > {COMP_MAX_MS:,} ms'


def run_competitive_timing_test():
    """Runs the competitive timing test. Prints the names of the bots that fail
    the test."""
    bot_classes = query_bot_classes()
    results = timing_test(
        bots=bot_classes,
        battle_count=COMP_SAMPLE_SIZE,
        verbose_results=False,
        shuffle_bots=True,
        disable_logging=True,
        )
    fail_mean = [bn for bn, tr in results.items() if tr.mean > COMP_MEAN_MS]
    fail_max = [bn for bn, tr in results.items() if tr.max > COMP_MAX_MS]
    fail_names = set(fail_max) | set(fail_mean)
    print(f'\n\n{COMP_FAIL_CONDITIONS}\n')
    if fail_names:
        fail_names_str = '\n'.join(f'- {f}' for f in fail_names)
        print(f'FAILED:\n{fail_names_str}')
    else:
        print('No fails.')
    print('\n')


def run_regular_timing_test():
    """Runs a timing test. Continuously prints the results (mean and max
    calculation time) of each bot."""
    ucount = input('\nNumber of battles to play (leave blank for 10,000): ')
    battle_count = int(ucount) if ucount else 10_000
    bot_classes = query_bot_classes()
    timing_test(bot_classes, battle_count)


def run_winrates():
    """Plays many battles, and continuously prints the winrates of each bot."""
    def print_summary():
        print('\n')
        print(f'           ----------------------------------')
        print(f'               Winrates ({battles_played:,} battles total)')
        print(f'           ----------------------------------')
        if battles_played <= 0:
            print(f'Waiting for results of the first game...')
            return
        for bot, wins in counter.most_common():
            print(f'{bot:>20}: {f"{wins/battles_played*100:.2f}":>7} % ({str(wins):<4} wins)')

    counter = Counter()
    battles_played = 0
    initial_state = get_map_state(query_map_name())
    bot_selection = [b.NAME for b in query_bot_classes()]
    get_bots = bot_getter(
        selection=bot_selection,
        all_play=True,
        include_testing=True,
        )
    while True:
        battle = BattleManager(
            initial_state=initial_state,
            bot_classes_getter=get_bots,
            enable_logging=False)
        print_summary()
        print(f'\nPlaying next battle (map: {battle.map_name})...\n')
        winner, losers = play_complete(battle)
        print(battle.get_info_panel_text())
        counter[winner] += 1
        for loser in losers:
            counter[loser] += 0
        battles_played += 1
    print_summary()


def query_map_name() -> str:
    """Queries the user in console for a map name."""
    maps = MAPS
    print('\n'.join([
        f'Available maps:',
        *(f'- {i}. {m}' for i, m in enumerate(maps)),
        ]))
    map = input('Select map: ')
    while True:
        if map in MAPS:
            break
        try:
            idx = int(map)
            assert 0 <= idx < len(MAPS)
        except ValueError:
            print(f'"{map}" is not an option.')
            continue
        map = maps[idx]
    print(f'Selected: {map}')
    return map


def query_bot_classes() -> list[type]:
    """Queries the user in console for bots. Returns a list of bot classes."""
    def query_user():
        names = []
        for i, bn in enumerate(available_bots):
            in_prefix = '++' if bn in selected_names else '--'
            names.append(f'{str(i):>3}. {in_prefix} {bn}')
            names_str = '\n'.join(names)
        print(f'Bots:\nLegend: -- available ++ selected')
        print(names_str)
        # print('Enter one of the following:')
        print('\nBot selection:')
        print('>  leave blank to finish')
        print('>  number to add/remove a bot by number')
        print('>  "a" to add all bots')
        print('>  "r" to remove all bots')
        r = input('>> ')
        print('')
        return r

    bot_cls_list = [bot_cls for bot_cls in BOTS.values()]
    sorted_bots = sorted(bot_cls_list, key=lambda botcls: botcls.TESTING_ONLY)
    available_bots = [bot_cls.NAME for bot_cls in sorted_bots]
    selected_names = []

    # Collect bots
    while True:
        uinput = query_user()
        if uinput == '':
            break
        if uinput == 'a':  # Add all
            selected_names = [a for a in available_bots]
            continue
        if uinput == 'r':  # Remove all
            selected_names = []
            continue
        # Convert to index
        try:
            bot_index = int(uinput)
            bot_name = available_bots[bot_index]
        except (ValueError, IndexError):
            continue
        # Add/remove index
        if bot_name not in selected_names:
            selected_names.append(bot_name)
        else:
            selected_names.remove(bot_name)

    # Fill with all bots if none selected
    if not selected_names:
        selected_names = available_bots
    bot_classes = [BOTS[bn] for bn in selected_names]
    return bot_classes


def play_complete(battle: BattleManager) -> tuple[str, list[str]]:
    """Plays a battle to completion and returns a winner name and a list of
    losers' names."""
    battle.play_all(print_progress=True)
    assert battle.state.game_over
    winner_id = battle.state.winner
    winner = battle.bots[winner_id].name if winner_id is not None else 'draw'
    losers = [battle.bots[loser_id].name for loser_id in battle.losers]
    return winner, losers


def run():
    while True:
        print('\n'.join([
            '\n\n',
            'Select operation:',
            '1. Winrates',
            '2. Bot timer tests',
            '3. Bot timer tests for competition',
            'q. Quit CLI',
            '',
        ]))
        selection = input('Enter selection: ')
        if selection == 'q':
            return
        selection = int(selection)
        assert 1 <= selection <= 3
        if selection == 1:
            run_winrates()
        elif selection == 2:
            run_regular_timing_test()
        elif selection == 3:
            run_competitive_timing_test()
