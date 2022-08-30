"""
Build the docs based on local source code.

Uses `pdoc3` library to automatically read source code and produce HTML documentation. Will delete the `docs/botroyale` folder and recreate docs.
"""
import os
import shutil
import argparse
from collections import namedtuple
from pdoc import Module, Context, tpl_lookup, link_inheritance
from util import PROJ_DIR
from util.file import popen_path, file_dump, file_load


__all__ = []  # for pdoc

ROOT_PACKAGE_NAME = PROJ_DIR.name
if not ROOT_PACKAGE_NAME.isidentifier():
    raise NameError(f'Project directory "{ROOT_PACKAGE_NAME}" must be a valid python package name. Try renaming your project folder with *only* letters, (e.g. "botroyale").')

INCLUDE_SUBPACKAGES = [
    'api',
    'bots',
    'logic',
    'run',
    'util',
    'guides',
]
DOCS_DIR = PROJ_DIR / 'docs'
"""The docs folder. Includes the html docs themselves, templates, guides, and more."""
TEMPLATE_DIR = DOCS_DIR / 'templates'
tpl_lookup.directories.insert(0, str(TEMPLATE_DIR))
OUTPUT_DIR = DOCS_DIR / ROOT_PACKAGE_NAME
"""The html documentation folder."""
INDEX_FILE = OUTPUT_DIR / 'index.html'
"""The root index of the html documentation folder."""
GUIDES_MD_DIR = DOCS_DIR / 'guides'
"""The guides folder of markdown files."""
GUIDES_OUTPUT_DIR = OUTPUT_DIR / 'guides'
"""The html guides root folder."""
GUIDES_PY_DIR = PROJ_DIR / 'guides'
"""The guides package. Generated with the docs and should be ignored by git."""
GUIDE_CATEGORIES = ('beginner', 'guides', 'rules', 'advanced')
"""Category names for guides."""
CATEGORY_IDENT_PREFIX = '*Categories: '
"""Prefix of line to parse categories of a guide. See: `_find_guide_title_categories`."""
CATEGORY_IDENT_SUFFIX = '*'
"""Suffix of line to parse categories of a guide. See: `_find_guide_title_categories`."""
CATEGORY_IDENT_SPLIT = ', '
"""Seperator between category names of a guide. See: `_find_guide_title_categories`."""

Guide = namedtuple('Guide', ['path', 'title', 'categories'])


def run():
    make_docs()


def make_docs():
    """Clear and create the docs."""
    print(f'{ROOT_PACKAGE_NAME=}')
    print(f'{DOCS_DIR=}')
    print(f'{INCLUDE_SUBPACKAGES=}')
    print(f'TEMPLATE_DIR={tpl_lookup.directories}')
    print('Preparing guides...')
    _rebuild_guides()
    print('Building docs...')
    subpackages = []
    context = Context()
    root_package = Module('.', context=context)
    for subpkg in INCLUDE_SUBPACKAGES:
        mod = Module(subpkg, context=context)
        subpackages.append(mod)
    link_inheritance(context)
    print('Clearing existing docs...')
    if OUTPUT_DIR.is_dir():
        shutil.rmtree(OUTPUT_DIR)
    print('Writing new docs...')
    for subpkg in subpackages:
        for mod in _recursive_mods(subpkg):
            file_path = _module_path(mod)
            _write_html(file_path, mod.html())
    _write_html(OUTPUT_DIR / 'index.html', root_package.html())
    print('Make docs done.')


