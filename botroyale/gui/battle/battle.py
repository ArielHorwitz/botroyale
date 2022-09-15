from botroyale.api.gui import combine_control_menus
from botroyale.gui.kex import widgets
from botroyale.gui.battle.panel import Panel
from botroyale.gui.battle.tilemap import TileMap


class BattleScreen(widgets.AnchorLayout):
    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        self.api = api
        self.panel = Panel(api)
        self.map = TileMap(api)
        hsplit = self.add(widgets.FlipZIndex(orientation='horizontal'))
        hsplit.add(self.panel.set_size(hx=0.5))
        hsplit.add(self.map)

    def get_controls(self):
        map_controls = self.map.get_controls()
        api_controls = self.api.get_controls()
        return combine_control_menus(api_controls, map_controls)

    def update(self):
        self.api.update()
        self.panel.update()
        self.map.update()
