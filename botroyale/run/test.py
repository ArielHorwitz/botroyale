"""A suite of tests for continuous integration.

This module is intended for developers that wish to contribute source code. The
`run` function will run and ensure the code passes all standard tests, and is
compliant with the project's automated requirements.

See: `botroyale.util.code`.
"""
import argparse
from botroyale.util.code import STANDARD_TEST_SUITE


def _parse_args() -> argparse.Namespace:
    desc = (
        "Run the standard test suite and output the results to console. "
        "Available tests: "
    )
    desc += ", ".join(STANDARD_TEST_SUITE.keys())
    parser = argparse.ArgumentParser(
        description=desc,
    )
    parser.add_argument(
        "tests",
        metavar="TESTS",
        nargs="*",
        default=None,
        help="names of tests to run (default: all)",
    )
    args = parser.parse_args()
    return args


def run():
    """Run the standard test suite and output the results to console."""
    args = _parse_args()
    print(f"{args.tests=}")
    if args.tests:
        test_names = set(args.tests) & set(STANDARD_TEST_SUITE.keys())
    else:
        test_names = list(STANDARD_TEST_SUITE.keys())
    total_tests = len(test_names)
    errors = 0
    outputs = []
    for test_name in test_names:
        func, description = STANDARD_TEST_SUITE[test_name]
        result = func()
        if result is True:
            result = "Pass"
        else:
            errors += 1
            result = "FAIL"
        outputs.append(f"{description:>30}: {result}")
    print("≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡ Test Outputs ≡≡≡≡≡≡≡≡≡≡≡≡≡≡≡")
    for output in outputs:
        print(output)
    if errors > 0:
        print(f"FAIL. {errors}/{total_tests} tests failed.")
    else:
        print(f"Pass. All {total_tests} tests passed.")
