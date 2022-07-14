import math
from gui.kex import widgets
from util.settings import Settings


PANEL_FONT_SIZE = Settings.get('gui.panel_font_size', 16)


class Panel(widgets.BoxLayout):
    def __init__(self, control_buttons, **kwargs):
        super().__init__(orientation='vertical')
        self.make_bg((0.05, 0.2, 0.35))

        control_panel = self.add(ControlPanel(buttons=control_buttons))
        text_frame = self.add(widgets.AnchorLayout(
            anchor_x='left', anchor_y='top', padding=(15, 15)))
        self.main_text = text_frame.add(widgets.Label(
            markup=True, font_size=PANEL_FONT_SIZE,
            valign='top', halign='left',
            ))

    def set_text(self, text):
        self.main_text.text = str(text)


class ControlPanel(widgets.GridLayout):
    def __init__(self, buttons, **kwargs):
        rows = math.ceil(len(buttons)/2)
        super().__init__(orientation='tb-lr', rows=rows, **kwargs)
        for text, callback in buttons:
            btn = self.add(widgets.Button(
                text=text, markup=True, font_size=PANEL_FONT_SIZE,
                on_release=lambda *a, c=callback: c()))
            btn.set_size(y=30)
        self.set_size(y=30*rows)
