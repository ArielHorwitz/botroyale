"""Opens the documentation in the default browser. Creates the docs if missing."""
import argparse
from botroyale.util.docs import open_docs, make_docs


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and view Bot Royale documentation",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force recreating the docs",
    )
    parser.add_argument(
        "--no-open",
        "--no",
        action="store_true",
        help="don't open the docs",
    )
    args = parser.parse_args()
    return args


def run():
    """Creates and opens the docs.

    See: `botroyale.util.docs`
    """
    args = _parse_args()
    make_docs(force_remake=args.force)
    if not args.no_open:
        open_docs()
