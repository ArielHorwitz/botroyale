"""The default GUI option.

Uses `botroyale.logic.game.StandardGameAPI`.
"""
from botroyale.logic.game import StandardGameAPI
from botroyale.util.settings import Settings
from botroyale.gui.app import App


def run():
    """Runs the GUI app with `botroyale.logic.game.StandardGameAPI`."""
    app = App(game_api=StandardGameAPI())
    # We write settings to file after completing startup, after all parts
    # of the program have had a chance to set their defaults.
    Settings.write_to_file()
    app.run()
