from logic.game import GameAPI
from util.settings import Settings
from gui.app import App


def run():
    app = App(game_api=GameAPI())
    # We write settings to file after completing startup, after all parts
    # of the program have had a chance to set their defaults.
    Settings.write_to_file()
    app.run()
