from gui.kex import widgets
from api.gui import GameAPI, Control, combine_control_menus, PALETTE_BG


class GameScreen(widgets.AnchorLayout):
    def __init__(self, api, **kwargs):
        super().__init__(**kwargs)
        assert isinstance(api, GameAPI)
        self.api = api
        self.new_battle = None
        # Make widgets
        main_frame = self.add(widgets.BoxLayout(orientation='vertical'))
        title = widgets.Label(text=api.get_menu_title())
        input_frame = widgets.StackLayout(orientation='tb-lr')
        new_battle_btn = widgets.Button(
            text=f'Start New Battle ([i]spacebar[/i])',
            on_release=self.set_new_battle, markup=True)
        # Assemble
        title_frame = main_frame.add(widgets.AnchorLayout())
        title_frame.make_bg(PALETTE_BG[4])
        title_frame.set_size(y=100)
        title_frame.add(title).set_size(hx=0.5, hy=0.5)
        input_outer_frame = main_frame.add(widgets.AnchorLayout())
        input_outer_frame.add(input_frame).set_size(hx=0.9, hy=0.9)
        input_outer_frame.make_bg(PALETTE_BG[3])
        new_battle_frame = main_frame.add(widgets.AnchorLayout())
        new_battle_frame.set_size(y=100)
        new_battle_frame.make_bg(PALETTE_BG[1])
        new_battle_frame.add(new_battle_btn).set_size(hx=0.5, hy=0.5)
        # Add input widgets
        self.input_widgets = {}
        for iw in api.get_menu_widgets():
            container = self.add_input_widget(iw)
            input_frame.add(container)

    def add_input_widget(self, iw):
        container = widgets.BoxLayout(orientation='vertical')
        half_size = 40
        container_size = half_size * 2
        if iw.type == 'spacer':
            container.make_bg(PALETTE_BG[0])
            container.add(widgets.Label(text=iw.label))
            container.set_size(hx=0.25, y=container_size)
            return container
        if iw.type == 'toggle':
            container_size = half_size
            w = widgets.ToggleButton(text=iw.label)
            w.active = iw.default
            container.add(w)
            value_getter = lambda: w.active
        elif iw.type == 'text':
            w = widgets.Entry()
            container.add(widgets.Label(text=iw.label))
            container.add(w)
            w.text = iw.default
            value_getter = lambda: w.text
        elif iw.type == 'select':
            container.orientation = 'horizontal'
            container_size = half_size
            w = widgets.DropDownSelect(callback=lambda *a: None)
            if iw.options is None:
                raise ValueError(f'Cannot make a select InputWidget without options')
            w.set_options(iw.options)
            w.text = iw.default
            container.add(widgets.Label(text=iw.label))
            container.add(w)
            value_getter = lambda: w.text
        elif iw.type == 'slider':
            w = widgets.SliderText()
            w.value = iw.default
            container.add(widgets.Label(text=iw.label))
            container.add(w)
            value_getter = lambda: w.slider.value
        else:
            raise ValueError(f'Unknown InputWidget type: {iw.type}')
        self.input_widgets[iw.sendto] = value_getter
        container.set_size(hx=0.25, y=container_size)
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
