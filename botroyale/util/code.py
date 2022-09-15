"""Source code utilities.

This module includes a test suite for code integration and utilities for
complying with the test suite. Project must be installed from source and with
dev requirements, see: `botroyale.guides.contributing`.

## Command line
To run the integration test suite:
```noformat
botroyale test --help
```

To format the code to comply:
```noformat
botroyale format --help
```

### Unit tests
Uses [pytest](https://pytest.org) and [hypothesis](
https://hypothesis.readthedocs.io/en/latest/) to test modules in `tests/`.

### Lint check
Uses the [flake8 linter](https://flake8.pycqa.org/). For a list of error codes
and violations, see:

- https://flake8.pycqa.org/en/latest/user/error-codes.html
- https://pycodestyle.pycqa.org/en/latest/intro.html#error-codes

### Code format
Uses the [Black code formatter](https://github.com/psf/black). The standard
format of the project is [Black's default configuration
](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html).
`format_source_code` will automatically format the source code to comply with
the test.

### Documentation generator
Uses `botroyale.util.docs.test_docs` to ensure the docs can be created without
errors or warnings.
"""
from typing import Optional
import subprocess
import argparse
from hypothesis import Verbosity as Verb
from botroyale.util.docs import test_docs
from botroyale.util import PROJ_DIR, PACKAGE_DIR


TEST_NAMES = ["unit", "lint", "format", "docs"]
MAX_LINE_LENGTH = 88  # Black's default
IGNORE_ERRORS = [
    "E203",  # whitespace before ':' (not pep8 compliant)
]
TARGET_PYTHON_VERSION = "py39"
EXCLUDE_FOLDERS = [
    "gui",  # Currently too messy to consider (should be removed in the future)
]
DOCSTRING_CONVENTION = "google"
# A dictionary of hypothesis profiles for unit testing `conftest.py`
UNITTEST_PROFILES = {
    "sample": dict(max_examples=1),
    "dev": dict(max_examples=20),
    "debug": dict(max_examples=20, verbosity=Verb.verbose),
    "normal": dict(max_examples=100, verbosity=Verb.normal),
    "extensive": dict(max_examples=500, verbosity=Verb.quiet),
    "ci": dict(max_examples=2_000, verbosity=Verb.quiet),
}


def entry_point_tests(args) -> int:
    """Script entry point to run the integration test suite."""
    parser = argparse.ArgumentParser(
        prog="botroyale test",
        description="Run the test suite.",
    )
    parser.add_argument(
        "tests",
        nargs="*",
        metavar="TEST_NAMES",
        default=None,
        help="names of tests to run (default: all)",
    )
    parser.add_argument(
        "-p",
        "--unittests-profile",
        default="dev",
        help="profile for unittests (default: dev)",
    )
    parser.add_argument(
        "-n",
        "--unittests-names",
        default="test_",
        help='filter for unittest names (default: "test_")',
    )
    parser.add_argument(
        "-u",
        "--unittests-modules",
        default=None,
        help="filter for unittest modules (default: no filter)",
    )
    args = parser.parse_args(args)
    print(f"{args=}")
    result = run_test_suite(
        test_names=args.tests,
        unit_profile=args.unittests_profile,
        unit_module_filter=args.unittests_modules,
        unit_test_filter=args.unittests_names,
    )
    return 0 if result else 1


def entry_point_format(args) -> int:
    """Script entry point to format the source code."""
    parser = argparse.ArgumentParser(
        prog="botroyale format",
        description="Format the source code.",
    )
    parser.parse_args(args)
    return _run_black(check_only=False)


def run_test_suite(
    test_names: Optional[list[str]] = None,
    unit_profile: Optional[str] = "dev",
    unit_test_filter: Optional[str] = "test_",
    unit_module_filter: Optional[str] = None,
) -> bool:
    """Run the test suite.

    Args:
        test_names: List of names of tests to run (see: `TEST_NAMES`)
        unit_profile: Name of profile for unittests (see: `UNITTEST_PROFILES`)
        unit_test_filter: Include only test names containing this string
            (default: "test_")
        unit_module_filter: Include only test modules containing this string
            (default: no filter)

    Returns:
        True if all tests pass.
    """
    if test_names:
        invalid_names = set(test_names) - set(TEST_NAMES)
        if invalid_names:
            raise ValueError(
                f"{invalid_names} are not valid test names. "
                f"Available tests: {TEST_NAMES}"
            )
    else:
        test_names = TEST_NAMES
    total_tests = len(test_names)
    results = []
    outputs = []

    def add_result(description, result):
        results.append(result)
        outputs.append(f"{description:>30}: {'pass' if result else 'FAIL'}")

    # unittests
    if "unit" in test_names:
        result = _run_unittests(
            profile=unit_profile,
            module_filter=unit_module_filter,
            test_filter=unit_test_filter,
        )
        add_result("unit tests (unit)", result == 0)
    if "lint" in test_names:
        add_result("flake8 linting (lint)", _run_flake8() == 0)
    if "format" in test_names:
        add_result("black formatting (format)", _run_black(check_only=True) == 0)
    if "docs" in test_names:
        add_result("pdoc3 documentation (docs)", test_docs())

    assert len(outputs) == total_tests
    errors = total_tests - sum(results)
    print("≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡ Test Results ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡")
    for output in outputs:
        print(output)
    if errors > 0:
        print(f"FAIL. {errors}/{total_tests} tests failed.")
    else:
        print(f"Pass. All {total_tests} tests passed.")


def _run_unittests(
    profile: str,
    test_filter: str,
    module_filter: Optional[str] = None,
) -> int:
    base_args = [
        "pytest",
    ]
    # We wish to avoid automatic discovery so we pass all modules as arguments
    modules = [
        m
        for m in _collect_test_modules()
        if not module_filter or module_filter in str(m)
    ]
    pytest_args = [
        "-k",
        test_filter,
        "-s",
        "--hypothesis-profile",
        profile,
    ]
    command_args = [
        *base_args,
        *(str(m) for m in modules),
        *pytest_args,
    ]
    show_command = " ".join(base_args + pytest_args)
    print(f"≡≡≡≡≡ Running unit tests...\n{show_command}")
    print("Testing modules:")
    for m in modules:
        print(f"  {m.relative_to(PROJ_DIR / 'tests')}")
    print(f"Hypothesis profile: {UNITTEST_PROFILES[profile]}")
    r = subprocess.run(command_args)
    return r.returncode


def _run_flake8(
    exclude: Optional[list[str]] = None,
    select_errors: Optional[list[str]] = None,
    ignore: Optional[list[str]] = None,
    max_line_length: int = MAX_LINE_LENGTH,
    max_complexity: int = 10,
) -> int:
    """Run flake8 linter and return the resulting returncode.

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
    print(f"≡≡≡≡≡ Running flake8 linter...\n{' '.join(command_args)}")
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


def _collect_test_modules(dir=None):
    dir = dir if dir is not None else PROJ_DIR / "tests"
    for child in dir.iterdir():
        if child.stem.startswith("_") or child.suffix != ".py":
            continue
        if child.is_dir():
            yield from _collect_test_modules(child)
        elif child.is_file():
            yield child
