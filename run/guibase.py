from api.gui import GameAPI
from util.settings import Settings
from gui.app import App


def run():
    app = App(game_api=GameAPI())
    app.run()
