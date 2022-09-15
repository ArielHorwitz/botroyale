"""Home of `botroyale.logic.game.StandardGameAPI`.

The the standard implementation of `botroyale.api.gui.GameAPI`.
"""
from typing import Any, Union, Optional
from botroyale.gui import logger
from botroyale.api.gui import GameAPI, InputWidget
from botroyale.api.bots import BOTS, BotSelection, NotFairError
from botroyale.logic.maps import MAPS, DEFAULT_MAP_NAME, get_map_state
from botroyale.logic.battle_manager import BattleManager
from botroyale.logic.map_editor import MapEditor


BOT_SENDTO_PREFIX = "╠"


def _get_sorted_bots():
    return sorted(BOTS.values(), key=lambda b: b.TESTING_ONLY)


def _get_normal_bots():
    return [b for b in _get_sorted_bots() if not b.TESTING_ONLY]


def _get_testing_bots():
    return [b for b in _get_sorted_bots() if b.TESTING_ONLY]


class StandardGameAPI(GameAPI):
    """A standard implementation of `botroyale.api.gui.GameAPI`.

    See `StandardGameAPI.get_new_battle` on starting battles and the map editor.
    """

    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super().__init__(*args, **kwargs)
        self.selected_bots = []
        self.menu_values = dict(
            editor=False,
            map=DEFAULT_MAP_NAME,
            show_selected=False,
            show_filter="",
            enable_testing=False,
            keep_fair=False,
            no_dummies=False,
            all_play=False,
            max_repeat="",
        )
        self.last_error = ""
        self._sorted_bots = _get_sorted_bots()
        self._normal_bots = _get_normal_bots()
        self._testing_bots = _get_testing_bots()

    @property
    def _bots_showing(self) -> list[type]:
        showing = []
        for bot in self._sorted_bots:
            if self.menu_values["show_selected"] and bot in self.selected_bots:
                showing.append(bot)
                continue
            if bot.TESTING_ONLY and not self.menu_values["enable_testing"]:
                continue
            if self.menu_values["show_filter"]:
                if self.menu_values["show_filter"].lower() not in bot.NAME.lower():
                    continue
            showing.append(bot)
        return showing

    def _get_bot_widgets(self) -> list[InputWidget]:
        widgets = []
        for bot in self._bots_showing:
            selected = bot in self.selected_bots
            label = f"<TEST> {bot.NAME}" if bot.TESTING_ONLY else bot.NAME
            iw = InputWidget(
                label,
                "toggle",
                default=selected,
                sendto=f"{BOT_SENDTO_PREFIX}{bot.NAME}",
            )
            widgets.append(iw)
        return widgets

    def _add_showing(self):
        for bot in self._bots_showing:
            self._toggle_bot(bot, set_as=True)

    def _remove_showing(self):
        for bot in self._bots_showing:
            self._toggle_bot(bot, set_as=False)

    def _remove_testing(self):
        for bot in self._testing_bots:
            self._toggle_bot(bot, set_as=False)

    def _toggle_bot(self, bot, set_as=None):
        if not self.menu_values["enable_testing"] and bot.TESTING_ONLY:
            set_as = False
        if set_as is not None:
            if set_as == (bot in self.selected_bots):
                return
        if bot in self.selected_bots:
            self.selected_bots.remove(bot)
        else:
            self.selected_bots.append(bot)

    def _get_battle_widgets(self) -> list[InputWidget]:
        if self.menu_values["show_selected"] and len(self._bots_showing) == 0:
            self.menu_values["show_selected"] = False
        bot_widgets = self._get_bot_widgets()
        return [
            # Map
            InputWidget("Map Selection", "divider"),
            InputWidget("Map editor mode", "toggle", sendto="editor"),
            InputWidget(
                "Map:",
                "select",
                default=self.menu_values["map"],
                options=MAPS,
                sendto="map",
            ),
            # Bot settings
            InputWidget("Bot Selection", "divider"),
            InputWidget("Add all", "toggle", sendto="add_all"),
            InputWidget("Remove all", "toggle", sendto="remove_all"),
            InputWidget(
                "Filter bots:",
                "text",
                default=self.menu_values["show_filter"],
                sendto="show_filter",
            ),
            InputWidget("Clear filter", "toggle", sendto="clear_filter"),
            InputWidget(
                "Show selected only",
                "toggle",
                default=self.menu_values["show_selected"],
                sendto="show_selected",
            ),
            InputWidget(
                "Enable testing bots",
                "toggle",
                default=self.menu_values["enable_testing"],
                sendto="enable_testing",
            ),
            # Competitive settings
            InputWidget("Competitive Settings", "spacer"),
            InputWidget(
                "All selected must play",
                "toggle",
                default=self.menu_values["all_play"],
                sendto="all_play",
            ),
            InputWidget(
                "Keep fair (equal numbers)",
                "toggle",
                default=self.menu_values["keep_fair"],
                sendto="keep_fair",
            ),
            InputWidget(
                "No dummies",
                "toggle",
                default=self.menu_values["no_dummies"],
                sendto="no_dummies",
            ),
            InputWidget(
                "Max per bot",
                "text",
                default=self.menu_values["max_repeat"],
                sendto="max_repeat",
            ),
            # Bot toggles
            InputWidget("Bots", "divider"),
            *bot_widgets,
        ]

    def _get_editor_widgets(self) -> list[InputWidget]:
        return [
            InputWidget("Map Selection", "divider"),
            InputWidget("Map editor mode", "toggle", default=True, sendto="editor"),
            InputWidget(
                "Based on map:",
                "select",
                default=self.menu_values["map"],
                options=MAPS,
                sendto="map",
            ),
        ]

    def get_menu_widgets(self) -> list[InputWidget]:
        """Return a list of widgets for controlling how to start the next battle.

        Includes "Map editor mode" toggle, map selection, bot selection options.

        See: `botroyale.api.gui.GameAPI.get_menu_widgets`.
        """
        if self.menu_values["editor"]:
            return self._get_editor_widgets()
        return self._get_battle_widgets()

    def handle_menu_widget(
        self, widgets: list[str], menu_values: dict[str, Any]
    ) -> bool:
        """Widgets are set based on battle/map editor modes.

        See: `botroyale.api.gui.GameAPI.handle_menu_widget`.
        """
        # Update our menu values
        relevant_keys = set(self.menu_values.keys()) & set(menu_values.keys())
        for k in relevant_keys:
            self.menu_values[k] = menu_values[k]
        # Clear last error if user changed anything
        if widgets:
            self.last_error = ""
        # Do not recreate menu if user is typing text
        text_widgets = {"show_filter", "max_repeat"} & set(widgets)
        if text_widgets and len(widgets) == 1:
            return False
        # Clear filter text if necessary
        clear_filter_widgets = {"clear_filter", "show_selected"}
        if clear_filter_widgets & set(widgets):
            self.menu_values["show_filter"] = ""
        # Handle widget interactions
        for widget in widgets:
            logger(f'User set "{widget}" in main menu to: {menu_values[widget]}')
            if widget == "add_all":
                self._add_showing()
            elif widget == "remove_all":
                self._remove_showing()
            elif widget == "enable_testing" and not self.menu_values["enable_testing"]:
                self._remove_testing()
            elif widget.startswith(BOT_SENDTO_PREFIX):
                bname = widget[len(BOT_SENDTO_PREFIX) :]
                self._toggle_bot(BOTS[bname])
        return True

    def get_info_panel_text(self) -> str:
        """Overrides: `GameAPI.get_info_panel_text`."""
        if self.menu_values["editor"]:
            return "\n".join(
                [
                    "[b][u]Map Editor[/u][/b]",
                    "",
                    "Press spacebar to start editing.",
                    "",
                    'Saved maps overwrite the "custom.json" map. Rename the '
                    "file to save the custom map permanently (then restart the "
                    "app to refresh).",
                ]
            )
        map = self.menu_values["map"]
        bots = [f"  » {b.NAME}" for b in self.selected_bots]
        max_bot_list = 15
        showing = self._bots_showing
        if len(self.selected_bots) > max_bot_list:
            bots = bots[: max_bot_list - 1]
            remaining = len(self.selected_bots) - max_bot_list + 1
            bots.append(f"  ... and {remaining} more")
        return "\n".join(
            [
                "[b][u]New Battle[/u][/b]",
                "",
                f"[i]{self.last_error}[/i]",
                "",
                f"Map:      {map}",
                "",
                f"Showing:  {len(showing)} bots",
                f"[u]Selected: {len(self.selected_bots)} bots[/u]",
                *bots,
            ]
        )

    def get_new_battle(
        self, menu_values: dict[str, Any]
    ) -> Optional[Union[BattleManager, MapEditor]]:
        """Return a `botroyale.api.gui.BattleAPI`.

        Returns a `botroyale.logic.battle_manager.BattleManager` or None if it fails to
        create the battle, or a `botroyale.logic.map_editor.MapEditor` if map editor
        mode was set in the main menu.

        See: `botroyale.api.gui.GameAPI.get_new_battle`.
        """
        map_name = menu_values["map"]
        if menu_values["editor"]:
            return MapEditor(load_map=map_name)
        # Parse arguments from menu values
        state = get_map_state(map_name)
        keep_fair = menu_values["keep_fair"]
        no_dummies = menu_values["no_dummies"]
        all_play = menu_values["all_play"]
        max_repeat_input = menu_values["max_repeat"]
        try:
            if max_repeat_input == "":
                max_repeat = None
            else:
                max_repeat = int(max_repeat_input)
                assert max_repeat > 0
        except (ValueError, AssertionError):
            self.last_error = (
                '» Invalid "max_repeat" value, must be a positive integer, '
                f'not: "{max_repeat_input}"'
            )
            return None
        # Collect bots
        selected_bot_names = [b.NAME for b in self.selected_bots]
        if not selected_bot_names:
            selected_bot_names = [b.NAME for b in self._normal_bots]
        # Make bot getter
        bot_selector = BotSelection(
            selection=selected_bot_names,
            keep_fair=keep_fair,
            no_dummies=no_dummies,
            all_play=all_play,
            max_repeat=max_repeat,
        )
        # Make Battle
        try:
            return BattleManager(
                initial_state=state,
                bots=bot_selector,
                description=f"GUI battle @ {map_name}",
                gui_mode=True,
            )
        except NotFairError as e:
            self.last_error = f"» {e}"
            logger(f"Failed to create new battle: {e}")
            return None
