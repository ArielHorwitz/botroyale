import copy
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


def state_to_world_info(state):
    return world_info(
        positions=copy.copy(state.positions),
        walls=copy.copy(state.walls),
        pits=copy.copy(state.pits),
        ring_radius=state.death_radius,
        alive_mask=copy.deepcopy(state.alive_mask),
        turn_count=state.turn_count,
        round_count=state.round_count,
        ap=copy.deepcopy(state.ap),
        round_ap_spent=copy.deepcopy(state.round_ap_spent),
        round_remaining_turns=copy.deepcopy(state.round_remaining_turns),
        )


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

    def get_action(self, world_info):
        return Move(Hex(0, 0))

    def poll_action(self, state):
        """
        Called by a Battle on our turn.
        Receive a State object and return an Action object.
        """
        # Backward compatibility for old get_action call.
        glogger(f'get_action will be DEPRECATED, please override "poll_action" instead.')
        wi = state_to_world_info(state)
        return self.get_action(wi)

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
                {'name': vfx_name, 'hex': hex, 'neighbor': None, 'expire_seconds': 0.5},
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
