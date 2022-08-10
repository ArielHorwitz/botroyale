from gui.kex import widgets
from util.settings import Settings


FONT_SIZE = Settings.get('gui.panel_font_size', 16)


class Panel(widgets.BoxLayout):
    def __init__(self, api, **kwargs):
        super().__init__(orientation='vertical')
        self.make_bg((0.05, 0.2, 0.35))
        self.api = api
        text_frame = self.add(widgets.AnchorLayout(
            anchor_x='left', anchor_y='top', padding=(15, 15)))
        self.main_text = text_frame.add(widgets.Label(
            markup=True, font_size=FONT_SIZE,
            valign='top', halign='left',
            ))

    def update(self):
        text = self.api.get_info_panel_text()
        self.main_text.text = text
        self.make_bg(self.api.get_info_panel_color())
