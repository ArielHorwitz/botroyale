from botroyale.gui.kex import widgets
from botroyale.util import settings
from botroyale.gui import ASSETS_DIR, FONT, FONT_SIZE


font = settings.get('gui.fonts.menubar')
FONT_MENU = str(ASSETS_DIR / 'fonts' / f'{font}.ttf')


class MenuBar(widgets.BoxLayout):
    def __init__(self, control_menu, **kwargs):
        super().__init__(**kwargs)
        self.callbacks = {}
        self.make_bg((0,0,0))
        for menu_label, menu in control_menu.items():
            btn = self.add(widgets.DropDownMenu(
                text=menu_label, markup=True, font_size=FONT_SIZE, font_name=FONT_MENU,
                callback=lambda i, l, s=menu_label: self.handle_button(f'{s}.{l}')))
            options = []
            for label, callback, hotkey in menu:
                if hotkey:
                    hotkey_label = widgets.InputManager.humanize_keys(hotkey)
                    label = f'{label} ([i]{hotkey_label}[/i])'
                options.append(label)
                self.callbacks[f'{menu_label}.{label}'] = callback
            btn.set_options(options, markup=True, font_size=FONT_SIZE, font_name=FONT)
        self.set_size(y=30)
        self.label = self.add(widgets.MLabel())
        self.label.set_size(x=125)

    def handle_button(self, label):
        assert label in self.callbacks
        c = self.callbacks[label]
        c()

    def set_text(self, text):
        self.label.text = str(text)
