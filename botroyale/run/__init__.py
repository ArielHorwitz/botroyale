"""The first package to be imported and executed.

The function `run_script` will be called to parse the command line arguments and
decide which submodule to import and call it's `run()` function.
"""
import sys
from importlib import import_module
from pkgutil import iter_modules
from botroyale.util import PACKAGE_DIR, TITLE, MAIN_ARGS


SCRIPT_DIR = PACKAGE_DIR / "run"


def run_script():
    """Imports and calls `run` from the requested module.

    The name of the module to be executed is collected from the program
    arguments. Searches the "run" directory for modules.
    """
    args = MAIN_ARGS
    if args.list:
        _print_run_modules(verbose=True)
        quit()
    print(f"Parsed args: {args}")
    requested_module_name = args.module
    print(f"\n>> Welcome to {TITLE} <<\n")

    # Find the module
    run_modules = _find_run_modules()
    if requested_module_name not in run_modules:
        _print_run_modules()
        requested_file = SCRIPT_DIR / f"{requested_module_name}.py"
        raise ModuleNotFoundError(f"No such module: {requested_file}")

    # Import the module
    module_name = f"botroyale.run.{requested_module_name}"
    print(f"Importing: {module_name}")
    module = import_module(module_name)
    print(f"Imported: {module}")

    # Call the run() function
    if hasattr(module, "run"):
        if callable(module.run):
            print(f"Running: {module_name}.run()")
            module.run()
    print(f"Completed running: {module_name}")


def _find_run_modules() -> list[str]:
    """Finds module names in the run subpackage."""
    assert SCRIPT_DIR.is_dir()
    return [minfo.name for minfo in iter_modules([str(SCRIPT_DIR)])]


def _print_run_modules(verbose: bool = False):
    """Prints the module names found in the run directory.

    Args:
        verbose: If true, will import each module to retrieve its docstring and
            print it along with the module name.
    """
    run_modules = _find_run_modules()
    module_names = []
    for mod_name in run_modules:
        s = f"» {mod_name}"
        if verbose:
            mod = import_module(f"botroyale.run.{mod_name}")
            doc = mod.__doc__.strip().split("\n", 1)[0]
            if len(doc) > 100:
                doc = f"{doc[:100]}..."
            s = f"{s:<20}: {doc}"
        module_names.append(s)
    module_output = "\n".join(module_names)
    print(f'Available modules in the "run" directory:\n{module_output}')
    print(f"\nSee: {sys.argv[0]} --help\n")
