"""Version upgrade script.

Applies a version change:

- Lists all actions that will be performed
- Prompts user in terminal for confirmation
- Modifies necessary files
- Commits to local git repo
- May create a tag in local git repo

Example usage (given version `1.2.3`):

```bash
# To upgrade to: 2.0.0-rc.1
python main.py upgrade major ++p rc.1

# To upgrade to: 1.3.0+build_data.123
python main.py upgrade minor ++b build_data.123

# To upgrade to: 1.2.4+COMMITHASH
python main.py upgrade patch commit

# To upgrade to: 2.0.0-alpha+b123 and add a tag
python main.py upgrade tag major ++p alpha ++b b123

# To "undo" the last version upgrade -- use only if HEAD points to said commit
python main.py upgrade undo
```
"""
from typing import Optional
from pathlib import Path
import subprocess
from functools import partial
from util import VERSION, PROJ_DIR, MAIN_ARGS
from util.file import file_dump, file_load


SUBJECT_PREFIX = "Upgrade to v"
MISSING_GIT_ERROR = EnvironmentError(
    f"Could not find git repo for {PROJ_DIR} (CWD: {Path.cwd()})"
)
UNCLEAN_GIT_ERROR = RuntimeError(
    "Unclean git status, please commit or stash changes. Run `git status` for details."
)


def upgrade_version(write_tag: bool = False, **kwargs):
    """Apply a new version to the project, and commit to local git repo.

    Args:
        write_tag: Create a tag in the git repo.
        kwargs: Keyword arguments for `increment_version`.
    """
    if not is_git_clean():
        raise UNCLEAN_GIT_ERROR
    new_version = increment_version(**kwargs)
    if new_version == VERSION:
        raise ValueError(f"No version change: {VERSION=}, {new_version=}")
    confirm = f"Ready to upgrade version: {VERSION}  ->  {new_version}"
    cmds = [
        partial(file_dump, PROJ_DIR / "VERSION", new_version),
        partial(subprocess.run, ["git", "restore", "--staged", "."]),
        partial(subprocess.run, ["git", "add", "VERSION"]),
        partial(
            subprocess.run, ["git", "commit", "-m", f"{SUBJECT_PREFIX}{new_version}"]
        ),
    ]
    if write_tag:
        cmds.append(
            partial(
                subprocess.run,
                [
                    "git",
                    "tag",
                    "-a",
                    f"v{new_version}",
                    "-m",
                    f"{SUBJECT_PREFIX}{new_version}",
                ],
            )
        )
    r = _run_commands(cmds, confirm_prompt=confirm)
    if r:
        print(f"Completed upgrade to version {new_version}.")


def undo_upgrade():
    """Resets HEAD, deletes the tag, and undoes changes to the project files."""
    if not is_git_clean():
        raise UNCLEAN_GIT_ERROR
    head_subject = get_head_subject()
    confirm = (
        f"Ready to undo commit: {get_head_hash()[:6]} {head_subject} "
        "(code version: {VERSION})"
    )
    # Check `in` and not `startswith` since the head_subject may be encased
    # in quotation marks
    if SUBJECT_PREFIX not in head_subject:
        confirm = "\n".join(
            [
                confirm,
                "=" * 100,
                (
                    "WARNING! Commit suspected to not be a "
                    f"version upgrade commit: {head_subject}"
                ),
                "=" * 100,
            ]
        )
    r = _run_commands(
        [
            partial(subprocess.run, ["git", "reset", "HEAD^"]),
            partial(subprocess.run, ["git", "checkout", "--", "VERSION"]),
            partial(subprocess.run, ["git", "tag", "-d", f"v{VERSION}"]),
        ],
        confirm_prompt=confirm,
    )
    if r:
        print(f"Completed undo of version {VERSION}")
        new_version = file_load(PROJ_DIR / "VERSION").split("\n")[0]
        print(f"Now on version: {new_version}")


