import copy
from botroyale.gui.kex import widgets
from botroyale.api.gui import GameAPI, Control, combine_control_menus, PALETTE_BG
from botroyale.gui.game.menuwidget import get_menu_widget
from botroyale.gui import ASSETS_DIR, FONT_SIZE
from botroyale.util import settings


font = settings.get('gui.fonts.menu')
FONT = str(ASSETS_DIR / 'fonts' / f'{font}.ttf')


class GameScreen(widgets.AnchorLayout):
    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(api, GameAPI)
        self.api = api
        self.new_battle = None
        self.menu_widgets = {}
        self.last_menu_values = {}
        self.menu_widgets_container = widgets.BoxLayout()
        self.info_panel = widgets.MLabel(
            font_name=FONT, font_size=FONT_SIZE, valign='top', halign='left')
        self.make_widgets()

    def make_widgets(self):
        self.clear_widgets()
        self.info_panel.text = self.api.get_info_panel_text()
        main_frame = self.add(widgets.BoxLayout())
        new_battle_btn = widgets.Button(
            text=f'Start New Battle ([i]spacebar[/i])',
            on_release=self.set_new_battle, markup=True)
        # Assemble
        left_panel = main_frame.add(widgets.BoxLayout(orientation='vertical'))
        left_panel.make_bg(PALETTE_BG[4])
        left_panel.set_size(hx=0.3)
        # Info panel frame
        if self.info_panel.parent:
            self.info_panel.parent.remove_widget(self.info_panel)
        info_panel_frame = left_panel.add(widgets.AnchorLayout())
        info_panel_frame.add(self.info_panel).set_size(hx=0.9, hy=0.9)
        # New battle button
        new_battle_frame = left_panel.add(widgets.AnchorLayout())
        new_battle_frame.set_size(y=100)
        new_battle_frame.add(new_battle_btn).set_size(hx=0.8, hy=0.5)
        # Menu frame
        if self.menu_widgets_container.parent:
            self.menu_widgets_container.parent.remove_widget(self.menu_widgets_container)
        menu_widgets_frame = main_frame.add(widgets.AnchorLayout())
        menu_widgets_frame.add(self.menu_widgets_container).set_size(hx=0.95, hy=0.95)
        menu_widgets_frame.make_bg(PALETTE_BG[3])
        # Make menu widgets
        initial_menu_widgets = self.api.get_menu_widgets()
        self.remake_menu_widgets(menu_widgets=initial_menu_widgets)

    def remake_menu_widgets(self, menu_widgets):
        self.menu_widgets = {}
        self.menu_widgets_container.clear_widgets()
        def new_stack():
            stack = widgets.StackLayout(orientation='tb-lr')
            scroller = widgets.ScrollView(view=stack)
            self.menu_widgets_container.add(scroller)
            return stack
        def resize_stack(stack):
            stack.set_size(y=sum(w.size[1] for w in stack.children))
        stack = new_stack()
        for idx, iw in enumerate(menu_widgets):
            menu_widget = get_menu_widget(iw)
            if menu_widget.type == 'divider' and idx > 0:
                resize_stack(stack)
                stack = new_stack()
            assert iw.sendto == menu_widget.sendto
            if menu_widget.get_value is not None:
                self.menu_widgets[iw.sendto] = menu_widget
            stack.add(menu_widget)
        resize_stack(stack)
        self.last_menu_values = self.get_menu_values()

    def set_new_battle(self, *args):
        menu_values = self.get_menu_values()
        self.new_battle = self.api.get_new_battle(menu_values)

    def get_controls(self):
        game_controls = {'Game': [
            Control('New battle', self.set_new_battle, 'spacebar'),
            Control('Refresh menu', self.refresh_menu, 'enter'),
            Control('Refresh menu', self.refresh_menu, 'numpadenter'),
            ]}
        api_controls = self.api.get_controls()
        return combine_control_menus(api_controls, game_controls)

    def get_menu_values(self):
        return {sendto: w.get_value() for sendto, w in self.menu_widgets.items()}

    def handle_changes(self, force=False):
        changes = set()
        new_values = self.get_menu_values()
        for sendto, value in new_values.items():
            if (
                sendto in self.last_menu_values
                and value != self.last_menu_values[sendto]
            ):
                changes.add(sendto)
        self.last_menu_values = new_values
        if not changes and not force:
            return
        do_update = self.api.handle_menu_widget(list(changes), copy.deepcopy(new_values))
        if do_update:
            self.make_widgets()

    def refresh_menu(self):
        self.handle_changes(force=True)

    def update(self):
        if self.new_battle:
            b = self.new_battle
            self.new_battle = None
            return b
        self.handle_changes()
        self.info_panel.text = self.api.get_info_panel_text()
        return None
