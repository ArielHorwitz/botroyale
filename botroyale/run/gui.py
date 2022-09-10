"""Run the GUI app.

Uses `botroyale.logic.game.StandardGameAPI`.
"""
import argparse
from botroyale.logic.game import StandardGameAPI
from botroyale.gui.app import App


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the gui app.",
    )
    args = parser.parse_args()
    return args


def run():
    """Runs the GUI app with `botroyale.logic.game.StandardGameAPI`."""
    app = App(game_api=StandardGameAPI())
    app.run()
