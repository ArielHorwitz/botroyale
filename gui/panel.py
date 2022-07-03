from gui.kex import widgets


class Panel(widgets.BoxLayout):
    def __init__(self, control_buttons, **kwargs):
        super().__init__(orientation='vertical')
        self.make_bg((0.05, 0.2, 0.35))

        control_panel = self.add(ControlPanel(buttons=control_buttons))
        text_frame = self.add(widgets.AnchorLayout(
            anchor_x='left', anchor_y='top', padding=(15, 15)))
        self.main_text = text_frame.add(widgets.Label(markup=True, valign='top', halign='left'))

    def set_text(self, text):
        self.main_text.text = str(text)


class ControlPanel(widgets.BoxLayout):
    def __init__(self, buttons, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        for text, callback in buttons:
            btn = self.add(widgets.Button(
                text=text, markup=True, on_release=lambda *a, c=callback: c()))
            btn.set_size(y=40)
        self.set_size(y=40*len(buttons))
