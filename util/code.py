"""Utility for source code compliance.

This module includes a suite of code checks that are standard for the project's
source code.

### Static code check
`check_code_static` uses the [flake8 static code checker](
https://flake8.pycqa.org/). Currently ignores E501 (max line length), however
this may change in the future. For a list of error codes and violations, see:

- https://flake8.pycqa.org/en/latest/user/error-codes.html
- https://pycodestyle.pycqa.org/en/latest/intro.html#error-codes

### Code format
`check_format` uses the [Black code formatter](https://github.com/psf/black).
The standard format of the project is based on [Black's default configuration
](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)
but without string normalization. `format_source_code` will automatically format
the source code to comply with the `check_format`.

### Documentation generator
`check_docs` generates the documentation using `run.makedocs` to catch
warnings.
"""
from typing import Optional, Callable
import subprocess
import warnings
from run.makedocs import make_docs


MAX_LINE_LENGTH = 88  # Black's default
IGNORE_ERRORS = [
    "E203",  # whitespace before ':' (not pep8 compliant)
]
TARGET_PYTHON_VERSION = "py39"
EXCLUDE_FOLDERS = [
    "venv",  # Virtual environment has many python files that are not ours
    "dev",  # Convenience folder for developers for arbitrary files
    "gui",  # Currently too messy to consider (should be removed in the future)
]


def check_format() -> bool:
    """Check source code using the Black code formatter.

    See also: `format_source_code`.

    Returns:
        True if the source code passes the check.
    """
    return _run_black(check_only=True, string_normalization=False) == 0


def check_code_static() -> bool:
    """Check source code using the flake8 static code checker.

    Ignores some formatting errors.

    See: https://flake8.pycqa.org/

    Returns:
        True if the source code passes the check.
    """
    return _run_flake8() == 0


def check_docs() -> bool:
    """Generate the docs and check no warnings were raised.

    See `run.makedocs`.

    Returns:
        True if the docs were generated without warnings.
    """
    print(f"≡≡≡≡≡ Checking automatic documentation generator...")
    with warnings.catch_warnings(record=True) as warning_catcher:
        make_docs()
    if len(warning_catcher) > 0:
        print(f"Found {len(warning_catcher)} warnings:")
        for warning in warning_catcher:
            print(f"  {warning.message}")
        return False
    print("Documentation built sucessfully.")
    return True


def format_source_code(string_normalization: bool = True) -> int:
    """Format source code using the Black code formatter.

    By default, *string_normalization* is enabled (to be encouraged) even
    though it is not required by `check_format`.

    Returns:
        The returncode of the command to the Black code formatter.
    """
    return _run_black(check_only=False, string_normalization=string_normalization)


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
        "flake8",
        ".",
        "--max-line-length",
        str(max_line_length),
        "--max-complexity",
        str(max_complexity),
        *extra_args,
    ]
    print(f"≡≡≡≡≡ Running flake8 code checker...\n{' '.join(command_args)}")
    r = subprocess.run(command_args)
    return r.returncode


def _run_black(
    check_only: bool = False,
    exclude: Optional[list[str]] = None,
    string_normalization: bool = True,
) -> int:
    """Run the Black code formatter and return the resulting returncode.

    Calling this function without arguments will format the source code to
    comply with the standard format of the project.

    Args:
        check_only: Performs a check only without modifying files.
        exclude: List of patterns in file/folders to exclude.
        string_normalization: Enable formatting strings' quotes.

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
    if not string_normalization:
        extra_args.append("--skip-string-normalization")
    command_args = [
        "black",
        ".",
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
    'code': (check_code_static, "Static code (flake8)"),
    'format': (check_format, "Code format (Black)"),
    'docs': (check_docs, "Documentation (pdoc3)"),
}
"""Dictionary of test name to (function, description) tuple that are the
standard test suite."""
