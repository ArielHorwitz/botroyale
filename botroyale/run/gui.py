"""GUI app entry point.

To run:
```noformat
botroyale gui --help
```
"""
import argparse
from botroyale.logic.game import StandardGameAPI


def entry_point_gui(args):
    """Runs the GUI app with `botroyale.logic.game.StandardGameAPI`."""
    parser = argparse.ArgumentParser(description="Open the GUI app.")
    parser.parse_args(args)
    # Import as late as possible since this opens up a window on desktop
    from botroyale.gui.app import App

    app = App(game_api=StandardGameAPI())
    app.run()
    return 0
