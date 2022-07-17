from util.hexagon import Hex
from collections import namedtuple
from api.logging import logger as glogger
from api.actions import Move, Push


world_info = namedtuple('WorldInfo', [
    'positions',  # list of tiles
    'walls',  # set of tiles
    'pits',  # set of tiles
    'ring_radius',  # int
    'alive_mask',  # ndarray mask
    'turn_count',  # int
    'round_count',  # int
    'ap',  # ndarray
    'round_ap_spent',  # ndarray
    # when round_priority is empty, round is over.
    'round_remaining_turns',  # list
    ])


class BaseBot:
    NAME = "BaseBot"
    SPRITE = "circle"
    TESTING_ONLY = False
    COLOR_INDEX = 0
    logging_enabled = False

    def __init__(self, id: int):
        self.id = id
        self.name = self.NAME

    def setup(self, wi):
        pass

    def get_action(self, world_state):
        return Move(Hex(0, 0))

    def gui_click(self, hex, button):
        """
        Called when we are clicked on in the GUI.
        May return a list of vfx args.
        """
        if button == 'left':
            return self.gui_click_debug(hex)
        elif button == 'right':
            self.logging_enabled = not self.logging_enabled
            glogger(f'{self} logging: {self.logging_enabled}')
            vfx_name = 'mark-green' if self.logging_enabled else 'mark-red'
            return [
                {'name': vfx_name, 'hex': hex, 'neighbor': None, 'real_time': 0.5},
            ]
        elif button == 'middle':
            return self.gui_click_debug_alt(hex)

    def gui_click_debug(self, hex):
        """
        Called by gui_click when we are clicked on in the GUI with the left
        mouse button. May return a list of vfx args.
        """
        return [
            {'name': 'mark-blue', 'hex': hex, 'neighbor': None},
        ]

    def gui_click_debug_alt(self, hex):
        """
        Called by gui_click when we are clicked on in the GUI with the middle
        mouse button. May return a list of vfx args.
        """
        return [
            {'name': 'mark-blue', 'hex': hex, 'neighbor': None},
        ]

    def logger(self, text):
        if self.logging_enabled:
            glogger(text)

    def __repr__(self):
        return f'<Bot #{self.id} {self.name}>'
