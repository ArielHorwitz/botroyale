""".. include:: ./docs/README.md"""
# We pass a fixed version of the README to the docstring, see below

from util import PROJ_DIR, VERSION
from util.file import file_load, file_dump


def _insert_readme_guides_link(original_readme_text):
    found_guides_line = False
    new_lines = []
    for line in original_readme_text.split('\n'):
        new_lines.append(line)
        if not line == '## Guides and Documentation':
            continue
        found_guides_line = True
        new_lines.extend([
            '',
            f'Check out `{PROJ_DIR.name}.guides` for many resources, from beginner to advanced.',
            '',
        ])
    assert found_guides_line
    return '\n'.join(new_lines)


# Insert the dynamically generated reference for the html docs
__readme_path = PROJ_DIR / 'README.md'
__fixed_readme_path = PROJ_DIR / 'docs' / 'README.md'
__fixed_readme = _insert_readme_guides_link(file_load(__readme_path))
file_dump(__fixed_readme_path, __fixed_readme)


__version__ = VERSION
__pdoc__ = {
    'main': False,
    'gui': False,
    'docs': False,
    'dev': False,
    'venv': False,
}
