"""
The first package to be imported and executed.

The function `run_script` will be called to parse the command line arguments and decide which submodule to import and call it's `run()` function.
"""
import sys
from importlib import import_module
from pkgutil import iter_modules
import argparse
from util import PROJ_DIR, FULL_TITLE, DESCRIPTION


SCRIPT_DIR = PROJ_DIR / 'run'


def run_script():
    """Imports the module requested from the main program arguments and calls
    a `run()` function if exists. Searches the "run" directory for modules."""
    print(f'\n>> Welcome to {FULL_TITLE} <<\n')
    args = _parse_args()
    if args.list:
        _print_run_modules()
        quit()
    print(f'Parsed args: {args}')
    requested_module_name = args.module

    # Find the module
    run_modules = _find_run_modules()
    if requested_module_name not in run_modules:
        _print_run_modules()
        requested_file = SCRIPT_DIR / f'{requested_module_name}.py'
        raise ModuleNotFoundError(f'No such module: {requested_file}')

    # Import the module
    module_name = f'run.{requested_module_name}'
    print(f'Importing: {module_name}')
    module = import_module(module_name)
    print(f'Imported: {module}')

    # Call the run() function
    if hasattr(module, 'run'):
        if callable(module.run):
            print(f'Running: {module_name}.run()')
            module.run()
    print(f'Completed running: {module_name}')


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(DESCRIPTION)
    parser.add_argument('module', metavar='MODULE',
        nargs='?', default='gui',
        help='name of module to run (default: gui)')
    parser.add_argument('--list',
        action='store_true',
        help='print available modules to run and quits')
    args = parser.parse_args()
    return args


def _find_run_modules() -> list[str]:
    """Finds module names in the run subpackage."""
    assert SCRIPT_DIR.is_dir()
    return [minfo.name for minfo in iter_modules([str(SCRIPT_DIR)])]


def _print_run_modules():
    """Prints the module names found in the run directory."""
    run_modules = _find_run_modules()
    module_names = '\n'.join(f'- {s}' for s in run_modules)
    print(f'Available modules in the "run" directory:\n{module_names}')
    example_module = run_modules[0]
    print(f'\nSee: {sys.argv[0]} --help\n')
