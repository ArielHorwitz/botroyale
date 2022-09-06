"""Build the docs based on local source code.

Uses `pdoc3` library to automatically read source code and produce HTML
documentation. Will delete the output folder and recreate docs.
"""
import shutil
from pdoc import Module, Context, tpl_lookup, link_inheritance
from botroyale.util.file import file_dump, file_load, popen_path
from botroyale.util import PROJ_DIR, PACKAGE_DIR, VERSION


DOCS_ROOT = PROJ_DIR / "docs"
PACKAGE_OUTPUT_DIR = DOCS_ROOT / "botroyale"
GUIDE_PACKAGE_DIR = PACKAGE_DIR / "guides"
TEMPLATE_DIR = DOCS_ROOT / "templates"
INDEX_FILE = PACKAGE_OUTPUT_DIR / "index.html"


def open_docs(force_remake: bool = False):
    """Opens the docs in default browser, using `botroyale.util.file.popen_path`."""
    if not INDEX_FILE.is_file() or force_remake:
        make_docs()
    popen_path(INDEX_FILE)


def make_docs(dry_run: bool = False):
    """Clear and create the docs."""
    print("Clearing existing docs...")
    if PACKAGE_OUTPUT_DIR.is_dir():
        if dry_run:
            print(f"Would delete recursively: {PACKAGE_OUTPUT_DIR}")
            print(f"Would delete recursively: {GUIDE_PACKAGE_DIR}")
        else:
            shutil.rmtree(PACKAGE_OUTPUT_DIR)
            shutil.rmtree(GUIDE_PACKAGE_DIR)
    print("Preparing docs...")
    tpl_lookup.directories.insert(0, str(TEMPLATE_DIR))
    _generate_guides(dry_run)
    _generate_fixed_readme(dry_run)
    print("Building docs...")
    context = Context()
    root_package = Module(".", context=context)
    link_inheritance(context)
    print("Writing new docs...")
    for mod in _recursive_mods(root_package):
        html = mod.html()
        file_path = _module_path(mod)
        if dry_run:
            print(f"Would write html at: {file_path}")
        else:
            _write_html(file_path, html)
    if dry_run:
        print("Use dry_run=False to apply changes.")
    else:
        print("Make docs done.")


def _module_path(mod):
    full_module_name = mod.name
    module_parts = full_module_name.split(".")
    module_name = module_parts[-1]
    file_path = DOCS_ROOT
    for n in module_parts[:-1]:
        file_path /= n
    if mod.is_package:
        file_path /= module_name
        file_path /= "index.html"
    else:
        file_path /= f"{module_name}.html"
    return file_path


def _write_html(file_path, html):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_dump(file_path, html)


def _recursive_mods(mod):
    yield mod
    for submod in mod.submodules():
        yield from _recursive_mods(submod)


def _generate_fixed_readme(dry_run: bool = False):
    """Generate a "fixed" README for the html docs.

    We want to use the readme for our docs index page. While the readme is
    designed to work well for Github, not so much for the html docs. A "fixed"
    readme will be generated in the docs folder (hence the
    `.. include:: ./docs/README.md` in botroyale.__init__.py). Since the fixed
    readme has a difference location, the relative links also need to be fixed.

    And so the following is done before writing the fixed readme:
    - Insert version
    - Insert link to the guides
    - Fix assets folder relative link to absolute link
    """
    readme_path = PROJ_DIR / "README.md"
    fixed_readme_path = DOCS_ROOT / "README.md"
    # Add version and link to guides up top
    added_lines = "\n".join(
        [
            f"Documentation built on `v{VERSION}`.\n",
            "Check out the [guides](guides/index.html) for many resources, "
            "from beginner to advanced.\n",
        ]
    )
    fixed_readme = f"{added_lines}\n{file_load(readme_path)}"
    # Fix the assets path for the preview gif
    fixed_assets_path = PACKAGE_DIR / "assets"
    oldstr, newstr = "botroyale/assets/", f"{str(fixed_assets_path)}/"
    fixed_readme = fixed_readme.replace(oldstr, newstr)
    if dry_run:
        print(f"Would fix readme to: {fixed_readme_path}")
    else:
        file_dump(fixed_readme_path, fixed_readme)


def _generate_guides(dry_run: bool = False):
    """Generate a module with a `..inclue::guide.md` for the guides."""
    sources = DOCS_ROOT / "guides"
    GUIDE_PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    root_guide = GUIDE_PACKAGE_DIR / "__init__.py"
    if dry_run:
        print(f"Would write guide module: {root_guide}")
    else:
        file_dump(root_guide, '"""A collection of guides."""')
    for md in _recursive_guides(sources):
        rel_path = md.relative_to(sources).parent
        mod = GUIDE_PACKAGE_DIR / rel_path / f"{md.stem}.py"
        if dry_run:
            print(f"Would write guide module: {mod}")
        else:
            mod.parent.mkdir(parents=True, exist_ok=True)
            file_dump(mod, f'""".. include:: {md}"""')


def _recursive_guides(source):
    for child in source.iterdir():
        if child.is_file():
            yield child
        elif child.is_dir():
            yield from _recursive_guides(child)
