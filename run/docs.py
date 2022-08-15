"""
Build the docs based on local source code.

Uses `pdoc3` library to automatically read source code and produce HTML documentation. Will delete the `docs/botroyale` folder and recreate docs.
"""
__all__ = []  # for pdoc


import os
import shutil
import argparse
from pdoc import Module, Context, tpl_lookup, link_inheritance
from util import PROJ_DIR
from util.file import popen_path


ROOT_PACKAGE_NAME = 'botroyale'
INCLUDE_SUBPACKAGES = [
    'api',
    'bots',
    'logic',
    'run',
    'util',
    'docs.guides',
]
DOCS_DIR = PROJ_DIR / 'docs'
"""The docs folder. Includes the html docs themselves and templates."""
OUTPUT_DIR = DOCS_DIR / ROOT_PACKAGE_NAME
"""The html documentation folder."""
TEMPLATE_DIR = DOCS_DIR / 'templates'
tpl_lookup.directories.insert(0, str(TEMPLATE_DIR))


def run():
    """Clear and create the docs."""
    print(f'{tpl_lookup.directories=}')
    print(f'{INCLUDE_SUBPACKAGES=}')
    print(f'{DOCS_DIR=}')
    print(f'{OUTPUT_DIR=}')
    print('Clearing docs...')
    if OUTPUT_DIR.is_dir():
        shutil.rmtree(OUTPUT_DIR)
    print('Building docs...')
    context = Context()
    subpackages = []
    root_package = Module('.', context=context)
    for subpkg in INCLUDE_SUBPACKAGES:
        mod = Module(subpkg, context=context)
        subpackages.append(mod)
    link_inheritance(context)
    print('Writing docs...')
    _write_html(OUTPUT_DIR / 'index.html', root_package.html())
    for subpkg in subpackages:
        for mod in _recursive_mods(subpkg):
            file_path = _module_path(mod)
            _write_html(file_path, mod.html())
    print('Make docs done.')


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
    print(f'Writing {file_path=} {len(html)=}')
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(html)

def _recursive_mods(mod):
    yield mod
    for submod in mod.submodules():
        yield from _recursive_mods(submod)
