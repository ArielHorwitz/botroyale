"""
A debugging GUI option.


Runs the GUI and uses the base class `api.gui.GameAPI`. Expected to have extremely limited functionality and is used for debugging by the GUI.
"""
__all__ = []  # for pdoc


from api.gui import GameAPI
from util.settings import Settings
from gui.app import App


def run():
    app = App(game_api=GameAPI())
    app.run()
