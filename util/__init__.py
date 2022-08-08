from pathlib import Path


TITLE = 'Bot Royale'
VERSION = 1.000
FULL_TITLE = f'{TITLE} v{VERSION:.3f}'
DESCRIPTION = 'A battle royale for bots.'


PROJ_DIR = Path(__file__).parent.parent
assert PROJ_DIR.is_dir()
assert (PROJ_DIR / 'main.py').is_file()


def file_load(file):
    with open(file, 'r') as f:
        d = f.read()
    return d


def file_dump(file, d, clear=True):
    with open(file, 'w' if clear else 'a') as f:
        f.write(d)
