"""Build the docs based on local source code.

Uses `pdoc3` library to automatically read source code and produce HTML
documentation. Will delete the output folder and recreate docs.
"""
from typing import Optional
import shutil
import os
import warnings
from pathlib import Path
from pdoc import Module, Context, tpl_lookup, link_inheritance
from botroyale.util import PROJ_DIR, PACKAGE_DIR, INSTALLED_FROM_SOURCE
from botroyale.util.file import popen_path, file_dump, get_usr_dir


DOCS_DIR = PROJ_DIR / "docs"
TEMPLATE_DIR = DOCS_DIR / "templates"
USER_DIR = "botroyale"


def open_docs(
    output_dir: Optional[os.PathLike] = None,
    force_remake: bool = False,
):
    """Opens the docs in default browser, using `botroyale.util.file.popen_path`."""
    output_dir = _get_output_dir(output_dir)
    index_file = output_dir / "botroyale" / "index.html"
    if not index_file.is_file() or force_remake:
        make_docs()
    popen_path(index_file)


def make_docs(output_dir: Optional[os.PathLike] = None):
    """Clear and create the docs."""
    if not INSTALLED_FROM_SOURCE:
        raise EnvironmentError("Cannot create docs unless installed from source.")
    print("Clearing existing docs...")
    output_dir = _get_output_dir(output_dir)
    if output_dir.is_dir():
        shutil.rmtree(output_dir)
    print("Preparing docs...")
    tpl_lookup.directories.insert(0, str(TEMPLATE_DIR))
    _copy_assets(output_dir)
    _write_guides(output_dir)
    print("Building docs...")
    doc_root = _get_root_package_doc()
    print("Writing new docs...")
    _write_html(doc_root, output_dir)
    print("Make docs done.")


def test_docs():
    """If making the docs raises no warnings."""
    if not INSTALLED_FROM_SOURCE:
        print("Cannot create docs unless installed from source.")
        return False
    with warnings.catch_warnings(record=True) as warning_catcher:
        make_docs()
    if len(warning_catcher) > 0:
        print(f"Found {len(warning_catcher)} warnings:")
        for warning in warning_catcher:
            print(f"  {warning.message}")
        return False
    print("Documentation built sucessfully.")
    return True


def _get_output_dir(output_dir: Optional[os.PathLike]) -> Path:
    if output_dir is None:
        output_dir = get_usr_dir("docs")
    else:
        output_dir /= "docs"
    return output_dir


def _copy_assets(output_dir):
    new_package_dir = output_dir / "botroyale"
    new_package_dir.mkdir(parents=True, exist_ok=True)
    # Copy icon
    shutil.copy(
        PACKAGE_DIR / "icon.png",
        new_package_dir / "icon.png",
    )
    # Copy preview gif
    shutil.copy(
        PACKAGE_DIR / "assets" / "preview.gif",
        new_package_dir / "preview.gif",
    )


def _write_guides(output_dir):
    # TODO: make an html index for the guides, not just copying the md files
    new_guides_dir = output_dir / "botroyale"
    new_guides_dir.mkdir(parents=True, exist_ok=True)
    # Copy guides
    shutil.copytree(
        DOCS_DIR / "guides",
        new_guides_dir / "guides",
    )


def _get_root_package_doc():
    context = Context()
    root_package = Module("botroyale", context=context)
    link_inheritance(context)
    return root_package


def _write_html(doc_root, output_dir):
    for mod in _recursive_mods(doc_root):
        html = mod.html()
        file_path = output_dir / _module_relative_path(mod)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_dump(file_path, html)


def _module_relative_path(mod):
    full_module_name = mod.name
    module_parts = full_module_name.split(".")
    module_name = module_parts[-1]
    file_path = Path()
    for n in module_parts[:-1]:
        file_path /= n
    if mod.is_package:
        file_path /= module_name
        file_path /= "index.html"
    else:
        file_path /= f"{module_name}.html"
    return file_path


def _recursive_mods(mod):
    yield mod
    for submod in mod.submodules():
        yield from _recursive_mods(submod)
