"""Utility for source code compliance.

This module includes a suite of code checks that are standard for the project's
source code.

### Lint check
`check_lint` uses the [flake8 linter](https://flake8.pycqa.org/). For a
list of error codes and violations, see:

- https://flake8.pycqa.org/en/latest/user/error-codes.html
- https://pycodestyle.pycqa.org/en/latest/intro.html#error-codes

### Code format
`check_format` uses the [Black code formatter](https://github.com/psf/black).
The standard format of the project is based on [Black's default configuration
](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html).
`format_source_code` will automatically format the source code to comply with
`check_format`.

### Documentation generator
`check_docs` generates the documentation using `botroyale.util.docs.test_docs`
to catch warnings.
"""
from typing import Optional, Callable
import subprocess
from botroyale.util.docs import test_docs
from botroyale.util import PACKAGE_DIR


MAX_LINE_LENGTH = 88  # Black's default
IGNORE_ERRORS = [
    "E203",  # whitespace before ':' (not pep8 compliant)
]
TARGET_PYTHON_VERSION = "py39"
EXCLUDE_FOLDERS = [
    "gui",  # Currently too messy to consider (should be removed in the future)
]
DOCSTRING_CONVENTION = "google"


def check_format() -> bool:
    """Check source code using the Black code formatter.

    See also: `format_source_code`.

    Returns:
        True if the source code requires no formatting.
    """
    return _run_black(check_only=True) == 0


def check_lint() -> bool:
    """Check source code using the flake8 linter.

    See: https://flake8.pycqa.org/

    Returns:
        True if no relevant errors are found.
    """
    return _run_flake8() == 0


def check_docs() -> bool:
    """Generate the docs and check no warnings were raised.

    See `botroyale.util.docs.make_docs`.

    Returns:
        True if the docs were generated without errors or warnings.
    """
    print("≡≡≡≡≡ Checking automatic documentation generator...")
    return test_docs()


def format_source_code() -> int:
    """Format source code using the Black code formatter.

    Returns:
        The returncode of the command to the Black code formatter.
    """
    return _run_black(check_only=False)


def _run_flake8(
    exclude: Optional[list[str]] = None,
    select_errors: Optional[list[str]] = None,
    ignore: Optional[list[str]] = None,
    max_line_length: int = MAX_LINE_LENGTH,
    max_complexity: int = 10,
) -> int:
    """Run flake8 code checker and return the resulting returncode.

    Args:
        exclude: List of patterns in file/folders to exclude.
        select_errors: List of patterns in error codes to check.
        ignore: List of patterns in error codes to ignore.
        max_line_length: Max length of a line that will not be considered a
            violation. 0 to disable.
        max_complexity: Maximum cyclomatic complexity for the mccabe complexity
            checker plugin.

    Returns:
        The returncode of the command (0 means no issues).
    """
    extra_args = []

    excludes = EXCLUDE_FOLDERS
    if exclude is not None:
        excludes += exclude
    extra_args.extend(["--extend-exclude", ",".join(excludes)])

    if select_errors is not None:
        extra_args.extend(["--select", ",".join(select_errors)])

    ignores = IGNORE_ERRORS
    if ignore is not None:
        ignores += ignore
    extra_args.extend(["--extend-ignore", ",".join(ignores)])

    command_args = [
        "python",
        "-m",
        "flake8",
        str(PACKAGE_DIR),
        "--max-line-length",
        str(max_line_length),
        "--max-complexity",
        str(max_complexity),
        "--docstring-convention",
        DOCSTRING_CONVENTION,
        *extra_args,
    ]
    print(f"≡≡≡≡≡ Running flake8 code checker...\n{' '.join(command_args)}")
    r = subprocess.run(command_args)
    return r.returncode


def _run_black(
    check_only: bool = False,
    exclude: Optional[list[str]] = None,
) -> int:
    """Run the Black code formatter and return the resulting returncode.

    Calling this function without arguments will format the source code to
    comply with the standard format of the project.

    Args:
        check_only: Performs a check only without modifying files.
        exclude: List of patterns in file/folders to exclude.

    Returns:
        The returncode of the command (0 means no issues).
    """
    extra_args = []
    excludes = EXCLUDE_FOLDERS
    if exclude is not None:
        excludes += exclude
    excludes = f"/({'|'.join(excludes)})/"
    extra_args.extend(["--extend-exclude", excludes])
    if check_only:
        extra_args.append("--check")
    command_args = [
        "python",
        "-m",
        "black",
        str(PACKAGE_DIR),
        "--target-version",
        TARGET_PYTHON_VERSION,
        "--line-length",
        str(MAX_LINE_LENGTH),
        *extra_args,
    ]
    print(f"≡≡≡≡≡ Running Black code formatter...\n{' '.join(command_args)}")
    r = subprocess.run(command_args)
    return r.returncode


STANDARD_TEST_SUITE: dict[str, tuple[Callable, str]] = {
    "lint": (check_lint, "Code lint (flake8)"),
    "format": (check_format, "Code format (Black)"),
    "docs": (check_docs, "Documentation (pdoc3)"),
}
"""Dictionary of test name to (function, description) tuple that are the
standard test suite."""
