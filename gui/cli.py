from collections import Counter
from api.logging import logger
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
    def run(cls):
        cls.run_battles()
