"""Home of `botroyale.api.bots.BaseBot`, the base class for all bots."""
from typing import NamedTuple, Union, TypeVar
import copy
from botroyale.util.hexagon import Hexagon, ORIGIN
from botroyale.api.logging import logger as glogger
from botroyale.api.actions import Action, Idle
from botroyale.logic.state import State


VFXArgs = dict[str, Union[None, int, float]]
VFXArgsList = list[VFXArgs]


CENTER: Hexagon = ORIGIN
"""Map center. Alias for `botroyale.util.hexagon.ORIGIN`."""


def center_distance(hex: Hexagon) -> int:
    """Returns distance of *hex* from the `CENTER`."""
    return ORIGIN.get_distance(hex)


class BaseBot:
    """The base class for all bots.

    Should be initialized by a `botroyale.logic.battle.Battle`. The
    `BaseBot.setup` method is to be used by the bot to do any startup procedures.

    The `botroyale.logic.battle.Battle` will call `BaseBot.poll_action` as long
    as it is the bot's turn, and is how the bots actually play.
    """

    NAME: str = "BaseBot"
    """The bot class name. Must be unique."""
    SPRITE: str = "bot"
    """The bot class sprite. Must be a name of a file in `assets/sprites`
    (without the .png extension)."""
    TESTING_ONLY: bool = False
    """Marks the bot class as a test bot. Indicates that it should not be used
    by default."""
    COLOR_INDEX: int = 0
    """The color (as an index) of the bot class. See `botroyale.logic.UNIT_COLORS`."""
    logging_enabled: bool = True
    """Enables `BaseBot.logger`."""
    max_ap: int = 100
    """The maximum amount of AP that can be accumulated."""
    ap_regen: int = 50
    """The amount of AP regained per round."""

    def __init__(self, id: int):
        """Initialize the class."""
        self.id: int = id
        """The id of the bot in the battle.

        Is commonly used as an index in lists. Also known as `uid`."""
        self.name: str = self.NAME

    def setup(self, state: State):
        """Used by the bot to perform startup procedures.

        Called in round 0, before any turns have started. When subclassing,
        override this method to prepare the bot.

        Args:
            state: The initial state of the battle.
        """
        pass

    def get_action(self, world_info):
        """Deprecated method to get actions. Use `BaseBot.poll_action` instead.

        .. deprecated:: Use `BaseBot.poll_action` instead.
        """
        return Idle()

    def poll_action(self, state: State) -> Action:
        """Called by a Battle on our turn.

        This method is where a bot "does their turn".

        Args:
            state: Current state of the battle.

        Returns:
            Action object.
        """
        # Backward compatibility for old get_action call.
        glogger('get_action will be DEPRECATED, please override "poll_action" instead.')
        wi = _state_to_world_info(state)
        return self.get_action(wi)

    def gui_click(self, hex: Hexagon, button: str) -> VFXArgsList:
        """Called when we are clicked on in the GUI.

        Left click: will call `BaseBot.gui_click_debug`.

        Middle click: will call `BaseBot.gui_click_debug_alt`.

        Right click: will toggle `BaseBot.logging_enabled` for this bot instance.

        See `botroyale.logic.battle_manager.BattleManager.handle_hex_click`.

        Args:
            hex: The hex on which the unit was clicked.
            button: The name of the mouse button that was clicked with. May be
                one of: *left*, *right*, *middle*, *mouse1*, *mouse2*, etc.

        Returns:
            None, or a list of dictionaries of vfx keyword arguments.
                See `botroyale.api.gui.VFX`.
        """
        if button == "left":
            return self.gui_click_debug(hex)
        elif button == "right":
            self.logging_enabled = not self.logging_enabled
            glogger(f"{self} logging: {self.logging_enabled}")
            vfx_name = "mark-green" if self.logging_enabled else "mark-red"
            return [
                {
                    "name": vfx_name,
                    "hex": hex,
                    "direction": None,
                    "expire_seconds": 0.5,
                },
            ]
        elif button == "middle":
            return self.gui_click_debug_alt(hex)

    def gui_click_debug(self, hex: Hexagon) -> VFXArgsList:
        """Called when we are clicked on with the left mouse button.

        Args:
            hex: The hex on which we were clicked.

        Returns:
            None, or a list of dictionaries of vfx keyword arguments.
                See `botroyale.api.gui.VFX`.
        """
        return [
            {"name": "mark-blue", "hex": hex},
        ]

    def gui_click_debug_alt(self, hex: Hexagon) -> VFXArgsList:
        """Called when we are clicked on in the GUI with the middle mouse button.

        Args:
            hex: The hex on which we were clicked.

        Returns:
            None, or a list of dictionaries of vfx keyword arguments.
                See `botroyale.api.gui.VFX`.
        """
        return [
            {"name": "mark-blue", "hex": hex},
        ]

    def logger(self, text: str):
        """Logger for the bot.

        Is enabled/disabled by `BaseBot.logging_enabled`.
        """
        if self.logging_enabled:
            glogger(text)

    def __repr__(self):
        """Repr."""
        return f"<Bot #{self.id} {self.name}>"

    @property
    def gui_label(self):
        """Formatted name with uid."""
        id_label = f"#{self.id}"
        return f"{id_label:>3} {self.name}"


BotLike = TypeVar("BotLike", bound=BaseBot)
"""A type variable for subclasses of `BaseBot`."""


# Backward compatibility
class world_info(NamedTuple):
    """Will be removed in v2.0. Replaced by `botroyale.logic.state.State`."""

    positions: list
    walls: set
    pits: set
    ring_radius: int
    alive_mask: list
    turn_count: int
    round_count: int
    ap: list
    round_ap_spent: list
    round_remaining_turns: list


def _state_to_world_info(state):
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


__pdoc__ = {"world_info": False}