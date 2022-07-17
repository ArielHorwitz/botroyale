from collections import Counter
import numpy as np
from api.logging import logger
from logic.maps import SELECTED_MAP_NAME


HELP_STR = """
=== BOT ROYALE ===
Running in terminal mode (CLI). To use the GUI, disable "gui.cli" setting, or delete your settings file.
Please note that settings are not auto-fixed when using the CLI.

  "help" : Show this message.
  enter  : Next battle step.
  "s"    : Show battle details.
  "#"    : Run # number of steps.
  "c"    : Run the battle to completion.
  "r #"  : Run # of battles and get winrates.
  "n"    : Start a new battle.
  "q"    : Quit.
"""
nl = '─'*50


class CLI:
    def __init__(self, logic_cls):
        self.logic_cls = logic_cls
        self.battle = self.logic_cls()

    def new_battle(self, do_print=True):
        self.battle = self.logic_cls()
        if do_print:
            self.print_battle()

    def print_battle(self):
        print(self.battle.get_match_state())

    def next_step(self, do_print=True):
        self.battle.next_step()
        if do_print:
            self.print_battle()

    def play_steps(self, steps):
        for s in range(steps):
            self.battle.next_step()
        self.print_battle()

    def play_complete(self):
        while not self.battle.game_over:
            self.battle.next_step()
        self.print_battle()
        alive = np.flatnonzero(self.battle.alive_mask)
        if len(alive):
            winner_id = alive[0]
            winner = self.battle.bots[winner_id].name
            losers = [b.name for b in self.battle.bots if b.id != winner_id]
        else:
            losers = [b.name for b in self.battle.bots]
            winner = 'draw'
        return winner, losers

    def run_battles(self, count):
        def print_summary():
            print(f'\n\n          Total Winrates (played {i} / {count} games)')
            print(f'            MAP: {SELECTED_MAP_NAME}\n')
            if i <= 0:
                return
            for bot, wins in counter.most_common():
                print(f'{bot:>20}: {f"{wins/i*100:.2f}":>7} % ({str(wins):<4} wins)')

        logging_enabled_default = logger.enable_logging
        logger.enable_logging = False
        counter = Counter()
        for i in range(count):
            self.new_battle(do_print=False)
            print_summary()
            print('\nPlaying next battle...\n')
            winner, losers = self.play_complete()
            last_battle_summary = self.battle.get_match_state()
            counter[winner] += 1
            for loser in losers:
                counter[loser] += 0
        i += 1
        print_summary()
        logger.enable_logging = logging_enabled_default

    def print_help(self):
        print(HELP_STR)

    def get_uinput(self):
        print(f'\n{nl}')
        uinput = input(f'Bot Royale (try "help") >> ')
        print(f'{nl}\n')
        return uinput

    def run(self):
        uinput = ''
        self.print_help()
        while uinput != 'q':
            uinput = self.get_uinput()
            if uinput == 'help':
                self.print_help()
            elif uinput == 'n':
                self.new_battle()
            elif uinput == 's':
                self.print_battle()
            elif uinput == '':
                self.next_step()
            elif uinput == 'c':
                self.play_complete()
            elif uinput.startswith('r '):
                count = int(uinput[2:])
                self.run_battles(count)
            else:
                try:
                    steps = int(uinput)
                except ValueError:
                    self.print_help()
                    continue
                self.play_steps(steps)
