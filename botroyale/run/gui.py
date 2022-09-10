"""The default GUI option.

Uses `botroyale.logic.game.StandardGameAPI`.
"""
from botroyale.logic.game import StandardGameAPI
from botroyale.gui.app import App


def run():
    """Runs the GUI app with `botroyale.logic.game.StandardGameAPI`."""
    app = App(game_api=StandardGameAPI())
    app.run()