def increment_version(
    old_version: Optional[str] = None,
    major: bool = False,
    minor: bool = False,
    patch: bool = False,
    prerelease: Optional[str] = None,
    build_data: Optional[str] = None,
    include_commit_hash: bool = False,
) -> str:
    """Get a new version using the Semantic Version convention.

    Unless specified, the prerelease identifier and build metadata will not be
    included.

    See: [Semantic Versioning](https://semver.org/)

    Args:
        old_version: Defaults to current project version.
        major: Increment the major version.
        minor: Increment the minor version. Ignored if *major* is True.
        patch: Increment the patch version. Ignored if *major* or *minor* are True.
        prerelease: Prerelease identifier.
        build_data: Build metadata.

    Returns:
        A string of the new Semantic Version.
    """
    if old_version is None:
        old_version = VERSION
    # Current version
    if old_version.startswith("v"):
        old_version = old_version[1:]
    old_version = old_version.split("+", 1)[0]  # Remove previous build data
    old_core = old_version.split("-", 1)[0]  # Remove previous prerelease
    # New version
    new_core = [int(_) for _ in old_core.split(".")]
    if bool(major):
        new_core[0] += 1
        new_core[1] = 0
        new_core[2] = 0
    elif bool(minor):
        new_core[1] += 1
        new_core[2] = 0
    elif bool(patch):
        new_core[2] += 1
    new_core = ".".join(str(_) for _ in new_core)
    new_prerelease = f"-{prerelease}" if prerelease else ""
    new_build_data = f"+{build_data}" if build_data else ""
    if include_commit_hash:
        new_build_data += "-" if new_build_data else "+"
        new_build_data += get_head_hash()[:6]
    new_version = "".join([new_core, new_prerelease, new_build_data])
    return new_version


def is_git() -> bool:
    """If the cwd is at project's root and contains a local git repo."""
    # Confirm it is the correct directory
    if not Path.cwd().samefile(PROJ_DIR):
        return False
    # Confirm there is a git repo
    is_inside_tree = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], capture_output=True
    )
    if not is_inside_tree.returncode == 0:
        return False
    return True


def is_git_clean() -> bool:
    """If the git working tree is clean."""
    if not is_git():
        raise MISSING_GIT_ERROR
    clean_tree = subprocess.run(["git", "diff", "--exit-code"], capture_output=True)
    clean_tree_staged = subprocess.run(
        ["git", "diff", "--cached", "--exit-code"], capture_output=True
    )
    if clean_tree.returncode or clean_tree_staged.returncode:
        return False
    return True


def get_head_hash() -> str:
    """The commit hash of the HEAD of the project's local git repo."""
    if not is_git():
        raise MISSING_GIT_ERROR
    console_output = subprocess.check_output(["git", "rev-parse", "HEAD"])
    return console_output.decode("ascii").strip()


def get_head_subject() -> str:
    """The commit message subject of the HEAD of the project's local git repo."""
    if not is_git():
        raise MISSING_GIT_ERROR
    console_output = subprocess.check_output(
        ["git", "show", '--pretty=format:"%s"', "--no-patch"]
    )
    return console_output.decode("ascii").strip()


def _collect_args():
    # Core
    major = "major" in MAIN_ARGS.opargs
    minor = "minor" in MAIN_ARGS.opargs
    patch = "patch" in MAIN_ARGS.opargs
    prerelease = None
    if "++p" in MAIN_ARGS.opargs:
        prerelease = MAIN_ARGS.opargs[MAIN_ARGS.opargs.index("++p") + 1]
    # Build data
    build_data = None
    if "++b" in MAIN_ARGS.opargs:
        build_data = MAIN_ARGS.opargs[MAIN_ARGS.opargs.index("++b") + 1]
    include_commit_hash = "commit" in MAIN_ARGS.opargs
    return {
        "major": major,
        "minor": minor,
        "patch": patch,
        "prerelease": prerelease,
        "build_data": build_data,
        "include_commit_hash": include_commit_hash,
    }


def _run_commands(commands, confirm_prompt=False):
    print("Queued commands:")
    print("\n".join(f"  {cmd}" for cmd in commands))
    if confirm_prompt:
        print(confirm_prompt)
        confirm = (
            input(
                'Enter "confirm" to proceed (anything else or leave empty to abort): '
            )
            == "confirm"
        )
        if not confirm:
            print("Aborted.")
            return False
    for cmd in commands:
        cmd()
    return True


def run():
    """Uses command line arguments to call `upgrade_version`."""
    if "undo" in MAIN_ARGS.opargs:
        undo_upgrade()
        return
    write_tag = "tag" in MAIN_ARGS.opargs
    increment_args = _collect_args()
    upgrade_version(write_tag=write_tag, **increment_args)
