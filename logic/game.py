"""
Home of `logic.game.StandardGameAPI` - the standard implementation of `api.gui.GameAPI`.
"""
from typing import Any, Union, Optional
import random
from util.settings import Settings
from api.logging import logger as glogger
from api.gui import GameAPI as GameAPI, Control, InputWidget
from logic.maps import MAPS, DEFAULT_MAP_NAME, get_map_state
from logic.battle_manager import BattleManager
from logic.map_editor import MapEditor
from bots import BOTS, BaseBot, bot_getter, NotFairError


ADD_PREFIX = '╠+'
FILTER_PREFIX = '╠-'


class StandardGameAPI(GameAPI):
    """A standard implementation of `api.gui.GameAPI`.

    See `StandardGameAPI.get_new_battle` on starting battles and the map editor.
    """

    def get_menu_widgets(self) -> list[InputWidget]:
        """
        Returns a list of widgets for controlling how to start the next battle.

        Includes "Map editor mode" toggle, map selection, bot selection options.

        See: `api.gui.GameAPI.get_menu_widgets`.
        """
        sorted_bot_names = sorted(BOTS.values(), key=lambda b: b.TESTING_ONLY)
        bot_toggles = []
        bot_ignore_toggles = []
        for b in sorted_bot_names:
            prefix = '¬ ' if b.TESTING_ONLY else '» '
            bname = f'{prefix}{b.NAME}'
            bot_toggles.append(InputWidget(bname, 'toggle', sendto=f'{ADD_PREFIX}{b.NAME}'))
            bot_ignore_toggles.append(InputWidget(bname, 'toggle', sendto=f'{FILTER_PREFIX}{b.NAME}'))
        return [
            InputWidget('Map Selection', 'spacer'),
            InputWidget('Map editor mode', 'toggle', sendto='mapedit'),
            InputWidget('Map:', 'select', default=DEFAULT_MAP_NAME, options=MAPS, sendto='map'),
            InputWidget('Bot Selection', 'spacer'),
            InputWidget('Keep fair (equal numbers)', 'toggle', sendto='keep_fair'),
            InputWidget('No dummies', 'toggle', sendto='no_dummies'),
            InputWidget('All selected must play', 'toggle', sendto='all_play'),
            InputWidget('Include bots:', 'spacer'),
            InputWidget('Include all', 'toggle', sendto='select_all'),
            *bot_toggles,
            InputWidget('Filter bots:', 'spacer'),
            InputWidget('Filter all test bots', 'toggle', default=True, sendto='filter_test'),
            *bot_ignore_toggles,
        ]

    def get_new_battle(self, menu_values: dict[str, Any]) -> Optional[Union[BattleManager, MapEditor]]:
        """
        Returns a `logic.battle_manager.BattleManager` or None if it fails to create the battle, or a `logic.map_editor.MapEditor` if "Map editor mode" was set in the main menu.

        See: `api.gui.GameAPI.get_new_battle`.
        """
        map_name = menu_values['map']
        if menu_values['mapedit']:
            return MapEditor(load_map=map_name)
        # Parse arguments from menu values
        state = get_map_state(map_name)
        keep_fair = menu_values['keep_fair']
        no_dummies = menu_values['no_dummies']
        all_play = menu_values['all_play']
        include_testing = not menu_values['filter_test']
        selected_bot_names = None  # will collect all bots
        # Collect bots
        if not menu_values['select_all']:
            # Collect selected bots only
            selected_bot_names = []
            for k, v in menu_values.items():
                if not v or not k.startswith(ADD_PREFIX):
                    continue
                bot_name = k[len(ADD_PREFIX):]  # remove prefix
                selected_bot_names.append(bot_name)
            if not selected_bot_names:
                selected_bot_names = None  # revert to collecting all bots
        # Filter bots
        filter_bot_names = set()
        for k, v in menu_values.items():
            if not v or not k.startswith(FILTER_PREFIX):
                continue
            bot_name = k[len(FILTER_PREFIX):]  # remove prefix
            filter_bot_names.add(bot_name)

        # Make bot getter
        bots = bot_getter(
            selection=selected_bot_names,
            ignore=filter_bot_names,
            include_testing=include_testing,
            keep_fair=keep_fair,
            no_dummies=no_dummies,
            all_play=all_play,
            )
        # Make Battle
        try:
            return BattleManager(
                initial_state=state,
                bot_classes_getter=bots,
                gui_mode=True,
                )
        except NotFairError as e:
            glogger(f'Failed to create new battle: {e}')
            return None
