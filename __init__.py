""".. include:: ./docs/README.md"""  # noqa
# We pass a fixed version of the README to the docstring, see below

from util import PROJ_DIR, VERSION
from util.file import file_load, file_dump


def _generate_fixed_readme():
    """Generate a "fixed" README for the html docs.

    We want to use the readme for our docs index page. While the readme is
    designed to work well for Github, not so much for the html docs. A "fixed"
    readme will be generated in the docs folder (hence the
    `.. include:: ./docs/README.md` above). Since the fixed readme has a
    difference location, the relative links also need to be fixed. And so the
    following is done before writing the fixed readme:

    - Insert version
    - Insert absolute link to the guides
    - Fix assets folder relative link to absolute link
    """
    readme_path = PROJ_DIR / "README.md"
    fixed_readme_path = PROJ_DIR / "docs" / "README.md"
    # Add version and link to guides up top
    added_lines = "\n".join(
        [
            f"Documentation built on `v{VERSION}`.\n",
            f"Check out `{PROJ_DIR.name}.guides` for many resources, "
            "from beginner to advanced.\n",
        ]
    )
    fixed_readme = f"{added_lines}\n{file_load(readme_path)}"
    # Fix the assets path for the preview gif
    fixed_assets_path = PROJ_DIR / "assets"
    oldstr, newstr = "assets/", f"{str(fixed_assets_path)}/"
    fixed_readme = fixed_readme.replace(oldstr, newstr)
    file_dump(fixed_readme_path, fixed_readme)


_generate_fixed_readme()


__version__ = VERSION
__pdoc__ = {
    "main": False,
    "gui": False,
    "docs": False,
    "dev": False,
    "venv": False,
}
