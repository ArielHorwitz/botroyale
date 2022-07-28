from collections import Counter
from api.logging import logger
from bots import BOTS, BaseBot
from api.time_test import timing_test
from logic.battle_manager import BattleManager


class CLI:
    @staticmethod
    def play_complete(battle):
        battle.play_all()
        assert battle.state.game_over
        winner_id = battle.state.winner
        winner = battle.bots[winner_id].name if winner_id is not None else 'draw'
        losers = [b.name for b in battle.losers]
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

        logging_enabled_default = logger.enable_logging
        logger.enable_logging = False
        counter = Counter()
        battles_played = 0
        last_battle_summary = ''
        while True:
            battle = BattleManager()
            print('-'*75)
            print(last_battle_summary)
            print_summary()
            print(f'\nPlaying next battle (map: {battle.map_name})...\n')
            winner, losers = cls.play_complete(battle)
            last_battle_summary = battle.get_info_panel_text()
            counter[winner] += 1
            for loser in losers:
                counter[loser] += 0
            battles_played += 1
        print_summary()
        logger.enable_logging = logging_enabled_default

    @classmethod
    def timing_test(cls):
        def print_available():
            print('\nAvailable bots:\n'+'\n'.join([f'- {bn}' for bn in available_bots if bn not in selected_names]))
        def print_selected():
            print('\nSelected bots:\n'+'\n'.join(f'- {bn}' for bn in selected_names))
        def get_bot_name():
            return input('\nEnter bot name to add (or leave blank to finish): ')
        available_bots = [bn for bn, bc in BOTS.items() if bn != 'dummy' and not bc.TESTING_ONLY]
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
        battle_count = int(input('\nEnter number of battles to play: '))
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
