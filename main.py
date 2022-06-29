print('Welcome to Bot Royale.')

from util.settings import Settings
from logic.battle import Battle
from gui.gui import App


def run():
    logic = Battle()
    app = App(logic_api=logic)
    Settings.write_to_file()
    app.run()


if __name__ == '__main__':
    run()
