"""Automatic source code formatting.

Helps developers comply with the project's standard format. See
`util.code.format_source_code`.
"""
from util import MAIN_ARGS
from util.code import format_source_code


def run():
    """Format the source code to comply with the project's standard format.

    See `util.code.format_source_code`.
    """
    string_normalization = 'nostring' not in MAIN_ARGS.opargs
    format_source_code(string_normalization=string_normalization)
