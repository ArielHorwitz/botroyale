from gui.kex import widgets
from api.gui import GameAPI, Control, combine_control_menus, PALETTE_BG


class GameScreen(widgets.AnchorLayout):
    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(api, GameAPI)
        self.api = api
        self.new_battle = None
        self.input_widgets = {}
        # Make widgets
        main_frame = self.add(widgets.BoxLayout())
        info_panel = widgets.Label(text=api.get_menu_title())
        self.input_widgets_container = widgets.StackLayout(orientation='tb-lr')
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
            container = self.add_input_widget(iw)
            self.input_widgets_container.add(container)

    def add_input_widget(self, iw):
        container = widgets.BoxLayout(orientation='vertical')
        width = 250
        container_size = 40
        if iw.type == 'spacer':
            container.make_bg(PALETTE_BG[0])
            container.add(widgets.Label(text=iw.label))
            container.set_size(x=width, y=container_size)
            return container
        if iw.type == 'toggle':
            w = widgets.ToggleButton(text=iw.label)
            w.active = iw.default
            container.add(w)
            value_getter = lambda: w.active
        elif iw.type == 'text':
            container_size *= 2
            w = widgets.Entry()
            container.add(widgets.Label(text=iw.label))
            container.add(w)
            w.text = iw.default
            value_getter = lambda: w.text
        elif iw.type == 'select':
            container.orientation = 'horizontal'
            w = widgets.DropDownSelect(callback=lambda *a: None)
            if iw.options is None:
                raise ValueError(f'Cannot make a select InputWidget without options')
            w.set_options(iw.options)
            w.text = iw.default
            container.add(widgets.Label(text=iw.label))
            container.add(w)
            value_getter = lambda: w.text
        elif iw.type == 'slider':
            container_size *= 2
            w = widgets.SliderText()
            w.slider.value = iw.default
            container.add(widgets.Label(text=iw.label))
            container.add(w)
            value_getter = lambda: w.slider.value
        else:
            raise ValueError(f'Unknown InputWidget type: {iw.type}')
        self.input_widgets[iw.sendto] = value_getter
        container.set_size(x=width, y=container_size)
        return container

    def set_new_battle(self, *args):
        self.new_battle = self.api.get_new_battle({
            l: value_getter() for l, value_getter in self.input_widgets.items()
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
