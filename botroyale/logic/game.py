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


class StandardGameAPI(GameAPI):
    """A standard implementation of `botroyale.api.gui.GameAPI`.

    See `StandardGameAPI.get_new_battle` on starting battles and the map editor.
    """

    _widgets_requiring_remake = {
        "editor",
        "clear_filter",
        "show_selected",
        "enable_testing",
    }
    _bot_changing_widgets = {"add_all", "remove_all", "show_selected", "enable_testing"}
    _text_widgets = {"show_filter", "max_repeat"}
    _clear_filter_widgets = {"clear_filter", "show_selected"}

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
            max_repeat=0,
        )
        self.last_error = ""
        self._sorted_bots = _get_sorted_bots()
        self._normal_bots = [b for b in self._sorted_bots if not b.TESTING_ONLY]
        self._testing_bots = [b for b in self._sorted_bots if b.TESTING_ONLY]

    @property
    def _bots_showing(self) -> list[type]:
        showing = []
        for bot in self._sorted_bots:
            if self.menu_values["show_selected"]:
                if bot in self.selected_bots:
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

    def get_menu_widgets(self) -> list[InputWidget]:
        """Return a list of widgets for controlling how to start the next battle.

        Includes "Map editor mode" toggle, map selection, bot selection options.

        See: `botroyale.api.gui.GameAPI.get_menu_widgets`.
        """
        editor_mode = self.menu_values["editor"]
        map_widgets = [
            # Map
            InputWidget("Map Selection", "divider"),
            InputWidget(
                "Map:",
                "select",
                default=self.menu_values["map"],
                options=MAPS,
                sendto="map",
            ),
            InputWidget("Map Editor", "spacer"),
            InputWidget(
                "Toggle map editor mode",
                "toggle",
                default=editor_mode,
                sendto="editor",
            ),
        ]
        if editor_mode:
            return map_widgets
        bot_widgets = self._get_bot_widgets()
        return [
            *map_widgets,
            # Bot settings
            InputWidget("Bot Selection", "divider"),
            InputWidget(
                "Add all",
                "toggle",
                sendto="add_all",
            ),
            InputWidget(
                "Remove all",
                "toggle",
                sendto="remove_all",
            ),
            InputWidget(
                "Filter bots:",
                "text",
                default=self.menu_values["show_filter"],
                sendto="show_filter",
            ),
            InputWidget(
                "Clear filter",
                "toggle",
                sendto="clear_filter",
            ),
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
                "Max slots per bot:",
                "slider",
                default=self.menu_values["max_repeat"],
                sendto="max_repeat",
                slider_range=(0, 15, 1),
            ),
            # Bot toggles
            InputWidget("Bots", "divider"),
            *bot_widgets,
        ]

    def handle_menu_widget(
        self, widgets: list[str], menu_values: dict[str, Any]
    ) -> bool:
        """Overrides `botroyale.api.gui.GameAPI.handle_menu_widget`."""
        widgets = set(widgets)
        # Update our menu values
        for sendto in widgets:
            self.menu_values[sendto] = menu_values[sendto]
        # Clear last error if user changed anything
        if widgets:
            self.last_error = ""
        # Handle the effects of each widget
        require_remake = 0
        for w in widgets:
            remake = self._handle_menu_widget_single(w)
            require_remake += remake
        # Recreate/update menu if necessary
        if require_remake or len(widgets) == 0:
            return "widgets"
        if len(self._text_widgets & widgets) == 1:
            # User is typing and nothing else - don't recreate the widget from
            # under their keyboard (widgets lose focus when recreated).
            return "nothing"
        return "values"

    def _handle_menu_widget_single(self, widget):
        """Expected to be called once per widget only by `handle_menu_widget`."""
        # Clear filter text if necessary
        require_remake = 0
        if widget in self._widgets_requiring_remake:
            require_remake += 1
        if widget in self._bot_changing_widgets and self.menu_values["show_filter"]:
            require_remake += 1
        if widget in self._clear_filter_widgets:
            self.menu_values["show_filter"] = ""
        if widget == "add_all":
            self._add_showing()
        elif widget == "remove_all":
            self._remove_showing()
        elif widget == "enable_testing" and not self.menu_values["enable_testing"]:
            self._remove_testing()
        elif widget.startswith(BOT_SENDTO_PREFIX):
            bname = widget[len(BOT_SENDTO_PREFIX) :]
            self._toggle_bot(BOTS[bname])
            if self.menu_values["show_selected"] or self.menu_values["show_filter"]:
                require_remake += 1
        return require_remake

    def get_info_panel_text(self) -> str:
        """Overrides: `GameAPI.get_info_panel_text`."""
        if self.menu_values["editor"]:
            return "\n".join(
                [
                    "[b][u]Map Editor[/u][/b]",
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
        max_repeat = round(menu_values["max_repeat"])
        if max_repeat == 0:
            max_repeat = None
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

    def get_new_battle_text(self) -> str:
        """Return the string to be displayed in the button to start a new battle."""
        return "Edit custom map" if self.menu_values["editor"] else "Start new battle"
