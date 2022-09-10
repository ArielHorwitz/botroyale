"""Automatic source code formatting.

Helps developers comply with the project's standard format. See
`botroyale.util.code.format_source_code`.
"""
import argparse
from botroyale.util.code import format_source_code


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Format the source code to comply with integration tests.",
    )
    args = parser.parse_args()
    return args


def run():
    """Format the source code to comply with the project's standard format.

    See `botroyale.util.code.format_source_code`.
    """
    _parse_args()
    format_source_code()
