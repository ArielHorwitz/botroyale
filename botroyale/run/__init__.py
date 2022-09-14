"""Default command line entry point for the program."""
import sys
import argparse
from botroyale.util import INSTALLED_FROM_SOURCE
from botroyale.run.gui import entry_point_gui
from botroyale.run.cli import entry_point_cli


HELP_STR = """usage: botroyale [SUBCOMMAND] [--help]

Subcommands (default: "gui")
  gui         Open the GUI app
  cli         Open the CLI utility
"""

if INSTALLED_FROM_SOURCE:
    HELP_STR += """
Developer subcommands
  test        Run integration test suite
  format      Format source code
  docs        Create and view documentation locally
"""


def _collect_entry_points():
    INSTALLED_FROM_SOURCE
    commands_map = {
        "gui": entry_point_gui,
        "cli": entry_point_cli,
    }
    if INSTALLED_FROM_SOURCE:
        from botroyale.util.code import entry_point_tests, entry_point_format
        from botroyale.util.docs import entry_point_docs

        commands_map |= {
            "test": entry_point_tests,
            "format": entry_point_format,
            "docs": entry_point_docs,
        }
    return commands_map


def _parse_args(args) -> argparse.Namespace:
    parser = argparse.ArgumentParser(usage=HELP_STR)
    return parser.parse_args(args)


def script_entry_point() -> int:
    """Runs the GUI app with `botroyale.logic.game.StandardGameAPI`."""
    args = sys.argv[1:]
    if not args:
        args = ["gui"]
    command = args.pop(0)
    if command in ("-h", "--help"):
        print(HELP_STR)
        return 0
    entry_points = _collect_entry_points()
    if command not in entry_points:
        print(f'"{command}" is not a valid subcommand.\n\n{HELP_STR}')
        return 1
    entry_point_func = entry_points[command]
    returncode = entry_point_func(args)
    assert isinstance(returncode, int) and returncode >= 0
    return returncode