def _rebuild_guides():
    """Prepares the guides in *GUIDES_MD_DIR* to be indexed by `make_docs`.

    Reads each guide markdown (.md) file in and writes a python module file with a docstring that includes the markdown file (to be indexed by `make_docs`). Then writes an `__init__.py` with a docstring with formatted links to the html files that will be generated by pdocs.
    """
    GUIDES_MD_DIR.mkdir(parents=True, exist_ok=True)
    GUIDES_PY_DIR.mkdir(parents=True, exist_ok=True)

    # Module for each markdown
    guides = []
    for child in sorted(GUIDES_MD_DIR.iterdir()):
        if child.suffix != '.md' or '.' in child.stem:
            continue
        title, categories = _find_guide_title_categories(child)
        guide_fname = child.stem
        new_docstring = f'""".. include:: {_windows_compat(str(child))}"""'
        gmod_path = GUIDES_PY_DIR / f'{guide_fname}.py'
        file_dump(gmod_path, new_docstring, clear=True)
        ghtml_path = GUIDES_OUTPUT_DIR / f'{guide_fname}.html'
        guides.append(Guide(ghtml_path, title, categories))

    # Package module with formatted list of guides
    # Organize by category
    categories = {c: [] for c in GUIDE_CATEGORIES}
    for g in guides:
        entry_str = _windows_compat(f'- [{g.title}]({g.path})')
        for c in g.categories:
            categories[c].append(entry_str)
    # Format the main module
    main_doc_strs = [
        '"""',
        'New here? Check out:\n',
        *categories[GUIDE_CATEGORIES[0]],
        '\n',
        '## Resources\n',
    ]
    # Extend with each category that isn't the beginner category
    for c in GUIDE_CATEGORIES[1:]:
        main_doc_strs.append(f'\n### {c.capitalize()}')
        main_doc_strs.extend(categories[c])
    # Finalize and write
    main_doc_strs.append('"""')
    main_doc = '\n'.join(main_doc_strs)
    file_dump(GUIDES_PY_DIR / '__init__.py', main_doc, clear=True)


def _windows_compat(s):
    """Add backslashes for windows path compatibility for `file_dump`."""
    return s.replace('\\', '\\\\')


def _find_guide_title_categories(guide_md_file):
    """Finds the title and categories of a markdown file guide for the docs.

    To find the title, we return the contents of the first *Header 1* in the file (a line starting with "# "). Default to the file name if no title found.

    To find categories, we look for a line with a specific format and parse the category names. This line must be prepended by `CATEGORY_IDENT_PREFIX` and appended by `CATEGORY_IDENT_SUFFIX`. The text in between these affixes will be split using the `CATEGORY_IDENT_SPLIT` to find a list of categories.

    For example, if the prefix is "*Categories", the suffix is "*" and the split is ", ", then the line "*Categories: beginner, guides*" in a guide markdown file will indicate that the guide belongs to the categories "beginner" and "guides".
    """
    markdown = file_load(guide_md_file)
    title = None
    categories = []
    for line in markdown.split('\n'):
        if not title and line.startswith('# '):  # A markdown header
            title = line[2:]
        if not categories:
            if line.startswith(CATEGORY_IDENT_PREFIX) and line.endswith(CATEGORY_IDENT_SUFFIX):
                parse_this = line[len(CATEGORY_IDENT_PREFIX):-len(CATEGORY_IDENT_SUFFIX)]
                categories = set(parse_this.split(CATEGORY_IDENT_SPLIT))
        if title and categories:
            break
    if title is None:
        title = guide_md_file.stem
    for c in categories:
        if c not in GUIDE_CATEGORIES:
            raise KeyError(f'Unknown category "{c}" in guide: {guide_md_file.name} ; {GUIDE_CATEGORIES=}')
    return title, categories


def _module_path(mod):
    html = mod.html()
    full_module_name = mod.name
    file_path = OUTPUT_DIR
    module_parts = full_module_name.split('.')
    module_name = module_parts[-1]
    for n in module_parts[:-1]:
        file_path /= n
    if mod.is_package:
        file_path /= module_name
        file_path /= f'index.html'
    else:
        file_path /= f'{module_name}.html'
    return file_path


def _write_html(file_path, html):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_dump(file_path, html)


def _recursive_mods(mod):
    yield mod
    for submod in mod.submodules():
        yield from _recursive_mods(submod)
