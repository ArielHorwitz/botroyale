import math
from collections import namedtuple
from gui.kex import widgets
from util.settings import Settings


PANEL_FONT_SIZE = Settings.get('gui.panel_font_size', 16)


class Panel(widgets.BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical')
        self.make_bg((0.05, 0.2, 0.35))

        text_frame = self.add(widgets.AnchorLayout(
            anchor_x='left', anchor_y='top', padding=(15, 15)))
        self.main_text = text_frame.add(widgets.Label(
            markup=True, font_size=PANEL_FONT_SIZE,
            valign='top', halign='left',
            ))

    def set_text(self, text):
        self.main_text.text = str(text)


class MenuBar(widgets.BoxLayout):
    def __init__(self, control_menus, **kwargs):
        super().__init__(**kwargs)
        self.callbacks = {}
        self.make_bg((0,0,0))
        for submenu in control_menus:
            btn = self.add(widgets.DropDownMenu(
                text=submenu.label, markup=True, font_size=PANEL_FONT_SIZE,
                callback=lambda i, l, s=submenu.label: self.handle_button(f'{s}.{l}')))
            options = []
            for label, callback, hotkey in submenu.controls:
                if hotkey:
                    hotkey_label = widgets.InputManager.humanize_keys(hotkey)
                    label = f'{label} ([i]{hotkey_label}[/i])'
                options.append(label)
                self.callbacks[f'{submenu.label}.{label}'] = callback
            btn.set_options(options, markup=True, font_size=PANEL_FONT_SIZE)
            btn.set_size(x=250)
        self.set_size(y=30)
        self.label = self.add(widgets.MLabel())

    def handle_button(self, label):
        assert label in self.callbacks
        c = self.callbacks[label]
        c()

    def set_text(self, text):
        self.label.text = str(text)
