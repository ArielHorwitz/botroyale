print('Welcome to Bot Royale.')

from util.settings import Settings
from api.logic import BaseLogicAPI
from logic.battle import Battle
from gui.gui import App


LOGIC_API = BaseLogicAPI if Settings.get('|api.use_base_logic_api', False) else Battle


def run():
    logic = LOGIC_API()
    app = App(logic_api=logic)
    Settings.write_to_file()
    app.run()


if __name__ == '__main__':
    run()
