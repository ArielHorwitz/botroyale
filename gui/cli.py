from collections import Counter
from api.logging import Logger
from bots import BOTS, BaseBot
from api.time_test import timing_test
from logic.battle_manager import BattleManager


class CLI:
    @staticmethod
    def play_complete(battle):
        battle.play_all(print_progress=True)
        assert battle.state.game_over
        winner_id = battle.state.winner
        winner = battle.bots[winner_id].name if winner_id is not None else 'draw'
        losers = [battle.bots[loser_id].name for loser_id in battle.losers]
        return winner, losers

    @classmethod
    def run_battles(cls):
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
        while True:
            with Logger.set_logging_temp(False):
                battle = BattleManager()
            print_summary()
            print(f'\nPlaying next battle (map: {battle.map_name})...\n')
            winner, losers = cls.play_complete(battle)
            print(battle.get_info_panel_text())
            counter[winner] += 1
            for loser in losers:
                counter[loser] += 0
            battles_played += 1
        print_summary()

    @classmethod
    def timing_test(cls):
        def print_available():
            print('\nAvailable bots:\n'+'\n'.join([f'- {bn}' for bn in available_bots if bn not in selected_names]))
        def print_selected():
            print('\nSelected bots:\n'+'\n'.join(f'++ {bn}' for bn in selected_names))
        def get_bot_name():
            return input('\nEnter bot name to add (leave blank to finish): ')
        available_bots = [bcls.NAME for bcls in BOTS.values() if not bcls.TESTING_ONLY]
        selected_names = []
        print_available()
        bot_name = get_bot_name()
        while bot_name != '':
            if bot_name in BOTS:
                selected_names.append(bot_name)
            print_available()
            print_selected()
            if bot_name not in BOTS:
                print(f'\nNo bot "{bot_name}", try again or leave blank.')
            bot_name = get_bot_name()
        if not selected_names:
            selected_names = available_bots
        print_selected()
        bot_classes = [BOTS[bn] for bn in selected_names]
        ucount = input('\nNumber of battles to play (leave blank for 10,000): ')
        battle_count = int(ucount) if ucount else 10_000
        timing_test(bot_classes, battle_count)

    @classmethod
    def run(cls):
        print('\n'.join([
            '\n\n',
            'Select operation:',
            '1. Winrates',
            '2. Bot timer tests',
            '',
        ]))
        selection = int(input('Enter selection: '))
        assert 1 <= selection <= 2
        if selection == 1:
            cls.run_battles()
        elif selection == 2:
            cls.timing_test()
