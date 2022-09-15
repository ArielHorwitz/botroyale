"""Documentation utility.

This module includes tools to test, create, and open the documentation locally.
Project must be installed from source and with dev requirements, see:
`botroyale.guides.contributing`.

To create and open the docs:
```noformat
botroyale docs --help
```

### Creating the docs
Uses the `pdoc3` library to automatically read source code and produce HTML
documentation. Will delete the output folder and recreate docs. Default output
folder is in the usr dir.

### Testing the docs
See `botroyale.util.code` for more information about testing.
"""
from typing import Optional
import shutil
import os
import traceback
import sys
import warnings
import argparse
from pathlib import Path
from pdoc import Module, Context, tpl_lookup, link_inheritance
from botroyale.util import PROJ_DIR, PACKAGE_DIR, INSTALLED_FROM_SOURCE
from botroyale.util.file import popen_path, file_dump, get_usr_dir


DOCS_DIR = PROJ_DIR / "docs"
TEMPLATE_DIR = DOCS_DIR / "templates"
USER_DIR = "botroyale"


def entry_point_docs(args) -> int:
    """Script entry point to run the documentation utility."""
    parser = argparse.ArgumentParser(
        description="Generate and view Bot Royale documentation",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="force recreating the docs",
    )
    parser.add_argument(
        "--no-open",
        "--no",
        action="store_true",
        help="don't open the docs",
    )
    args = parser.parse_args(args)
    make_docs(force_remake=args.force)
    if not args.no_open:
        open_docs()
    return 0


def open_docs(
    output_dir: Optional[os.PathLike] = None,
    force_remake: bool = False,
):
    """Opens the docs in default browser.

    Generates the docs if missing or if *force_remake*.
    """
    output_dir = _get_output_dir(output_dir)
    make_docs(output_dir, force_remake=force_remake)
    index_file = _get_index_file(output_dir)
    popen_path(index_file)


def docs_exist(output_dir: Optional[os.PathLike] = None) -> bool:
    """Return True if docs exist in *output_dir*."""
    output_dir = _get_output_dir(output_dir)
    index_file = _get_index_file(output_dir)
    return index_file.is_file()


def make_docs(
    output_dir: Optional[os.PathLike] = None,
    force_remake: bool = False,
):
    """Create the docs if missing or if *force_remake*."""
    output_dir = _get_output_dir(output_dir)
    if force_remake or not docs_exist(output_dir):
        _make_docs(output_dir)


def test_docs() -> bool:
    """If making the docs raises no warnings or exceptions."""
    if not INSTALLED_FROM_SOURCE:
        print("Cannot create docs unless installed from source.")
        return False
    issues = []
    with warnings.catch_warnings(record=True) as warning_catcher:
        try:
            make_docs(force_remake=True)
        except Exception as e:
            issues.append(f"  Error: {e}")
    issues = [f"  Warning: {w.message}" for w in warning_catcher] + issues
    if len(issues) > 0:
        print(f"Found {len(issues)} issues:")
        print("\n".join(issues))
        return False
    print("Documentation built sucessfully.")
    return True


def _get_index_file(output_dir: Optional[os.PathLike]) -> Path:
    output_dir = _get_output_dir(output_dir)
    return output_dir / "botroyale" / "index.html"


def _get_output_dir(output_dir: Optional[os.PathLike]) -> Path:
    return get_usr_dir("docs") if output_dir is None else output_dir


def _make_docs(output_dir: Optional[os.PathLike] = None):
    """Clear and create the docs."""
    if not INSTALLED_FROM_SOURCE:
        raise EnvironmentError("Cannot create docs unless installed from source.")
    output_dir = _get_output_dir(output_dir)
    if output_dir.is_dir():
        print("Clearing existing docs...")
        shutil.rmtree(output_dir)
    print("Preparing docs...")
    tpl_lookup.directories.insert(0, str(TEMPLATE_DIR))
    _copy_assets(output_dir)
    print("Building docs...")
    doc_root = _get_root_package_doc()
    print("Writing new docs...")
    _write_html(doc_root, output_dir)
    print("Make docs done.")


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


def _recursive_files(dir, _top_dir=None):
    _top_dir = dir if _top_dir is None else _top_dir
    for child in dir.iterdir():
        if child.is_dir():
            yield from _recursive_files(child, _top_dir)
        elif child.is_file():
            yield child.relative_to(_top_dir)


def _get_root_package_doc():
    try:
        _write_guides()
        context = Context()
        root_package = Module("botroyale", context=context)
        link_inheritance(context)
    except Exception as e:
        print("".join(traceback.format_exception(*sys.exc_info())))
        _delete_guides()
        raise e
    _delete_guides()
    return root_package


def _write_guides():
    guides_md = PACKAGE_DIR.parent / "docs" / "guides"
    guides_py = PACKAGE_DIR / "guides"
    if guides_py.is_dir():
        warnings.warn(f"Guides subpackage dir already exists: {guides_py}")
    guides_py.mkdir(exist_ok=True)
    guides = _recursive_files(guides_md)
    for path in guides:
        path_py = guides_py / path.parent / f"{path.stem}.py"
        path_py.parent.mkdir(parents=True, exist_ok=True)
        path_md = _windows_compatibility(str(guides_md / path))
        include_md = f'""".. include:: {path_md}"""'
        file_dump(path_py, include_md)


def _delete_guides():
    guides_py = PACKAGE_DIR / "guides"
    shutil.rmtree(guides_py)


def _write_html(doc_root, output_dir):
    for mod in _recursive_mods(doc_root):
        with warnings.catch_warnings(record=True) as warning_catcher:
            html = mod.html()
        for w in warning_catcher:
            warning_str = w.message.args[0]
            warnings.warn(warning_str)
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


def _windows_compatibility(s):
    """Multiply backslashes in a string for windows path compatibility."""
    return s.replace("\\", "\\\\")
