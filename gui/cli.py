HELP_STR = """
=== BOT ROYALE ===
Running in terminal mode (CLI). To use the GUI, disable "gui.cli" setting, or delete your settings file.
Please note that settings are not auto-fixed when using the CLI.

  "help" : Show this message.
  enter  : Next battle step.
  "s"    : Show battle details.
  "#"    : Run # number of steps.
  "c"    : Run the battle to completion.
  "n"    : Start a new battle.
  "q"    : Quit.
"""
nl = '─'*50


class CLI:
    def __init__(self, logic_cls):
        self.logic_cls = logic_cls
        self.battle = self.logic_cls()

    def new_battle(self):
        self.battle = self.logic_cls()
        self.print_battle()

    def print_battle(self):
        print(self.battle.get_match_state())

    def next_step(self, print=True):
        self.battle.next_step()
        if print:
            self.print_battle()

    def play_steps(self, steps):
        for s in range(steps):
            self.battle.next_step()
        self.print_battle()

    def play_complete(self):
        while not self.battle.game_over:
            self.battle.next_step()
        self.print_battle()

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
            else:
                try:
                    steps = int(uinput)
                except ValueError:
                    self.print_help()
                    continue
                self.play_steps(steps)
