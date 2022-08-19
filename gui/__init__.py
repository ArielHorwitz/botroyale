import numpy as np
from api.logging import logger as glogger
from util import PROJ_DIR
from util.settings import Settings


GUI_DEBUG = Settings.get('logging.gui', False)
ASSETS_DIR = PROJ_DIR / 'assets'
DEFAULT_FONT_NAME = Settings.get('gui.font', 'liberation')
FONT = str(ASSETS_DIR / 'fonts' / f'{DEFAULT_FONT_NAME}.ttf')


def center_sprite(pos, size):
    assert len(pos) == 2 and len(size) == 2
    r = np.array(pos) - (np.array(size) / 2)
    return [int(r[0]), int(r[1])]


def logger(m):
    if GUI_DEBUG:
        glogger(m)
