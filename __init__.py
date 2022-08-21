""".. include:: ./docs/README.md"""
# We pass a fixed version of the README to the docstring, see below

from util import PROJ_DIR, VERSION
from util.file import file_load, file_dump


def _generate_fixed_readme():
    """Generate a "fixed" README for the html docs.

    Insert version and a dynamically generated reference to the guides that are
    not relevant for the main project's static README."""
    added_lines = '\n'.join([
        f'Documentation built on `v{VERSION}`.\n',
        f'Check out `{PROJ_DIR.name}.guides` for many resources, from beginner to advanced.\n'
    ])
    readme_path = PROJ_DIR / 'README.md'
    fixed_readme_path = PROJ_DIR / 'docs' / 'README.md'
    fixed_readme = f'{added_lines}\n{file_load(readme_path)}'
    file_dump(fixed_readme_path, fixed_readme)


_generate_fixed_readme()


__version__ = VERSION
__pdoc__ = {
    'main': False,
    'gui': False,
    'docs': False,
    'dev': False,
    'venv': False,
}
