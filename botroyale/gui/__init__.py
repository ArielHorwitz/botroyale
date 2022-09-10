import numpy as np
from botroyale.api.logging import logger as glogger
from botroyale.util import PACKAGE_DIR
from botroyale.util import settings


GUI_DEBUG = settings.get('logging.gui')
ASSETS_DIR = PACKAGE_DIR / 'assets'
DEFAULT_FONT_NAME = settings.get('gui.fonts.default')
FONT = str(ASSETS_DIR / 'fonts' / f'{DEFAULT_FONT_NAME}.ttf')
FONT_SIZE = settings.get('gui.fonts.size')


def center_sprite(pos, size):
    assert len(pos) == 2 and len(size) == 2
    r = np.array(pos) - (np.array(size) / 2)
    return [int(r[0]), int(r[1])]


def logger(m):
    if GUI_DEBUG:
        glogger(m)
