from gui.kex import widgets
from api.gui import GameAPI, Control, combine_control_menus, PALETTE_BG
from gui.game.menuwidget import get_menu_widget


class GameScreen(widgets.AnchorLayout):
    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(api, GameAPI)
        self.api = api
        self.new_battle = None
        self.input_widgets = {}
        self.input_widgets_container = widgets.StackLayout(orientation='tb-lr')
        self.make_widgets()

    def make_widgets(self):
        self.clear_widgets()
        main_frame = self.add(widgets.BoxLayout())
        info_panel = widgets.Label(text=self.api.get_menu_title())
        new_battle_btn = widgets.Button(
            text=f'Start New Battle ([i]spacebar[/i])',
            on_release=self.set_new_battle, markup=True)
        # Assemble
        left_panel = main_frame.add(widgets.BoxLayout(orientation='vertical'))
        left_panel.make_bg(PALETTE_BG[4])
        left_panel.set_size(x=450)
        # Info panel frame
        info_panel_frame = left_panel.add(widgets.AnchorLayout())
        info_panel_frame.add(info_panel).set_size(hx=0.5, hy=0.5)
        # New battle frame
        new_battle_frame = left_panel.add(widgets.AnchorLayout())
        new_battle_frame.set_size(y=100)
        new_battle_frame.add(new_battle_btn).set_size(hx=0.8, hy=0.5)
        # Input frame
        input_widgets_frame = main_frame.add(widgets.AnchorLayout())
        input_widgets_frame.add(self.input_widgets_container).set_size(hx=0.9, hy=0.9)
        input_widgets_frame.make_bg(PALETTE_BG[3])
        # Add input widgets
        initial_menu_widgets = self.api.get_menu_widgets()
        self.remake_input_widgets(menu_widgets=initial_menu_widgets)

    def remake_input_widgets(self, menu_widgets):
        self.input_widgets = {}
        self.input_widgets_container.clear_widgets()
        for iw in menu_widgets:
            menu_widget = get_menu_widget(iw)
            assert iw.sendto == menu_widget.sendto
            if menu_widget.get_value is not None:
                self.input_widgets[iw.sendto] = menu_widget
            self.input_widgets_container.add(menu_widget)

    def set_new_battle(self, *args):
        self.new_battle = self.api.get_new_battle({
            l: w.get_value() for l, w in self.input_widgets.items()
            })

    def get_controls(self):
        game_controls = {'Game': [Control('New battle', self.set_new_battle, 'spacebar')]}
        api_controls = self.api.get_controls()
        return combine_control_menus(api_controls, game_controls)

    def update(self):
        if self.new_battle:
            b = self.new_battle
            self.new_battle = None
            return b
        return None
