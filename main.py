print('Welcome to Bot Royale.')

from util.settings import Settings
from api.logic import BaseLogicAPI
from logic.battle import Battle


RUN_CLI = Settings.get('gui.|cli', False)
LOGIC_CLS = BaseLogicAPI if Settings.get('||api.use_base_logic_api', False) else Battle


def run_gui():
    from gui.gui import App
    app = App(logic_cls=LOGIC_CLS)
    # We write settings to file after completing startup, after all parts
    # of the program have had a chance to set their defaults.
    Settings.write_to_file()
    app.run()


def run_cli():
    from gui.cli import CLI
    CLI(LOGIC_CLS).run()


if __name__ == '__main__':
    run_cli() if RUN_CLI else run_gui()
